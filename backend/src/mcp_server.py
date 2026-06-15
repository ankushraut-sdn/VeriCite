import os
import sys
import logging
from typing import List, Dict, Any, Optional

# Load env variables
from dotenv import load_dotenv
load_dotenv()

# Add the project directory root to path so backend imports resolve successfully
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging strictly to stderr to prevent stdout JSON-RPC corruption
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("vericite-mcp-server")

try:
    from backend.src.orchestrator import RAGOrchestrator
    from backend.src import config
except ImportError as e:
    logger.error(f"Import error: {e}. Current sys.path: {sys.path}")
    raise

from mcp.server.fastmcp import FastMCP

# Initialize MCP Server
mcp = FastMCP(
    "VeriCite-Document-System",
    description="Connect directly to the semantic document VeriCite ingestion pipeline and context-aware Q&A indices."
)

# Initialize core orchestrator components
try:
    orchestrator = RAGOrchestrator()
    logger.info("RAGOrchestrator successfully integrated with MCP Server.")
except Exception as e:
    logger.error(f"Failed to initialize RAGOrchestrator: {e}")
    orchestrator = None

@mcp.tool()
def query_rag(query: str, top_k: int = 5, min_similarity: float = 0.0) -> str:
    """
    Submit a search query or question to the VeriCite Document System.
    Retrieves matching document contexts and returns an LLM-synthesized answer with source citations.
    
    Args:
        query: The question, search query, or topic to look up.
        top_k: Maximum number of relevant document chunks to retrieve (default: 5).
        min_similarity: Minimum cosine similarity score threshold (0.0 to 1.0, default: 0.0).
    """
    if not orchestrator:
        return "Error: VeriCite Orchestrator is not initialized. Verify OpenAI keys and vector storage path."
        
    try:
        response = orchestrator.query(
            query_str=query,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        answer = response.get("answer", "")
        sources = response.get("sources", [])
        
        output = f"### Answer\n{answer}\n\n"
        if sources:
            output += "### Sources Cited\n"
            for src in sources:
                output += f"- **{src.get('source')}** (Page {src.get('page')}, Score: {src.get('score', 0.0):.4f})\n"
        else:
            output += "*No explicit source documents were retrieved above the similarity threshold.*"
            
        return output
    except Exception as e:
        logger.error(f"MCP Query Tool Error: {e}")
        return f"Error executing RAG query: {str(e)}"

@mcp.tool()
def list_documents() -> str:
    """
    List all documents currently ingested and indexed in the RAG system's vector database.
    Provides metadata such as document names, file sizes, and page counts.
    """
    if not orchestrator:
        return "Error: RAG Orchestrator is not initialized."
        
    try:
        store = orchestrator.store
        data = store.collection.get(include=["metadatas"])
        if not data or not data["metadatas"]:
            return "No documents are currently indexed in the RAG database."
            
        sources_meta = {}
        for meta in data["metadatas"]:
            source = meta.get("source")
            if not source:
                continue
            
            page = int(meta.get("page", 1))
            
            if source not in sources_meta:
                sources_meta[source] = {
                    "name": source,
                    "file_size": meta.get("file_size", 0),
                    "created_at": meta.get("created_at", ""),
                    "page_count": page
                }
            else:
                sources_meta[source]["page_count"] = max(sources_meta[source]["page_count"], page)
                
        documents = list(sources_meta.values())
            
        output = "### Ingested Documents List\n"
        for doc in documents:
            size_kb = doc.get("file_size", 0) / 1024
            output += f"- **{doc.get('name')}** — {size_kb:.2f} KB, Max Pages: {doc.get('page_count')}, Ingested: {doc.get('created_at')}\n"
            
        return output
    except Exception as e:
        logger.error(f"MCP List Documents Tool Error: {e}")
        return f"Error listing documents: {str(e)}"

@mcp.tool()
def ingest_document(file_path: str) -> str:
    """
    Ingest a new local document file (PDF, TXT, DOCX, MD) into the RAG vector storage index.
    The system will parse the file, chunk it, generate embeddings, and build indices.
    
    Args:
        file_path: The absolute path of the file on the host system.
    """
    if not orchestrator:
        return "Error: RAG Orchestrator is not initialized."
        
    if not os.path.exists(file_path):
        return f"Error: The specified file path does not exist on host: '{file_path}'"
        
    try:
        stats = orchestrator.ingest_document(file_path)
        status = stats.get("status", "success")
        chunks = stats.get("chunks_count", 0)
        time_taken = stats.get("ingestion_time_sec", 0.0)
        
        return (
            f"### Ingestion Success\n"
            f"Successfully processed and indexed document: **{stats.get('source')}**\n"
            f"- **Status**: {status}\n"
            f"- **Indexed Chunks**: {chunks} text chunks\n"
            f"- **Processing Time**: {time_taken:.2f} seconds\n"
        )
    except Exception as e:
        logger.error(f"MCP Ingest Document Tool Error: {e}")
        return f"Error ingesting document '{file_path}': {str(e)}"

@mcp.tool()
def delete_document(filename: str) -> str:
    """
    Remove an ingested document and delete all its associated vector embeddings from the collection.
    
    Args:
        filename: The exact base name of the file to remove (e.g. 'document.pdf').
    """
    if not orchestrator:
        return "Error: RAG Orchestrator is not initialized."
        
    try:
        # Delete from vector db index
        orchestrator.store.delete_by_source(filename)
        
        # Delete physical upload file if present
        uploads_dir = "./data/uploads"
        local_path = os.path.join(uploads_dir, filename)
        if os.path.exists(local_path):
            os.remove(local_path)
            
        return f"Successfully deleted document '**{filename}**' and completely wiped all associated vector database embeddings."
    except Exception as e:
        logger.error(f"MCP Delete Document Tool Error: {e}")
        return f"Error deleting document '{filename}': {str(e)}"

if __name__ == "__main__":
    # Launch MCP server over standard input/output transport
    mcp.run(transport="stdio")
