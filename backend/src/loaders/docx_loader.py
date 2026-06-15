import os
from backend.src.loaders.base import BaseLoader
from backend.src.exceptions import LoaderError

class DocxLoader(BaseLoader):
    """Loader for Microsoft Word documents (.docx). Converts structure to clean Markdown."""

    def load(self, file_path: str) -> str:
        """
        Load a DOCX file and convert its content (paragraphs and tables) to Markdown.
        
        Args:
            file_path: Path to the DOCX file.
            
        Returns:
            The content converted to Markdown string.
            
        Raises:
            LoaderError: If DOCX reading or conversion fails.
        """
        if not os.path.exists(file_path):
            raise LoaderError(f"DOCX file not found: {file_path}")
            
        try:
            import docx
        except ImportError:
            raise LoaderError("python-docx package is not installed. Please install it to load DOCX files.")

        try:
            doc = docx.Document(file_path)
            markdown_parts = []
            
            # Helper to convert a paragraph to Markdown
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                style_name = para.style.name.lower() if para.style else ""
                
                if "heading 1" in style_name:
                    markdown_parts.append(f"# {text}")
                elif "heading 2" in style_name:
                    markdown_parts.append(f"## {text}")
                elif "heading 3" in style_name:
                    markdown_parts.append(f"### {text}")
                elif "heading 4" in style_name:
                    markdown_parts.append(f"#### {text}")
                elif "list bullet" in style_name:
                    markdown_parts.append(f"- {text}")
                elif "list number" in style_name:
                    markdown_parts.append(f"1. {text}")
                else:
                    # Check runs for bold / italic formatting
                    formatted_text = ""
                    for run in para.runs:
                        run_text = run.text
                        if not run_text:
                            continue
                        if run.bold and run.italic:
                            formatted_text += f"***{run_text}***"
                        elif run.bold:
                            formatted_text += f"**{run_text}**"
                        elif run.italic:
                            formatted_text += f"*{run_text}*"
                        else:
                            formatted_text += run_text
                    
                    markdown_parts.append(formatted_text.strip())

            # Convert tables to Markdown tables
            for table in doc.tables:
                table_md = []
                for i, row in enumerate(table.rows):
                    row_cells = [cell.text.strip().replace("\n", "<br>") for cell in row.cells]
                    table_md.append("| " + " | ".join(row_cells) + " |")
                    
                    # Add divider after the header row
                    if i == 0:
                        dividers = ["---"] * len(row_cells)
                        table_md.append("| " + " | ".join(dividers) + " |")
                
                if table_md:
                    markdown_parts.append("\n".join(table_md))
                    
            return "\n\n".join(markdown_parts)
            
        except Exception as e:
            raise LoaderError(f"Error reading and converting DOCX file {file_path}: {str(e)}")
