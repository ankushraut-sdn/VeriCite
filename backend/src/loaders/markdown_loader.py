from backend.src.loaders.txt_loader import TextLoader

class MarkdownLoader(TextLoader):
    """Loader for Markdown files (.md). Passes content through as-is since format is already Markdown."""
    pass
