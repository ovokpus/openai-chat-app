import logging
from typing import List, Optional
from pypdf import PdfReader

class PDFFileLoader:
    """A utility class for loading and extracting text from PDF files."""
    
    def __init__(self, file_path: str):
        """
        Initialize the PDF loader with a file path.
        
        Args:
            file_path (str): Path to the PDF file
        """
        self.file_path = file_path
        self.reader: Optional[PdfReader] = None
        
    def _load_reader(self) -> None:
        """Load the PDF reader if not already loaded."""
        if self.reader is None:
            try:
                self.reader = PdfReader(self.file_path)
            except Exception as e:
                logging.error(f"Failed to load PDF file {self.file_path}: {e}")
                raise
    
    def load_documents(self) -> List[str]:
        """
        Extract text from all pages of the PDF.
        
        Returns:
            List[str]: List of text content from each page
        """
        self._load_reader()
        
        if not self.reader:
            return []
        
        documents = []
        
        try:
            for page_num, page in enumerate(self.reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():  # Only add non-empty pages
                        documents.append(text.strip())
                except Exception as e:
                    logging.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Failed to process PDF pages: {e}")
            raise
        
        return documents
    
    def get_page_count(self) -> int:
        """
        Get the number of pages in the PDF.
        
        Returns:
            int: Number of pages
        """
        self._load_reader()
        
        if not self.reader:
            return 0
            
        return len(self.reader.pages)
    
    def get_metadata(self) -> dict:
        """
        Get PDF metadata.
        
        Returns:
            dict: PDF metadata
        """
        self._load_reader()
        
        if not self.reader or not self.reader.metadata:
            return {}
        
        metadata = {}
        for key, value in self.reader.metadata.items():
            metadata[key] = str(value) if value else ""
        
        return metadata 