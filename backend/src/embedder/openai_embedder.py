import logging
import hashlib
import numpy as np
from typing import List
from backend.src import config
from backend.src.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

class OpenAIEmbedder:
    """Embedding generator using OpenAI's API, with a deterministic mock fallback for offline/testing use."""

    def __init__(self):
        self.model = config.EMBEDDING_MODEL
        self.api_key = config.OPENAI_API_KEY
        self.dimension = 1536  # Default dimension for text-embedding-3-small
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"Initialized OpenAIEmbedder with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Falling back to mock embedder.")
        else:
            logger.warning("No OPENAI_API_KEY found in configuration. Using deterministic mock embedder.")

    def _get_mock_embedding(self, text: str) -> List[float]:
        """Generate a deterministic mock embedding vector based on text word hashing."""
        vector = np.zeros(self.dimension)
        words = text.lower().split()
        if not words:
            return [0.0] * self.dimension
            
        for word in words:
            h = hashlib.sha256(word.encode("utf-8")).digest()
            seed = int.from_bytes(h[:4], byteorder="big")
            rng = np.random.default_rng(seed)
            vector += rng.normal(size=self.dimension)
            
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of text chunks.
        
        Args:
            texts: List of text chunks to embed.
            
        Returns:
            List of embedding vectors.
            
        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not texts:
            return []
            
        if self.client:
            try:
                # Limit batch size to 2048 (OpenAI's limit is larger, but 2048 is safe)
                batch_size = 512
                embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = self.client.embeddings.create(
                        input=batch,
                        model=self.model
                    )
                    embeddings.extend([data.embedding for data in response.data])
                return embeddings
            except Exception as e:
                logger.error(f"OpenAI embedding generation failed: {e}")
                raise EmbeddingError(f"OpenAI embedding generation failed: {str(e)}")
        else:
            # Return deterministic mock embeddings
            return [self._get_mock_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.
        
        Args:
            text: Query string to embed.
            
        Returns:
            Embedding vector.
            
        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not text:
            return [0.0] * self.dimension
            
        if self.client:
            try:
                response = self.client.embeddings.create(
                    input=[text],
                    model=self.model
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"OpenAI query embedding failed: {e}")
                raise EmbeddingError(f"OpenAI query embedding failed: {str(e)}")
        else:
            return self._get_mock_embedding(text)
