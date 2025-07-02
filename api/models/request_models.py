from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    developer_message: str
    user_message: str
    model: Optional[str] = "gpt-4o-mini"
    api_key: str

class RAGChatRequest(BaseModel):
    user_message: str
    session_id: str
    model: Optional[str] = "gpt-4o-mini"
    api_key: str
    use_rag: bool = True

class RegulatoryRAGRequest(BaseModel):
    user_message: str
    session_id: str
    user_role: Optional[str] = "general"
    model: Optional[str] = "gpt-4o-mini"
    api_key: str
    use_rag: bool = True
    doc_types: Optional[List[str]] = None
    priority_sources: Optional[List[str]] = None 