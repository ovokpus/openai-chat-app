import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import mimetypes
from abc import ABC, abstractmethod

# Import existing utilities
from .pdf_utils import PDFFileLoader
from .text_utils import TextFileLoader

class FileProcessorBase(ABC):
    """Abstract base class for file processors."""
    
    @abstractmethod
    def load_documents(self) -> List[str]:
        """Extract text content from the file."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from the file."""
        pass

class PDFProcessor(FileProcessorBase):
    """PDF file processor using existing PDFFileLoader."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.loader = PDFFileLoader(file_path)
    
    def load_documents(self) -> List[str]:
        return self.loader.load_documents()
    
    def get_metadata(self) -> Dict[str, Any]:
        metadata = self.loader.get_metadata()
        metadata.update({
            "file_type": "pdf",
            "page_count": self.loader.get_page_count()
        })
        return metadata

class TextProcessor(FileProcessorBase):
    """Plain text file processor."""
    
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding
    
    def load_documents(self) -> List[str]:
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.read().strip()
                return [content] if content else []
        except Exception as e:
            logging.error(f"Failed to load text file {self.file_path}: {e}")
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        file_path = Path(self.file_path)
        return {
            "file_type": "text",
            "encoding": self.encoding,
            "file_size": file_path.stat().st_size,
            "filename": file_path.name
        }

class MarkdownProcessor(FileProcessorBase):
    """Markdown file processor."""
    
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding
    
    def load_documents(self) -> List[str]:
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                content = f.read().strip()
                return [content] if content else []
        except Exception as e:
            logging.error(f"Failed to load markdown file {self.file_path}: {e}")
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        file_path = Path(self.file_path)
        return {
            "file_type": "markdown",
            "encoding": self.encoding,
            "file_size": file_path.stat().st_size,
            "filename": file_path.name
        }

class CSVProcessor(FileProcessorBase):
    """CSV file processor that treats each row as a document."""
    
    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding
    
    def load_documents(self) -> List[str]:
        try:
            import csv
            documents = []
            
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for i, row in enumerate(reader):
                    # Convert row to text representation
                    row_text = "\n".join([f"{key}: {value}" for key, value in row.items() if value])
                    if row_text.strip():
                        documents.append(f"Row {i+1}:\n{row_text}")
            
            return documents
        except Exception as e:
            logging.error(f"Failed to load CSV file {self.file_path}: {e}")
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        file_path = Path(self.file_path)
        return {
            "file_type": "csv",
            "encoding": self.encoding,
            "file_size": file_path.stat().st_size,
            "filename": file_path.name
        }

class DOCXProcessor(FileProcessorBase):
    """DOCX file processor for Microsoft Word documents."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def load_documents(self) -> List[str]:
        try:
            from docx import Document
            
            doc = Document(self.file_path)
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    paragraphs.append(text)
            
            # Join paragraphs into a single document
            content = "\n\n".join(paragraphs)
            return [content] if content else []
            
        except ImportError:
            raise ImportError("python-docx package is required to process DOCX files. Install with: pip install python-docx")
        except Exception as e:
            logging.error(f"Failed to load DOCX file {self.file_path}: {e}")
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        try:
            from docx import Document
            doc = Document(self.file_path)
            
            file_path = Path(self.file_path)
            metadata = {
                "file_type": "docx",
                "file_size": file_path.stat().st_size,
                "filename": file_path.name,
                "paragraph_count": len(doc.paragraphs)
            }
            
            # Add document properties if available
            if doc.core_properties:
                core_props = doc.core_properties
                if core_props.title:
                    metadata["title"] = core_props.title
                if core_props.author:
                    metadata["author"] = core_props.author
                if core_props.created:
                    metadata["created"] = core_props.created.isoformat()
                if core_props.modified:
                    metadata["modified"] = core_props.modified.isoformat()
            
            return metadata
            
        except ImportError:
            file_path = Path(self.file_path)
            return {
                "file_type": "docx",
                "file_size": file_path.stat().st_size,
                "filename": file_path.name
            }
        except Exception as e:
            logging.warning(f"Failed to extract DOCX metadata: {e}")
            file_path = Path(self.file_path)
            return {
                "file_type": "docx",
                "file_size": file_path.stat().st_size,
                "filename": file_path.name
            }

class UniversalFileProcessor:
    """Universal file processor that can handle multiple file types."""
    
    # Supported file types and their extensions
    SUPPORTED_TYPES = {
        '.pdf': PDFProcessor,
        '.txt': TextProcessor,
        '.md': MarkdownProcessor,
        '.markdown': MarkdownProcessor,
        '.csv': CSVProcessor,
        '.docx': DOCXProcessor,
    }
    
    # MIME type mapping for additional validation
    MIME_TYPES = {
        'application/pdf': '.pdf',
        'text/plain': '.txt',
        'text/markdown': '.md',
        'text/csv': '.csv',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    }
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_extension = self._get_file_extension()
        self.processor = self._create_processor()
    
    def _get_file_extension(self) -> str:
        """Get the file extension in lowercase."""
        return Path(self.file_path).suffix.lower()
    
    def _create_processor(self) -> FileProcessorBase:
        """Create the appropriate processor for the file type."""
        if self.file_extension not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: {self.file_extension}. Supported types: {list(self.SUPPORTED_TYPES.keys())}")
        
        processor_class = self.SUPPORTED_TYPES[self.file_extension]
        return processor_class(self.file_path)
    
    def load_documents(self) -> List[str]:
        """Extract text content from the file."""
        return self.processor.load_documents()
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from the file."""
        return self.processor.get_metadata()
    
    @classmethod
    def is_supported_file(cls, filename: str) -> bool:
        """Check if a file type is supported."""
        extension = Path(filename).suffix.lower()
        return extension in cls.SUPPORTED_TYPES
    
    @classmethod
    def is_supported_mime_type(cls, mime_type: str) -> bool:
        """Check if a MIME type is supported."""
        return mime_type in cls.MIME_TYPES
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of supported file extensions."""
        return list(cls.SUPPORTED_TYPES.keys())
    
    @classmethod
    def get_supported_mime_types(cls) -> List[str]:
        """Get list of supported MIME types."""
        return list(cls.MIME_TYPES.keys())
    
    @classmethod
    def validate_file(cls, filename: str, mime_type: Optional[str] = None) -> bool:
        """Validate if a file is supported based on filename and/or MIME type."""
        # Check by extension
        if cls.is_supported_file(filename):
            return True
        
        # Check by MIME type if provided
        if mime_type and cls.is_supported_mime_type(mime_type):
            return True
        
        return False 