from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os
from datetime import datetime
import uuid

# Add the project root to the Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/api")

# Global storage for user sessions and their documents
user_sessions = {}

class RAGChatRequest(BaseModel):
    user_message: str
    session_id: str
    model: Optional[str] = "gpt-4o-mini"
    api_key: str
    use_rag: bool = True

def get_or_create_session(session_id: Optional[str] = None, api_key: Optional[str] = None) -> str:
    if session_id and session_id in user_sessions:
        session = user_sessions[session_id]
        if api_key and (not hasattr(session["vector_db"], "embedding_model") or 
                       not hasattr(session["vector_db"].embedding_model, "openai_api_key") or
                       session["vector_db"].embedding_model.openai_api_key != api_key):
            print(f"🔧 Updating session {session_id} with new API key")
            embedding_model = EmbeddingModel(api_key=api_key)
            session["vector_db"].embedding_model = embedding_model
            session["api_key"] = api_key
        return session_id
    
    new_session_id = str(uuid.uuid4())
    
    if api_key:
        embedding_model = EmbeddingModel(api_key=api_key)
        vector_db = VectorDatabase(embedding_model=embedding_model)
    else:
        vector_db = VectorDatabase()
    
    user_sessions[new_session_id] = {
        "vector_db": vector_db,
        "documents": [],
        "created_at": datetime.now().isoformat(),
        "rag_pipeline": None,
        "api_key": api_key
    }
    return new_session_id

@router.post("/rag-chat")
async def rag_chat(request: RAGChatRequest):
    try:
        session_id = get_or_create_session(request.session_id, request.api_key)
        session = user_sessions[session_id]
        
        if not session["documents"] and request.use_rag:
            raise HTTPException(
                status_code=400,
                detail="No documents uploaded for RAG. Please upload documents first or disable RAG mode."
            )
        
        if request.use_rag and not session["rag_pipeline"]:
            chat_model = ChatOpenAI(api_key=request.api_key)
            session["rag_pipeline"] = RAGPipeline(
                vector_db=session["vector_db"],
                chat_model=chat_model
            )
        
        async def generate():
            if request.use_rag:
                async for chunk in session["rag_pipeline"].agenerate_response(request.user_message):
                    yield chunk
            else:
                chat_model = ChatOpenAI(api_key=request.api_key)
                async for chunk in chat_model.agenerate_response(request.user_message):
                    yield chunk
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 