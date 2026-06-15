import os
import time
from abc import ABC, abstractmethod
from backend.src.exceptions import LoaderError

class BaseLoader(ABC):
    """Abstract base class for all document loaders in the RAG system."""

    @abstractmethod
    def load(self, file_path: str) -> str:
        """
        Load a document and convert its contents to Markdown format.
        
        Args:
            file_path: Absolute or relative path to the file.
            
        Returns:
            The document content converted to Markdown string.
            
        Raises:
            LoaderError: If loading or parsing fails.
        """
        pass

    def extract_metadata(self, file_path: str) -> dict:
        """
        Extract basic metadata from the file.
        
        Args:
            file_path: Absolute or relative path to the file.
            
        Returns:
            A dictionary containing metadata.
        """
        try:
            if not os.path.exists(file_path):
                raise LoaderError(f"File not found: {file_path}")
            
            stat = os.stat(file_path)
            return {
                "source": os.path.basename(file_path),
                "file_path": os.path.abspath(file_path),
                "file_size": stat.st_size,
                "created_at": time.ctime(stat.st_ctime),
                "updated_at": time.ctime(stat.st_mtime)
            }
        except Exception as e:
            if isinstance(e, LoaderError):
                raise
            raise LoaderError(f"Failed to extract metadata for {file_path}: {str(e)}")
