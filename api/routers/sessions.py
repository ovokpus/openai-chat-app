from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Global storage for user sessions and their documents
user_sessions = {}

class SessionInfo(BaseModel):
    session_id: str
    document_count: int
    documents: List[str]
    created_at: str

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    try:
        sessions = []
        for session_id, session in user_sessions.items():
            sessions.append({
                "session_id": session_id,
                "document_count": len(session["documents"]),
                "documents": session["documents"],
                "created_at": session["created_at"]
            })
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a specific session"""
    try:
        if session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = user_sessions[session_id]
        return SessionInfo(
            session_id=session_id,
            document_count=len(session["documents"]),
            documents=session["documents"],
            created_at=session["created_at"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session"""
    try:
        if session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        del user_sessions[session_id]
        return {"success": True, "message": f"Session {session_id} deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 