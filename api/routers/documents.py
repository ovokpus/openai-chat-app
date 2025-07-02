import os
import sys
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

# Add parent directory to Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aimakerspace.multi_document_processor import MultiDocumentProcessor
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.rag_pipeline import RAGPipeline
from models.responses import UploadResponse, MultiDocumentUploadResponse

router = APIRouter()

# Services - using shared instances
from services.dependencies import session_service, global_kb_service

@router.post("/upload-document", response_model=UploadResponse)
async def upload_document_to_knowledge_base(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    api_key: str = Form(...)
):
    """Upload a document to the global knowledge base (available to all users)"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        print(f"📁 Starting document upload to global knowledge base: {file.filename}")
        
        # Check if global knowledge base is initialized
        if not global_kb_service.global_knowledge_base["initialized"]:
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Get or create session (for tracking purposes only)
        session_id = await session_service.get_or_create_session(session_id, api_key)
        
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
            
            # Add document to global knowledge base
            success = await global_kb_service.add_document_to_global_kb(
                processed_docs=processed_docs,
                filename=file.filename,
                api_key=api_key
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to add document to global knowledge base")
            
            print(f"✅ Successfully added {file.filename} to global knowledge base")
            
            return UploadResponse(
                success=True,
                message=f"Successfully uploaded {file.filename} to global knowledge base (available to all users)",
                session_id=session_id,
                document_count=len(global_kb_service.global_knowledge_base["user_uploaded_documents"]),
                filename=file.filename
            )
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in upload_document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.post("/upload-multi-document", response_model=MultiDocumentUploadResponse)
async def upload_multi_format_document(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    api_key: str = Form(...)
):
    """Upload a multi-format document to the global knowledge base with enhanced processing"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        print(f"📁 Starting multi-format document upload to global knowledge base: {file.filename}")
        
        # Check if global knowledge base is initialized
        if not global_kb_service.global_knowledge_base["initialized"]:
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Get or create session (for tracking purposes only)
        session_id = await session_service.get_or_create_session(session_id, api_key)
        
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
            
            # Add document to global knowledge base
            success = await global_kb_service.add_document_to_global_kb(
                processed_docs=processed_docs,
                filename=file.filename,
                api_key=api_key
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to add document to global knowledge base")
            
            print(f"✅ Successfully added {file.filename} to global knowledge base")
            
            return MultiDocumentUploadResponse(
                success=True,
                message=f"Successfully uploaded {file.filename} ({doc_type}) to global knowledge base (available to all users)",
                session_id=session_id,
                document_count=len(global_kb_service.global_knowledge_base["user_uploaded_documents"]),
                filename=file.filename,
                doc_type=doc_type,
                regulatory_type=regulatory_type,
                chunks_created=len(processed_docs)
            )
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in upload_multi_format_document: {e}")
        import traceback
        traceback.print_exc()
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

@router.delete("/documents/{filename}")
async def delete_document(filename: str, api_key: str):
    """Delete a user-uploaded document from the global knowledge base"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        print(f"🗑️ Delete request for document: {filename}")
        
        # Check if global knowledge base is initialized
        if not global_kb_service.global_knowledge_base["initialized"]:
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized")
        
        # Attempt to remove the document
        success = await global_kb_service.remove_document_from_global_kb(filename, api_key)
        
        if success:
            print(f"✅ Successfully deleted {filename} from global knowledge base")
            return {
                "success": True,
                "message": f"Successfully deleted {filename} from global knowledge base",
                "remaining_user_documents": global_kb_service.global_knowledge_base["user_uploaded_documents"],
                "total_documents": len(global_kb_service.global_knowledge_base["documents"]) + len(global_kb_service.global_knowledge_base["user_uploaded_documents"])
            }
        else:
            raise HTTPException(status_code=400, detail=f"Could not delete {filename}. Either it doesn't exist, is not a user-uploaded document, or an error occurred.")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in delete_document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}") 