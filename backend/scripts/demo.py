import os
import sys
import argparse
import logging
from typing import Dict, Any

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.src.orchestrator import RAGOrchestrator
from backend.src.exceptions import RAGError

logger = logging.getLogger("demo")

SAMPLE_DOC_CONTENT = """# The VeriCite RAG System

## Overview
The VeriCite RAG system is a state-of-the-art document-based Retrieval-Augmented Generation application. It allows users to ingest documents (PDF, DOCX, TXT, MD), convert them to Markdown, chunk them preserving metadata (like page number), and index them in a Chroma DB vector database.

## Architecture
The system consists of the following seven core layers:
1. **Document Ingestion Pipeline** - Unified loader base that converts everything to clean Markdown.
2. **Text Chunking** - Uses RecursiveCharacterTextSplitter for page-aware semantic splitting.
3. **Embedding Generation** - OpenAI `text-embedding-3-small` with clean deterministically hashed mock offline support.
4. **Vector Database Integration** - Chroma DB for cosine-similarity based indexing and querying.
5. **Retrieval Mechanism** - Queries vector store with similarity scoring and cutoff threshold filters.
6. **LLM Integration** - Uses OpenAI `gpt-4o` for generating precise answers based on matched documents.
7. **Attribution and Citation** - Ensures every answer has clear source tracking (file name and page numbers).

## Key Specifications
- Max Document Upload Size: 20 Megabytes (MB).
- Default Similarity Threshold: Cosine similarity score >= 0.70.
- Persisted DB Location: `./data/chroma_db`

## Historical Background
The development of this project started in early June 2026. The main objective was to create a zero-dependency local workspace framework that would allow seamless parsing and verification.
"""

def create_sample_document(target_dir: str = "./data") -> str:
    """Create a sample markdown knowledge base if none is supplied."""
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, "vericite_spec.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_DOC_CONTENT)
    print(f"[DEMO SETUP] Generated sample document: {file_path}")
    return file_path

def run_demo(file_path: str, query: str):
    print("=" * 80)
    print("                       VERICITE SYSTEM CLI DEMO                         ")
    print("=" * 80)
    
    try:
        # Initialize orchestrator
        print("[1/4] Initializing VeriCite pipeline components...")
        orchestrator = RAGOrchestrator()
        
        # 1. Ingest document
        print(f"\n[2/4] Ingesting document: '{file_path}'...")
        ingest_stats = orchestrator.ingest_document(file_path)
        print("-" * 50)
        print(f"  Source Document  : {ingest_stats['source']}")
        print(f"  Total Chunks     : {ingest_stats['chunks_count']}")
        print(f"  Ingestion Time   : {ingest_stats['ingestion_time_sec']:.2f}s")
        print(f"  Ingestion Status : {ingest_stats['status'].upper()}")
        print("-" * 50)
        
        # 2. Execute Query
        print(f"\n[3/4] Submitting query: '{query}'...")
        query_response = orchestrator.query(query, top_k=3, min_similarity=0.1)
        
        print("\n[4/4] Retrieval-Augmented Generation Results:")
        print("=" * 80)
        print(f"QUERY: {query_response['query']}")
        print("=" * 80)
        print("GENERATED RESPONSE:")
        print(query_response["answer"])
        print("=" * 80)
        
        # 3. Print Sources
        print("\nATTRIBUTED SOURCES:")
        if not query_response["sources"]:
            print("  No sources met similarity cutoff threshold.")
        else:
            for idx, source in enumerate(query_response["sources"]):
                print(f"  [{idx+1}] File: {source['source']} | Page: {source['page']} | Cosine Similarity Score: {source['score']:.4f}")
                
        print("\nPERFORMANCE METRICS:")
        perf = query_response["performance"]
        print(f"  Retrieval Time : {perf['retrieval_time_sec']:.4f}s")
        print(f"  LLM Gen Time   : {perf['llm_time_sec']:.4f}s")
        print(f"  Total Latency  : {perf['total_time_sec']:.4f}s")
        print("=" * 80)
        
    except RAGError as e:
        print(f"\n[ERROR] RAG System Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected System Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the RAG System End-to-End CLI Demo.")
    parser.add_argument("--file", type=str, help="Path to the document to upload. If omitted, a sample file will be generated.")
    parser.add_argument("--query", type=str, help="The query/question to ask.")
    args = parser.parse_args()
    
    # Generate mock file if not provided
    file_to_use = args.file if args.file else create_sample_document()
    
    # Default query if none provided
    query_to_use = args.query if args.query else "What is the max document upload size and the default similarity threshold?"
    
    run_demo(file_to_use, query_to_use)
