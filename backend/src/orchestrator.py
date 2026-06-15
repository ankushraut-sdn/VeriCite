import os
import time
import logging
from typing import List, Dict, Any

from backend.src.exceptions import (
    OrchestratorError, LoaderError, ChunkerError, EmbeddingError, VectorStoreError, LLMError
)
from backend.src.loaders.pdf_loader import PDFLoader
from backend.src.loaders.docx_loader import DocxLoader
from backend.src.loaders.txt_loader import TextLoader
from backend.src.loaders.markdown_loader import MarkdownLoader
from backend.src.chunker.semantic import DocumentChunker
from backend.src.embedder.openai_embedder import OpenAIEmbedder
from backend.src.vectordb.chroma_store import ChromaStore
from backend.src.retriever.semantic_retriever import SemanticRetriever
from backend.src.llm.openai_llm import OpenAILLM

# Initialize logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class RAGOrchestrator:
    """Core orchestrator coordinating loaders, chunkers, embedding generators, vector databases, and LLMs for VeriCite."""

    def __init__(self):
        try:
            self.embedder = OpenAIEmbedder()
            self.store = ChromaStore()
            self.chunker = DocumentChunker()
            self.retriever = SemanticRetriever(self.embedder, self.store)
            self.llm = OpenAILLM()
            
            # Register concrete loaders for supported file formats
            self.loaders = {
                ".pdf": PDFLoader(),
                ".docx": DocxLoader(),
                ".txt": TextLoader(),
                ".md": MarkdownLoader()
            }
            logger.info("VeriCite Orchestrator initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize VeriCite Orchestrator: {e}")
            raise OrchestratorError(f"Failed to initialize orchestrator components: {str(e)}")

    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """
        Run the full ingestion pipeline: Load -> Clean -> Chunk -> Embed -> Store.
        Automatically overwrites previous indexed chunks for the same source document.
        
        Args:
            file_path: Absolute or relative path to the file.
            
        Returns:
            Dict containing stats of the ingestion process (chunks, timing, filename).
            
        Raises:
            OrchestratorError: If ingestion fails at any stage.
        """
        start_time = time.time()
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        logger.info(f"Starting ingestion pipeline for document: '{filename}'")
        
        # 1. Input format validation & loader selection
        if ext not in self.loaders:
            raise OrchestratorError(f"Unsupported file format: {ext}. Supported: {list(self.loaders.keys())}")
            
        loader = self.loaders[ext]
        
        try:
            # 2. Extract base file metadata
            logger.info(f"Extracting metadata and loading document content...")
            base_meta = loader.extract_metadata(file_path)
            
            # 3. Load & convert to Markdown
            markdown_content = loader.load(file_path)
            
            # 4. Segment content into page-aware text chunks
            logger.info(f"Segmenting document content into chunks...")
            chunks = self.chunker.chunk_document(markdown_content, base_meta)
            
            if not chunks:
                logger.warning(f"No text extracted or chunked from document: {filename}")
                return {
                    "source": filename,
                    "chunks_count": 0,
                    "ingestion_time_sec": time.time() - start_time,
                    "status": "warning",
                    "message": "Document was empty or contained no extractable text."
                }
                
            # 5. Clear old embeddings for the same file in Chroma to prevent duplicate records
            logger.info(f"Cleaning previous indexes for source '{filename}'...")
            self.store.delete_by_source(filename)
            
            # 6. Generate embedding vectors
            logger.info(f"Generating embedding vectors for {len(chunks)} text chunks...")
            chunk_contents = [c["content"] for c in chunks]
            embeddings = self.embedder.embed_documents(chunk_contents)
            
            # 7. Store embeddings and documents in Vector DB
            logger.info("Indexing chunks into persistent vector store...")
            self.store.add_chunks(chunks, embeddings)
            
            duration = time.time() - start_time
            logger.info(f"Successfully indexed '{filename}' ({len(chunks)} chunks) in {duration:.2f} seconds.")
            
            return {
                "source": filename,
                "chunks_count": len(chunks),
                "ingestion_time_sec": duration,
                "status": "success",
                "message": f"Successfully indexed {len(chunks)} chunks."
            }
            
        except (LoaderError, ChunkerError, EmbeddingError, VectorStoreError) as e:
            logger.error(f"Ingestion failed for {filename}: {str(e)}")
            raise OrchestratorError(f"Pipeline Ingestion Failed for '{filename}': {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during ingestion: {str(e)}")
            raise OrchestratorError(f"Unexpected pipeline ingestion failure for '{filename}': {str(e)}")

    def query(self, query_str: str, top_k: int = 5, min_similarity: float = 0.0) -> Dict[str, Any]:
        """
        Run retrieval-augmented query pipeline: Retrieve -> Rerank/Filter -> LLM response.
        
        Args:
            query_str: The question to ask.
            top_k: Max chunks to retrieve.
            min_similarity: Threshold score.
            
        Returns:
            Dict containing answer, source metadata, and retrieval latency details.
            
        Raises:
            OrchestratorError: If query processing fails.
        """
        start_time = time.time()
        logger.info(f"Processing query: '{query_str}'")
        
        try:
            # 1. Retrieve relevant text chunks
            retrieved = self.retriever.retrieve(query_str, top_k=top_k, min_similarity=min_similarity)
            retrieval_latency = time.time() - start_time
            
            # 2. Call LLM to synthesize answer incorporating retrieval context
            logger.info("Calling LLM generator...")
            llm_start = time.time()
            answer = self.llm.generate_response(query_str, retrieved)
            llm_latency = time.time() - llm_start
            
            total_latency = time.time() - start_time
            logger.info(f"Query resolved. Total time: {total_latency:.2f}s (Retrieval: {retrieval_latency:.2f}s, LLM: {llm_latency:.2f}s)")
            
            # 3. Compile sources used for citation attribution
            sources = []
            seen_sources = set()
            for chunk in retrieved:
                meta = chunk["metadata"]
                source_file = meta.get("source", "unknown")
                page = meta.get("page", 1)
                source_key = f"{source_file}_page_{page}"
                
                if source_key not in seen_sources:
                    seen_sources.add(source_key)
                    sources.append({
                        "source": source_file,
                        "page": page,
                        "score": float(chunk.get("score", 0.0))
                    })
            
            return {
                "query": query_str,
                "answer": answer,
                "sources": sources,
                "retrieved_chunks": [
                    {
                        "content": c["content"],
                        "metadata": c["metadata"],
                        "score": float(c.get("score", 0.0))
                    } for c in retrieved
                ],
                "performance": {
                    "total_time_sec": total_latency,
                    "retrieval_time_sec": retrieval_latency,
                    "llm_time_sec": llm_latency
                }
            }
            
        except (EmbeddingError, VectorStoreError, LLMError) as e:
            logger.error(f"Query pipeline failed: {str(e)}")
            raise OrchestratorError(f"Query Pipeline Failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during query resolution: {str(e)}")
            raise OrchestratorError(f"Unexpected query resolution failure: {str(e)}")
