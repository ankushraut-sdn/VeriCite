import os
from backend.src.loaders.base import BaseLoader
from backend.src.exceptions import LoaderError

class TextLoader(BaseLoader):
    """Loader for plain text files (.txt)."""

    def load(self, file_path: str) -> str:
        """
        Load a text file and return its contents.
        
        Args:
            file_path: Path to the text file.
            
        Returns:
            The plain text contents of the file.
            
        Raises:
            LoaderError: If the file cannot be read or decoded.
        """
        if not os.path.exists(file_path):
            raise LoaderError(f"Text file not found: {file_path}")
            
        try:
            # Attempt to read as UTF-8, fallback to latin-1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            return content
        except Exception as e:
            raise LoaderError(f"Error reading text file {file_path}: {str(e)}")
