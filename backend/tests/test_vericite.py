import os
import shutil
import pytest
import numpy as np
from typing import Dict, Any

from backend.src.exceptions import LoaderError, ChunkerError, VectorStoreError
from backend.src.loaders.txt_loader import TextLoader
from backend.src.loaders.markdown_loader import MarkdownLoader
from backend.src.loaders.docx_loader import DocxLoader
from backend.src.loaders.pdf_loader import PDFLoader
from backend.src.chunker.semantic import DocumentChunker
from backend.src.embedder.openai_embedder import OpenAIEmbedder
from backend.src.vectordb.chroma_store import ChromaStore
from backend.src.retriever.semantic_retriever import SemanticRetriever
from backend.src.llm.openai_llm import OpenAILLM
from backend.src.orchestrator import RAGOrchestrator

# ==========================================================================
# 1. LOADERS TESTS
# ==========================================================================
def test_text_loader(tmp_path):
    """Test text loader reads content and extracts correct base metadata."""
    loader = TextLoader()
    sample_file = tmp_path / "test_sample.txt"
    sample_content = "Hello, world! This is a VeriCite text loader test."
    sample_file.write_text(sample_content, encoding="utf-8")
    
    # Verify content conversion
    content = loader.load(str(sample_file))
    assert content == sample_content
    
    # Verify metadata extraction
    meta = loader.extract_metadata(str(sample_file))
    assert meta["source"] == "test_sample.txt"
    assert meta["file_size"] == len(sample_content)
    assert "created_at" in meta

def test_markdown_loader(tmp_path):
    """Test markdown loader correctly subclassed from text loader."""
    loader = MarkdownLoader()
    sample_file = tmp_path / "test_sample.md"
    sample_content = "# VeriCite Specification\n\nThis is a Markdown text test."
    sample_file.write_text(sample_content, encoding="utf-8")
    
    content = loader.load(str(sample_file))
    assert content == sample_content

def test_loader_nonexistent_file():
    """Test that loaders raise LoaderError for missing files."""
    loader = TextLoader()
    with pytest.raises(LoaderError):
        loader.load("non_existent_file_path_123.txt")

# ==========================================================================
# 2. CHUNKER & PREPROCESSING TESTS
# ==========================================================================
def test_chunker_basic_splitting():
    """Test chunker splits text based on size and cleans layout spacing."""
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    raw_text = "This is a very long text block that needs to be parsed and chunked. " * 5
    base_meta = {"source": "test.txt", "file_size": len(raw_text)}
    
    chunks = chunker.chunk_document(raw_text, base_meta)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert "content" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["source"] == "test.txt"
        assert chunk["metadata"]["page"] == 1
        assert "chunk_index" in chunk["metadata"]
        assert len(chunk["content"]) <= 100

def test_chunker_page_markers_preservation():
    """Test that chunker tracks HTML page break comments accurately."""
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    paginated_content = (
        "<!-- PAGE: 1 -->\nThis is text on page 1.\n\n"
        "<!-- PAGE: 2 -->\nThis is text on page 2. Adding more sentences.\n\n"
        "<!-- PAGE: 3 -->\nThis is text on page 3. The end."
    )
    base_meta = {"source": "paginated.pdf", "file_size": len(paginated_content)}
    
    chunks = chunker.chunk_document(paginated_content, base_meta)
    
    # We expect 3 distinct page boundaries to be identified
    assert len(chunks) >= 3
    
    # Assert that chunks map to their respective page numbers
    pages_seen = [c["metadata"]["page"] for c in chunks]
    assert 1 in pages_seen
    assert 2 in pages_seen
    assert 3 in pages_seen

