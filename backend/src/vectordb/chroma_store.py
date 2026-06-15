import os
import logging
from typing import List, Dict, Any
from backend.src import config
from backend.src.exceptions import VectorStoreError

logger = logging.getLogger(__name__)

class ChromaStore:
    """Wrapper around ChromaDB to handle embedding storage, indexing, and retrieval."""

    def __init__(self, collection_name: str = "documents"):
        self.db_path = config.CHROMA_DB_PATH
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        try:
            import chromadb
            # Initialize persistent Client
            self.client = chromadb.PersistentClient(path=self.db_path)
            # Get or create collection. We pass None for embedding_function because we generate
            # embeddings externally using our custom OpenAI/Mock embedder.
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            logger.info(f"Initialized Chroma DB at {self.db_path} with collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma DB: {e}")
            raise VectorStoreError(f"Failed to initialize Chroma DB: {str(e)}")

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Add document chunks and their pre-computed embeddings to Chroma.
        
        Args:
            chunks: List of chunk dicts (each containing 'content' and 'metadata').
            embeddings: Pre-computed embedding vectors matching the chunks list.
            
        Raises:
            VectorStoreError: If ingestion fails.
        """
        if not chunks:
            return
            
        if len(chunks) != len(embeddings):
            raise VectorStoreError("Chunks list and embeddings list must be of equal length.")
            
        try:
            ids = []
            documents = []
            metadatas = []
            
            for idx, chunk in enumerate(chunks):
                source = chunk["metadata"].get("source", "unknown")
                chunk_idx = chunk["metadata"].get("chunk_index", 0)
                # Generate a unique ID: source_filename_chunk_index
                doc_id = f"{source}_{chunk_idx}"
                
                ids.append(doc_id)
                documents.append(chunk["content"])
                
                # Chroma metadata keys must be simple types (str, int, float, bool)
                meta = {}
                for k, v in chunk["metadata"].items():
                    if isinstance(v, (str, int, float, bool)):
                        meta[k] = v
                    else:
                        meta[k] = str(v)
                metadatas.append(meta)
                
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(chunks)} chunks to Chroma DB collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding chunks to Chroma DB: {e}")
            raise VectorStoreError(f"Error adding chunks to Chroma DB: {str(e)}")

    def delete_by_source(self, source: str):
        """
        Delete all indexed chunks associated with a specific source document.
        
        Args:
            source: Filename of the source document.
        """
        try:
            self.collection.delete(where={"source": source})
            logger.info(f"Deleted all chunks associated with source: {source}")
        except Exception as e:
            logger.error(f"Error deleting source {source} from Chroma DB: {e}")
            raise VectorStoreError(f"Error deleting source {source} from Chroma DB: {str(e)}")

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for most similar document chunks.
        
        Args:
            query_embedding: The embedding of the user query.
            top_k: Number of results to retrieve.
            
        Returns:
            List of search results, each containing 'content', 'metadata', and 'score'.
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            formatted_results = []
            if not results or not results["documents"] or not results["documents"][0]:
                return []
                
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(documents)
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                # Chroma distance is often L2 or Cosine distance. Cosine Similarity = 1 - Cosine Distance.
                similarity_score = 1.0 - dist
                formatted_results.append({
                    "content": doc,
                    "metadata": meta,
                    "score": similarity_score
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            raise VectorStoreError(f"Error performing similarity search: {str(e)}")
