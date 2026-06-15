class RAGError(Exception):
    """Base exception class for the RAG system."""
    pass

class LoaderError(RAGError):
    """Exception raised when document loading or parsing fails."""
    pass

class ChunkerError(RAGError):
    """Exception raised when document chunking fails."""
    pass

class EmbeddingError(RAGError):
    """Exception raised when embedding generation fails."""
    pass

class VectorStoreError(RAGError):
    """Exception raised when vector database operations fail."""
    pass

class LLMError(RAGError):
    """Exception raised when LLM generation fails."""
    pass

class ValidationError(RAGError):
    """Exception raised when inputs fail security or size validation."""
    pass

class OrchestratorError(RAGError):
    """Exception raised when the orchestrator pipeline fails."""
    pass
