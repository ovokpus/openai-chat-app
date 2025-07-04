# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
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
import sys
import numpy as np

# Add the project root to the Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import aimakerspace components
from aimakerspace.pdf_utils import PDFFileLoader
from aimakerspace.text_utils import CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.rag_pipeline import RAGPipeline
from aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt

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

# New PDF upload endpoint
@app.post("/api/upload-pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: str = Form(...)
):
    try:
        print(f"📁 Starting PDF upload: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            print(f"❌ Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        print(f"✅ File validation passed")
        
        # Get or create session with API key
        session_id = get_or_create_session(session_id, api_key)
        session = user_sessions[session_id]
        print(f"✅ Session created/retrieved: {session_id}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        print(f"✅ File saved temporarily: {tmp_file_path}")
        
        try:
            # Process PDF using aimakerspace
            print(f"📄 Loading PDF documents...")
            pdf_loader = PDFFileLoader(tmp_file_path)
            documents = pdf_loader.load_documents()
            
            if not documents:
                print(f"❌ No text extracted from PDF")
                raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
            
            print(f"✅ Extracted {len(documents)} documents")
            
            # Split text into chunks
            print(f"✂️ Splitting text into chunks...")
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
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
            
            print(f"💾 Processing chunks and storing embeddings...")
            # Process chunks and add to vector database
            for i, chunk in enumerate(chunks):
                print(f"🔄 Processing chunk {i+1}/{len(chunks)}")
                try:
                    embedding = vector_db.embedding_model.get_embedding(chunk)
                    metadata = {
                        "filename": file.filename,
                        "chunk_index": i,
                        "upload_time": datetime.now().isoformat()
                    }
                    vector_db.insert(chunk, np.array(embedding), metadata)
                    print(f"✅ Chunk {i+1} processed and stored")
                except Exception as chunk_error:
                    print(f"❌ Error processing chunk {i+1}: {chunk_error}")
                    raise chunk_error
            
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
        print(f"❌ Unexpected error in upload_pdf: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

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

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "features": ["chat", "pdf_upload", "rag_chat", "session_management"],
        "active_sessions": len(user_sessions)
    }

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)