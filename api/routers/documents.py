from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import sys
import os
import tempfile
from pathlib import Path
import uuid
from datetime import datetime

# Add the project root to the Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aimakerspace.file_utils import UniversalFileProcessor
from aimakerspace.text_utils import CharacterTextSplitter
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.vectordatabase import VectorDatabase

router = APIRouter()

# Global storage for user sessions and their documents
user_sessions = {}

class UploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    document_count: int
    filename: str

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

@router.post("/api/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: str = Form(...)
):
    try:
        print(f"📁 Starting document upload: {file.filename}")
        
        if not UniversalFileProcessor.validate_file(file.filename, file.content_type):
            supported_types = ", ".join(UniversalFileProcessor.get_supported_extensions())
            print(f"❌ Invalid file type: {file.filename} (content-type: {file.content_type})")
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types: {supported_types}")
        
        print(f"✅ File validation passed")
        
        session_id = get_or_create_session(session_id, api_key)
        session = user_sessions[session_id]
        print(f"✅ Session created/retrieved: {session_id}")
        
        file_extension = Path(file.filename).suffix.lower() if file.filename else '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        print(f"✅ File saved temporarily: {tmp_file_path}")
        
        try:
            print(f"📄 Loading document...")
            file_processor = UniversalFileProcessor(tmp_file_path)
            documents = file_processor.load_documents()
            
            if not documents:
                print(f"❌ No text extracted from document")
                raise HTTPException(status_code=400, detail="No text could be extracted from the document")
            
            print(f"✅ Extracted {len(documents)} documents")
            
            print(f"✂️ Splitting text into chunks...")
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = text_splitter.split_texts(documents)
            
            print(f"✅ Created {len(chunks)} chunks")
            
            print(f"🔍 Adding chunks to vector database...")
            session["vector_db"].add_texts(chunks, metadata={"filename": file.filename})
            session["documents"].append(file.filename)
            
            print(f"✅ Added chunks to vector database")
            
            return UploadResponse(
                success=True,
                message="Document uploaded and processed successfully",
                session_id=session_id,
                document_count=len(session["documents"]),
                filename=file.filename
            )
            
        finally:
            os.unlink(tmp_file_path)
            print(f"🧹 Cleaned up temporary file")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/documents/{session_id}/{document_name}")
async def delete_document(session_id: str, document_name: str, api_key: str):
    try:
        if session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = user_sessions[session_id]
        
        if document_name not in session["documents"]:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove document from the list
        session["documents"].remove(document_name)
        
        # Clear and rebuild vector database with remaining documents
        session["vector_db"] = VectorDatabase(embedding_model=EmbeddingModel(api_key=api_key))
        session["rag_pipeline"] = None
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 