# ==========================================================================
# 3. EMBEDDER TESTS
# ==========================================================================
def test_embedder_mock_fallback():
    """Test mock embedder generates stable, normalized 1536-dimensional float vectors."""
    embedder = OpenAIEmbedder()
    
    text = "Core components of a retrieval augmented generation system."
    embedding = embedder.embed_query(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    # Embedding vector should be normalized to unit length
    norm = np.linalg.norm(embedding)
    assert pytest.approx(norm, abs=1e-5) == 1.0

def test_embedder_mock_determinism():
    """Test that mock embedder generates identical vectors for identical inputs (highly critical for retrieval tests)."""
    embedder = OpenAIEmbedder()
    text = "Deterministic mock embedding test sentence."
    
    emb1 = embedder.embed_query(text)
    emb2 = embedder.embed_query(text)
    
    assert emb1 == emb2

# ==========================================================================
# 4. VECTOR DATABASE TESTS
# ==========================================================================
def test_chroma_store_operations(tmp_path, monkeypatch):
    """Test database connections, index inserting, searching, and deleting functions."""
    # Override Chroma DB path config inside tests to prevent overriding active workspace records
    test_db_dir = tmp_path / "test_chroma"
    monkeypatch.setattr("backend.src.config.CHROMA_DB_PATH", str(test_db_dir))
    
    store = ChromaStore(collection_name="test_collection")
    embedder = OpenAIEmbedder()
    
    chunks = [
        {"content": "Apples are red fruits that grow on trees.", "metadata": {"source": "fruits.txt", "chunk_index": 0}},
        {"content": "Carrots are orange root vegetables.", "metadata": {"source": "veggies.txt", "chunk_index": 0}},
        {"content": "Bananas are yellow curved fruits.", "metadata": {"source": "fruits.txt", "chunk_index": 1}}
    ]
    
    contents = [c["content"] for c in chunks]
    embeddings = embedder.embed_documents(contents)
    
    # 1. Add chunks to database
    store.add_chunks(chunks, embeddings)
    
    # 2. Similarity search
    query_emb = embedder.embed_query("bananas yellow")
    results = store.similarity_search(query_emb, top_k=2)
    
    assert len(results) > 0
    # Top result should match bananas since semantic mock hash links similar words
    top_hit = results[0]
    assert "yellow" in top_hit["content"] or "Bananas" in top_hit["content"]
    assert top_hit["metadata"]["source"] == "fruits.txt"
    
    # 3. Delete document from index
    store.delete_by_source("veggies.txt")
    
    # Search for carrot query
    carrot_emb = embedder.embed_query("carrots orange root")
    results_after_delete = store.similarity_search(carrot_emb, top_k=5)
    
    # Check that veggie chunks are not returned in top results
    for res in results_after_delete:
        assert res["metadata"]["source"] != "veggies.txt"

# ==========================================================================
# 5. ORCHESTRATOR END-TO-END PIPELINE TESTS
# ==========================================================================
def test_orchestrator_pipeline_flow(tmp_path, monkeypatch):
    """Test full document ingestion -> semantic retrieval -> augmented answer VeriCite flow."""
    test_db_dir = tmp_path / "test_orch_chroma"
    monkeypatch.setattr("backend.src.config.CHROMA_DB_PATH", str(test_db_dir))
    
    # Setup sample markdown document
    doc_file = tmp_path / "vericite_spec.md"
    doc_content = (
        "# VeriCite Project specifications\n\n"
        "Overview: The VeriCite system is highly optimized.\n"
        "Key specs: It handles maximum size limits of 20 Megabytes."
    )
    doc_file.write_text(doc_content, encoding="utf-8")
    
    orchestrator = RAGOrchestrator()
    
    # 1. Ingest document
    stats = orchestrator.ingest_document(str(doc_file))
    assert stats["status"] == "success"
    assert stats["chunks_count"] > 0
    assert stats["source"] == "vericite_spec.md"
    
    # 2. Query document context
    query = "What is the maximum size limit of the system?"
    response = orchestrator.query(query, top_k=2)
    
    assert response["query"] == query
    assert "answer" in response
    assert len(response["sources"]) > 0
    assert response["sources"][0]["source"] == "vericite_spec.md"
    
    # Since we are in mock LLM mode without OpenAI API keys, the answer should contain the citation structure
    assert "vericite_spec.md" in response["answer"]
