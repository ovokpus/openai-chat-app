# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import os
import tempfile
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import sys
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the project root to the Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import aimakerspace components
from aimakerspace.file_utils import UniversalFileProcessor
from aimakerspace.text_utils import CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.rag_pipeline import RAGPipeline
from aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt

# Import routers
from routers.chat import router as chat_router
from routers.rag import router as rag_router
from routers.documents import router as documents_router
from routers.sessions import router as sessions_router
from routers.health import router as health_router

# Initialize FastAPI application with a title
app = FastAPI(title="OpenAI Chat API with RAG")

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the API to be accessed from different domains/origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# Global storage for user sessions and their documents
# In production, this should be replaced with a proper database
user_sessions: Dict[str, Dict[str, Any]] = {}

# Define the data model for chat requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    developer_message: str  # Message from the developer/system
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

# Define the data model for RAG chat requests
class RAGChatRequest(BaseModel):
    user_message: str      # Message from the user
    session_id: str        # Session ID to identify user's documents
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication
    use_rag: bool = True   # Whether to use RAG for this request

# Define response models
class UploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    document_count: int
    filename: str

class SessionInfo(BaseModel):
    session_id: str
    document_count: int
    documents: List[str]
    created_at: str

# New model for document deletion
class DocumentDeletionRequest(BaseModel):
    session_id: str
    document_name: str
    api_key: str

# Helper function to get or create user session
def get_or_create_session(session_id: Optional[str] = None, api_key: Optional[str] = None) -> str:
    if session_id and session_id in user_sessions:
        session = user_sessions[session_id]
        # Ensure the vector database has a properly initialized embedding model
        if api_key and (not hasattr(session["vector_db"], "embedding_model") or 
                       not hasattr(session["vector_db"].embedding_model, "openai_api_key") or
                       session["vector_db"].embedding_model.openai_api_key != api_key):
            print(f"🔧 Updating session {session_id} with new API key")
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
    else:
        # Create a vector database without embedding model - will need to be initialized later
        vector_db = VectorDatabase()
    
    user_sessions[new_session_id] = {
        "vector_db": vector_db,
        "documents": [],
        "created_at": datetime.now().isoformat(),
        "rag_pipeline": None,
        "api_key": api_key  # Store the API key in session
    }
    return new_session_id

# Original chat endpoint (unchanged for backward compatibility)
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Initialize OpenAI client with the provided API key
        client = OpenAI(api_key=request.api_key)
        
        # Create an async generator function for streaming responses
        async def generate():
            # Create a streaming chat completion request
            stream = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "developer", "content": request.developer_message},
                    {"role": "user", "content": request.user_message}
                ],
                stream=True  # Enable streaming response
            )
            
            # Yield each chunk of the response as it becomes available
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        # Handle any errors that occur during processing
        raise HTTPException(status_code=500, detail=str(e))

