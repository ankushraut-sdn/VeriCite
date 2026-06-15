import re
import time
from typing import List, Dict, Any
from backend.src.exceptions import ChunkerError

class DocumentChunker:
    """Intelligent chunker that preserves page boundaries and metadata while cleaning text."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        except ImportError:
            raise ChunkerError("langchain is not installed. Please install it to use DocumentChunker.")

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw input text.
            
        Returns:
            Cleaned and normalized text.
        """
        if not text:
            return ""
        # Remove multiple consecutive blank lines, replacing with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace multiple consecutive spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def chunk_document(self, text: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split document text into chunks while preserving page numbers and adding rich metadata.
        
        Args:
            text: The full Markdown content of the document.
            base_metadata: Dict containing file metadata (source, file_size, etc.).
            
        Returns:
            A list of chunk dicts, each with 'content' and 'metadata'.
            
        Raises:
            ChunkerError: If chunking fails.
        """
        try:
            # Regular expression to find page markers: <!-- PAGE: 1 -->
            page_pattern = r"<!-- PAGE:\s*(\d+)\s*-->"
            matches = list(re.finditer(page_pattern, text))
            
            pages = []
            if not matches:
                # No page markers found (e.g. TXT, DOCX, MD)
                pages.append((1, text))
            else:
                # Handle text before the first page marker
                first_match = matches[0]
                if first_match.start() > 0:
                    intro_text = text[0:first_match.start()].strip()
                    if intro_text:
                        pages.append((1, intro_text))
                
                for i, match in enumerate(matches):
                    page_num = int(match.group(1))
                    start_pos = match.end()
                    end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
                    page_text = text[start_pos:end_pos]
                    pages.append((page_num, page_text))
            
            chunks = []
            chunk_global_idx = 0
            
            for page_num, page_text in pages:
                cleaned_page_text = self.clean_text(page_text)
                if not cleaned_page_text:
                    continue
                
                # Split the page text
                page_chunks = self.splitter.split_text(cleaned_page_text)
                
                for idx, chunk_content in enumerate(page_chunks):
                    chunk_content = chunk_content.strip()
                    if not chunk_content:
                        continue
                        
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata.update({
                        "page": page_num,
                        "chunk_index": chunk_global_idx,
                        "page_chunk_index": idx,
                        "timestamp": time.time()
                    })
                    
                    chunks.append({
                        "content": chunk_content,
                        "metadata": chunk_metadata
                    })
                    chunk_global_idx += 1
                    
            return chunks
            
        except Exception as e:
            raise ChunkerError(f"Error during chunking process: {str(e)}")
