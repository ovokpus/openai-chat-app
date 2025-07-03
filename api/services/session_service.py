import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Add api directory to path for aimakerspace imports
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel

class SessionService:
    def __init__(self):
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def get_or_create_session(self, session_id: Optional[str] = None, api_key: Optional[str] = None) -> str:
        """Get existing session or create new one"""
        if session_id and session_id in self.user_sessions:
            session = self.user_sessions[session_id]
            # Ensure the vector database has a properly initialized embedding model
            if api_key and (not hasattr(session["vector_db"], "embedding_model") or 
                           not hasattr(session["vector_db"].embedding_model, "openai_api_key") or
                           session["vector_db"].embedding_model.openai_api_key != api_key):
                # Create a new embedding model with the current API key
                embedding_model = EmbeddingModel(api_key=api_key)
                session["vector_db"].embedding_model = embedding_model
                session["api_key"] = api_key
            return session_id
        
        new_session_id = str(uuid.uuid4())
        
        # Always create VectorDatabase with embedding model that has API key
        if api_key:
            embedding_model = EmbeddingModel(api_key=api_key)
            vector_db = VectorDatabase(embedding_model=embedding_model)
            
            self.user_sessions[new_session_id] = {
                "vector_db": vector_db,
                "documents": [],
                "created_at": datetime.now().isoformat(),
                "rag_pipeline": None,
                "api_key": api_key,
                "global_kb": None,
                "has_global_kb": False
            }
        else:
            # Create a vector database without embedding model - will need to be initialized later
            vector_db = VectorDatabase()
            self.user_sessions[new_session_id] = {
                "vector_db": vector_db,
                "documents": [],
                "created_at": datetime.now().isoformat(),
                "rag_pipeline": None,
                "api_key": api_key,
                "global_kb": None,
                "has_global_kb": False
            }
        
        return new_session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.user_sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session by ID"""
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all sessions"""
        return {
            "total_sessions": len(self.user_sessions),
            "sessions": [
                {
                    "session_id": sid,
                    "document_count": len(session.get("documents", [])),
                    "created_at": session.get("created_at", ""),
                    "has_global_kb": session.get("has_global_kb", False)
                }
                for sid, session in self.user_sessions.items()
            ]
        } 