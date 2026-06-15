import os
import io
from backend.src.loaders.base import BaseLoader
from backend.src.exceptions import LoaderError

class PDFLoader(BaseLoader):
    """Loader for PDF documents. Extracts text page-by-page and injects page-marker comments."""

    def load(self, file_path: str) -> str:
        """
        Load a PDF file, extract its text page-by-page, and format as Markdown with page markers.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            The content converted to Markdown string with page markers.
            
        Raises:
            LoaderError: If PDF extraction fails.
        """
        if not os.path.exists(file_path):
            raise LoaderError(f"PDF file not found: {file_path}")
            
        try:
            from pdfminer.pdfpage import PDFPage
            from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
            from pdfminer.converter import TextConverter
            from pdfminer.layout import LAParams
        except ImportError:
            raise LoaderError("pdfminer.six is not installed. Please install it to load PDF files.")

        try:
            rsrcmgr = PDFResourceManager()
            laparams = LAParams()
            markdown_parts = []
            
            with open(file_path, "rb") as fp:
                for page_num, page in enumerate(PDFPage.get_pages(fp), start=1):
                    retstr = io.StringIO()
                    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
                    interpreter = PDFPageInterpreter(rsrcmgr, device)
                    interpreter.process_page(page)
                    text = retstr.getvalue()
                    device.close()
                    retstr.close()
                    
                    cleaned_text = text.strip()
                    if cleaned_text:
                        # Append a markdown-friendly page comment marker
                        markdown_parts.append(f"<!-- PAGE: {page_num} -->\n{cleaned_text}")
                        
            return "\n\n".join(markdown_parts)
            
        except Exception as e:
            raise LoaderError(f"Error reading and converting PDF file {file_path}: {str(e)}")