# New document upload endpoint (supports multiple file types)
@app.post("/api/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: str = Form(...)
):
    try:
        print(f"📁 Starting document upload: {file.filename}")
        
        # Validate file type using UniversalFileProcessor
        if not UniversalFileProcessor.validate_file(file.filename, file.content_type):
            supported_types = ", ".join(UniversalFileProcessor.get_supported_extensions())
            print(f"❌ Invalid file type: {file.filename} (content-type: {file.content_type})")
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types: {supported_types}")
        
        print(f"✅ File validation passed")
        
        # Get or create session with API key
        session_id = get_or_create_session(session_id, api_key)
        session = user_sessions[session_id]
        print(f"✅ Session created/retrieved: {session_id}")
        
        # Save uploaded file temporarily with appropriate extension
        file_extension = Path(file.filename).suffix.lower() if file.filename else '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        print(f"✅ File saved temporarily: {tmp_file_path}")
        
        try:
            # Process document using UniversalFileProcessor
            print(f"📄 Loading document...")
            file_processor = UniversalFileProcessor(tmp_file_path)
            documents = file_processor.load_documents()
            
            if not documents:
                print(f"❌ No text extracted from document")
                raise HTTPException(status_code=400, detail="No text could be extracted from the document")
            
            print(f"✅ Extracted {len(documents)} documents")
            
            # Split text into smaller chunks with less overlap for faster processing
            print(f"✂️ Splitting text into chunks...")
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = text_splitter.split_texts(documents)
            
            print(f"✅ Created {len(chunks)} chunks")
            
            # Ensure vector database has proper embedding model
            print(f"🧠 Ensuring vector database has proper embedding model...")
            vector_db = session["vector_db"]
            
            # Make sure the vector database has the embedding model with API key
            if not hasattr(vector_db, "embedding_model") or not vector_db.embedding_model:
                embedding_model = EmbeddingModel(api_key=api_key)
                vector_db.embedding_model = embedding_model
                print(f"✅ Created new embedding model for vector database")
            elif not hasattr(vector_db.embedding_model, "openai_api_key") or not vector_db.embedding_model.openai_api_key:
                embedding_model = EmbeddingModel(api_key=api_key)
                vector_db.embedding_model = embedding_model
                print(f"✅ Updated embedding model with API key")
            else:
                print(f"✅ Vector database already has proper embedding model")
            
            print(f"💾 Processing chunks in parallel...")
            
            # Process chunks in parallel using asyncio
            BATCH_SIZE = 5  # Process 5 chunks at a time
            total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
            
            # Process all batches
            for i in range(0, len(chunks), BATCH_SIZE):
                print(f"🔄 Processing batch {i//BATCH_SIZE + 1}/{total_batches}")
                batch = chunks[i:i + BATCH_SIZE]
                
                # Prepare metadata for the batch
                metadata_list = [{
                    "filename": file.filename,
                    "chunk_index": i + idx,
                    "upload_time": datetime.now().isoformat()
                } for idx in range(len(batch))]
                
                # Process batch in parallel
                await vector_db.ainsert_batch(batch, metadata_list)
                print(f"✅ Batch {i//BATCH_SIZE + 1} processed")
            
            print(f"✅ All chunks processed successfully")
            
            # Update session info
            session["documents"].append(file.filename)
            
            # Initialize RAG pipeline for this session
            print(f"🤖 Initializing RAG pipeline...")
            chat_model = ChatOpenAI(model_name="gpt-4o-mini", api_key=api_key)
            session["rag_pipeline"] = RAGPipeline(
                llm=chat_model,
                vector_db=vector_db,
                response_style="detailed"
            )
            
            print(f"✅ RAG pipeline initialized")
            
            return UploadResponse(
                success=True,
                message=f"Successfully processed {file.filename} into {len(chunks)} chunks",
                session_id=session_id,
                document_count=len(session["documents"]),
                filename=file.filename
            )
            
        finally:
            # Clean up temporary file
            print(f"🧹 Cleaning up temporary file")
            os.unlink(tmp_file_path)
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Unexpected error in upload_document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

# Legacy PDF upload endpoint for backward compatibility
@app.post("/api/upload-pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: str = Form(...)
):
    """Legacy endpoint that redirects to the new document upload endpoint."""
    return await upload_document(file, session_id, api_key)

