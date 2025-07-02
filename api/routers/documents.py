import os
import sys
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Add parent directory to Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aimakerspace.multi_document_processor import MultiDocumentProcessor
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.rag_pipeline import RAGPipeline
from models.responses import UploadResponse, MultiDocumentUploadResponse
from services.session_service import SessionService
from services.global_kb_service import GlobalKnowledgeBaseService

router = APIRouter()

# Services
session_service = SessionService()
global_kb_service = GlobalKnowledgeBaseService()

@router.post("/upload-document", response_model=UploadResponse)
async def upload_document_to_knowledge_base(
    file: UploadFile = File(...),
    session_id: str = None,
    api_key: str = None
):
    """Upload a document to user's knowledge base"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        # Get or create session
        session_id = await session_service.get_or_create_session(session_id, api_key)
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save uploaded file temporarily
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Process the document
            multi_doc_processor = MultiDocumentProcessor()
            processed_docs = multi_doc_processor.process_document(temp_file_path, file.filename)
            
            if not processed_docs:
                raise HTTPException(status_code=400, detail="Could not process the uploaded document")
            
            # Add to session's vector database
            vector_db = session["vector_db"]
            
            # Ensure embedding model is properly initialized
            if not hasattr(vector_db, "embedding_model") or not vector_db.embedding_model:
                embedding_model = EmbeddingModel(api_key=api_key)
                vector_db.embedding_model = embedding_model
            
            # Generate embeddings and add to vector database
            for doc in processed_docs:
                try:
                    # Generate embedding for the document content
                    embeddings = await vector_db.embedding_model.async_get_embeddings([doc.content])
                    
                    # Add document to vector database
                    vector_db.insert(doc.content, embeddings[0], doc.metadata)
                except Exception as e:
                    print(f"Warning: Failed to add document chunk to vector database: {e}")
                    continue
            
            # Update session
            session["documents"].append(file.filename)
            
            # Create/update RAG pipeline for the session
            chat_model = ChatOpenAI(api_key=api_key)
            session["rag_pipeline"] = RAGPipeline(llm=chat_model, vector_db=vector_db)
            
            return UploadResponse(
                success=True,
                message=f"Successfully uploaded and processed {file.filename}",
                session_id=session_id,
                document_count=len(session["documents"]),
                filename=file.filename
            )
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.post("/upload-multi-document", response_model=MultiDocumentUploadResponse)
async def upload_multi_format_document(
    file: UploadFile = File(...),
    session_id: str = None,
    api_key: str = None
):
    """Upload a multi-format document with enhanced processing"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        # Get or create session
        session_id = await session_service.get_or_create_session(session_id, api_key)
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save uploaded file temporarily
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Process the document with enhanced processing
            multi_doc_processor = MultiDocumentProcessor()
            processed_docs = multi_doc_processor.process_document(temp_file_path, file.filename)
            
            if not processed_docs:
                raise HTTPException(status_code=400, detail="Could not process the uploaded document")
            
            # Get document type and regulatory type from first processed document
            doc_type = processed_docs[0].doc_type if processed_docs else "unknown"
            regulatory_type = processed_docs[0].metadata.get("regulatory_type", "general")
            
            # Add to session's vector database
            vector_db = session["vector_db"]
            
            # Ensure embedding model is properly initialized
            if not hasattr(vector_db, "embedding_model") or not vector_db.embedding_model:
                embedding_model = EmbeddingModel(api_key=api_key)
                vector_db.embedding_model = embedding_model
            
            # Generate embeddings and add to vector database
            chunks_created = 0
            for doc in processed_docs:
                try:
                    # Generate embedding for the document content
                    embeddings = await vector_db.embedding_model.async_get_embeddings([doc.content])
                    
                    # Add document to vector database
                    vector_db.insert(doc.content, embeddings[0], doc.metadata)
                    chunks_created += 1
                except Exception as e:
                    print(f"Warning: Failed to add document chunk to vector database: {e}")
                    continue
            
            # Update session
            session["documents"].append(file.filename)
            
            # Create/update RAG pipeline for the session
            chat_model = ChatOpenAI(api_key=api_key)
            session["rag_pipeline"] = RAGPipeline(llm=chat_model, vector_db=vector_db)
            
            return MultiDocumentUploadResponse(
                success=True,
                message=f"Successfully uploaded and processed {file.filename}",
                session_id=session_id,
                document_count=len(session["documents"]),
                filename=file.filename,
                doc_type=doc_type,
                regulatory_type=regulatory_type,
                chunks_created=chunks_created
            )
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return session_service.list_sessions()

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session"""
    success = session_service.delete_session(session_id)
    if success:
        return {"success": True, "message": f"Session {session_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@router.get("/global-knowledge-base")
async def get_global_knowledge_base_info():
    """Get information about the global knowledge base"""
    return global_kb_service.get_info()

@router.post("/initialize-global-kb")
async def initialize_global_knowledge_base():
    """Initialize the global knowledge base with documents from the documents folder"""
    try:
        await global_kb_service.initialize_global_knowledge_base()
        return {
            "success": True,
            "message": "Global knowledge base initialization started",
            "info": global_kb_service.get_info()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize global knowledge base: {str(e)}") 