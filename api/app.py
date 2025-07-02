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
def get_or_create_session(session_id: Optional[str] = None) -> str:
    if session_id and session_id in user_sessions:
        return session_id
    
    new_session_id = str(uuid.uuid4())
    user_sessions[new_session_id] = {
        "vector_db": VectorDatabase(),
        "documents": [],
        "created_at": datetime.now().isoformat(),
        "rag_pipeline": None
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
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Get or create session
        session_id = get_or_create_session(session_id)
        session = user_sessions[session_id]
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process PDF using aimakerspace
            pdf_loader = PDFFileLoader(tmp_file_path)
            documents = pdf_loader.load_documents()
            
            if not documents:
                raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
            
            # Split text into chunks
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_texts(documents)
            
            # Generate embeddings and store in vector database
            # Set environment variable for the session
            os.environ["OPENAI_API_KEY"] = api_key
            embedding_model = EmbeddingModel()
            
            # Process chunks and add to vector database
            vector_db = session["vector_db"]
            
            for i, chunk in enumerate(chunks):
                embedding = embedding_model.get_embedding(chunk)
                metadata = {
                    "filename": file.filename,
                    "chunk_index": i,
                    "upload_time": datetime.now().isoformat()
                }
                vector_db.insert(chunk, embedding, metadata)
            
            # Update session info
            session["documents"].append(file.filename)
            
            # Initialize RAG pipeline for this session
            chat_model = ChatOpenAI(model_name="gpt-4o-mini")
            session["rag_pipeline"] = RAGPipeline(
                llm=chat_model,
                vector_db=vector_db,
                response_style="detailed"
            )
            
            return UploadResponse(
                success=True,
                message=f"Successfully processed {file.filename} into {len(chunks)} chunks",
                session_id=session_id,
                document_count=len(session["documents"]),
                filename=file.filename
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# New RAG chat endpoint
@app.post("/api/rag-chat")
async def rag_chat(request: RAGChatRequest):
    try:
        # Check if session exists
        if request.session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found. Please upload a PDF first.")
        
        session = user_sessions[request.session_id]
        
        # Check if session has documents
        if not session["documents"]:
            raise HTTPException(status_code=400, detail="No documents found in session. Please upload a PDF first.")
        
        # Set environment variable for OpenAI API
        os.environ["OPENAI_API_KEY"] = request.api_key
        
        # Get RAG pipeline from session
        rag_pipeline = session["rag_pipeline"]
        
        if not rag_pipeline:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        
        # Create streaming response
        async def generate():
            try:
                # Run RAG pipeline to get context and generate response
                if request.use_rag:
                    # Search for relevant documents
                    search_results = rag_pipeline.search_documents(
                        query=request.user_message,
                        k=4,
                        return_metadata=True
                    )
                    
                    if search_results:
                        # Format context from search results
                        context, metadata_info = rag_pipeline.format_context(search_results)
                        
                        # Generate response using RAG
                        response = rag_pipeline.generate_response(
                            query=request.user_message,
                            context=context,
                            metadata_info=metadata_info
                        )
                        
                        # Stream the response
                        yield response
                    else:
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
                yield f"Error generating response: {str(e)}"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Session management endpoints
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