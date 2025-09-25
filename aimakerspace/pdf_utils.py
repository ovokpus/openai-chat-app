import logging
from typing import List, Optional, Dict, Any
from pypdf import PdfReader
import concurrent.futures
import functools

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
        self._metadata_cache: Optional[Dict[str, Any]] = None
        
    @functools.lru_cache(maxsize=1)
    def _load_reader(self) -> None:
        """Load the PDF reader if not already loaded."""
        if self.reader is None:
            try:
                self.reader = PdfReader(self.file_path)
            except Exception as e:
                logging.error(f"Failed to load PDF file {self.file_path}: {e}")
                raise
    
    def _extract_page_text(self, page_info: tuple) -> Optional[str]:
        """
        Extract text from a single page.
        
        Args:
            page_info (tuple): Tuple containing (page_num, page)
            
        Returns:
            Optional[str]: Extracted text or None if extraction failed
        """
        page_num, page = page_info
        try:
            text = page.extract_text()
            if text.strip():  # Only return non-empty pages
                return text.strip()
        except Exception as e:
            logging.warning(f"Failed to extract text from page {page_num + 1}: {e}")
        return None
    
    def load_documents(self) -> List[str]:
        """
        Extract text from all pages of the PDF using parallel processing.
        
        Returns:
            List[str]: List of text content from each page
        """
        self._load_reader()
        
        if not self.reader:
            return []
        
        documents = []
        
        try:
            # Create list of (page_num, page) tuples for parallel processing
            pages = list(enumerate(self.reader.pages))
            
            # Process pages in parallel using a thread pool
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Map the extraction function over all pages
                results = list(executor.map(self._extract_page_text, pages))
            
            # Filter out None results and add valid texts to documents
            documents = [text for text in results if text]
                    
        except Exception as e:
            logging.error(f"Failed to process PDF pages: {e}")
            raise
        
        return documents
    
    def get_page_count(self) -> int:
        """Get the total number of pages in the PDF."""
        self._load_reader()
        return len(self.reader.pages) if self.reader else 0
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from the PDF file."""
        if self._metadata_cache is not None:
            return self._metadata_cache
        
        self._load_reader()
        metadata = {
            "page_count": self.get_page_count(),
            "file_type": "pdf"
        }
        
        if self.reader and self.reader.metadata:
            # Extract standard PDF metadata
            for key in ["/Title", "/Author", "/Subject", "/Keywords", "/Creator", "/Producer"]:
                if key in self.reader.metadata:
                    clean_key = key.replace("/", "").lower()
                    metadata[clean_key] = str(self.reader.metadata[key])
            
            # Add creation and modification dates if available
            if "/CreationDate" in self.reader.metadata:
                metadata["created"] = str(self.reader.metadata["/CreationDate"])
            if "/ModDate" in self.reader.metadata:
                metadata["modified"] = str(self.reader.metadata["/ModDate"])
        
        self._metadata_cache = metadata
        return metadata 