# New RAG chat endpoint
@app.post("/api/rag-chat")
async def rag_chat(request: RAGChatRequest):
    try:
        print(f"🔍 RAG chat request received:")
        print(f"  - Session ID: {request.session_id}")
        print(f"  - User message: {request.user_message}")
        print(f"  - Available sessions: {list(user_sessions.keys())}")
        
        # Check if session exists
        if request.session_id not in user_sessions:
            print(f"❌ Session {request.session_id} not found in {list(user_sessions.keys())}")
            raise HTTPException(status_code=404, detail="Session not found. Please upload a PDF first.")
        
        session = user_sessions[request.session_id]
        print(f"✅ Found session with {len(session['documents'])} documents")
        
        # Check if session has documents
        if not session["documents"]:
            print(f"❌ No documents in session")
            raise HTTPException(status_code=400, detail="No documents found in session. Please upload a PDF first.")
        
        # API key is already passed directly to models during initialization
        
        # Get RAG pipeline from session
        rag_pipeline = session["rag_pipeline"]
        
        if not rag_pipeline:
            print(f"❌ RAG pipeline not initialized")
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        
        # Ensure the vector database has a proper embedding model
        vector_db = session["vector_db"]
        if not hasattr(vector_db, "embedding_model") or not vector_db.embedding_model:
            print(f"🔧 Initializing embedding model for RAG search...")
            embedding_model = EmbeddingModel(api_key=request.api_key)
            vector_db.embedding_model = embedding_model
        elif not hasattr(vector_db.embedding_model, "openai_api_key") or not vector_db.embedding_model.openai_api_key:
            print(f"🔧 Updating embedding model with API key for RAG search...")
            embedding_model = EmbeddingModel(api_key=request.api_key)
            vector_db.embedding_model = embedding_model
        
        print(f"✅ RAG pipeline ready")
        
        # Create streaming response
        async def generate():
            try:
                # Run RAG pipeline to get context and generate response
                if request.use_rag:
                    print(f"🔎 Searching documents for: {request.user_message}")
                    # Search for relevant documents
                    search_results = rag_pipeline.search_documents(
                        query=request.user_message,
                        k=4,
                        return_metadata=True
                    )
                    
                    print(f"📋 Found {len(search_results)} search results")
                    
                    if search_results:
                        # Format context from search results
                        context, metadata_info = rag_pipeline.format_context(search_results)
                        
                        print(f"📝 Generated context length: {len(context)} characters")
                        print(f"🔗 Metadata: {metadata_info}")
                        
                        # Generate response using RAG
                        response = rag_pipeline.generate_response(
                            query=request.user_message,
                            context=context,
                            metadata_info=metadata_info
                        )
                        
                        print(f"💬 Generated response length: {len(response)} characters")
                        
                        # Stream the response
                        yield response
                    else:
                        print(f"❌ No relevant search results found")
                        yield "I couldn't find relevant information in the uploaded documents to answer your question."
                else:
                    # Fallback to regular chat without RAG
                    client = OpenAI(api_key=request.api_key)
                    stream = client.chat.completions.create(
                        model=request.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": request.user_message}
                        ],
                        stream=True
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            yield chunk.choices[0].delta.content
                            
            except Exception as e:
                print(f"❌ Error in generate function: {e}")
                import traceback
                traceback.print_exc()
                yield f"Error generating response: {str(e)}"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        print(f"❌ Error in rag_chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Session management endpoints
@app.get("/api/sessions")
async def list_sessions():
    """Debug endpoint to list all active sessions"""
    sessions_info = []
    for session_id, session_data in user_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "document_count": len(session_data["documents"]),
            "documents": session_data["documents"],
            "created_at": session_data["created_at"]
        })
    return {
        "total_sessions": len(user_sessions),
        "sessions": sessions_info
    }

@app.get("/api/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = user_sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        document_count=len(session["documents"]),
        documents=session["documents"],
        created_at=session["created_at"]
    )

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del user_sessions[session_id]
    return {"success": True, "message": "Session deleted successfully"}

@app.delete("/api/documents/{session_id}/{document_name}")
async def delete_document(session_id: str, document_name: str, api_key: str):
    """Delete a specific document from a session"""
    try:
        if session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = user_sessions[session_id]
        
        if document_name not in session["documents"]:
            raise HTTPException(status_code=404, detail="Document not found in session")
            
        # Remove document from session
        session["documents"].remove(document_name)
        session["document_count"] = len(session["documents"])
        
        # If no documents left, clear the session
        if session["document_count"] == 0:
            del user_sessions[session_id]
            return {"success": True, "message": "Document deleted and session cleared"}
            
        # Reinitialize RAG pipeline with remaining documents
        chat_model = ChatOpenAI(model_name="gpt-4o-mini", api_key=api_key)
        session["rag_pipeline"] = RAGPipeline(
            llm=chat_model,
            vector_db=session["vector_db"],
            response_style="detailed"
        )
        
        return {
            "success": True,
            "message": f"Document {document_name} deleted",
            "remaining_documents": session["documents"],
            "document_count": session["document_count"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(documents_router)
app.include_router(sessions_router)
app.include_router(health_router)

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)