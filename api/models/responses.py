from pydantic import BaseModel
from typing import List

class UploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    document_count: int
    filename: str

class MultiDocumentUploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    document_count: int
    filename: str
    doc_type: str
    regulatory_type: str
    chunks_created: int

class SessionInfo(BaseModel):
    session_id: str
    document_count: int
    documents: List[str]
    created_at: str 