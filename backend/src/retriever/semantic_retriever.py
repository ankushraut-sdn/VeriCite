import logging
from typing import List, Dict, Any
from backend.src.embedder.openai_embedder import OpenAIEmbedder
from backend.src.vectordb.chroma_store import ChromaStore

logger = logging.getLogger(__name__)

class SemanticRetriever:
    """Retriever that generates query embeddings and performs similarity searches with configurable filters."""

    def __init__(self, embedder: OpenAIEmbedder, store: ChromaStore):
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: str, top_k: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        Embed query, perform similarity search, and apply relevance filtering.
        
        Args:
            query: The user query string.
            top_k: Maximum number of chunks to retrieve.
            min_similarity: Minimum cosine similarity score threshold (0.0 to 1.0).
            
        Returns:
            List of matching chunk dicts sorted by relevance score.
        """
        if not query.strip():
            return []
            
        logger.info(f"Retrieving chunks for query: '{query}' (top_k={top_k}, min_similarity={min_similarity})")
        
        # 1. Embed query
        query_embedding = self.embedder.embed_query(query)
        
        # 2. Similarity search in Vector DB
        raw_results = self.store.similarity_search(query_embedding, top_k=top_k)
        
        # 3. Filter by minimum similarity score
        filtered_results = []
        for result in raw_results:
            score = result.get("score", 0.0)
            if score >= min_similarity:
                filtered_results.append(result)
            else:
                logger.debug(f"Filtered out chunk from {result['metadata'].get('source')} due to low score: {score:.4f}")
                
        logger.info(f"Retrieved {len(filtered_results)} relevant chunks after applying similarity threshold.")
        return filtered_results
