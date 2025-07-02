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

# Import new regulatory document processing capabilities
from aimakerspace.multi_document_processor import MultiDocumentProcessor
from aimakerspace.regulatory_rag_enhancer import RegulatoryRAGEnhancer

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

# Global knowledge base storage for pre-loaded regulatory documents
global_knowledge_base: Dict[str, Any] = {
    "vector_db": None,
    "documents": [],
    "rag_pipeline": None,
    "regulatory_enhancer": None,
    "initialized": False,
    "error": None
}

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

# New data models for enhanced regulatory functionality
class RegulatoryRAGRequest(BaseModel):
    user_message: str      # Message from the user
    session_id: str        # Session ID to identify user's documents
    user_role: Optional[str] = "general"  # User role (analyst, data_engineer, programme_manager, general)
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication
    use_rag: bool = True   # Whether to use RAG for this request
    doc_types: Optional[List[str]] = None  # Filter by document types
    priority_sources: Optional[List[str]] = None  # Prioritize specific sources

class MultiDocumentUploadResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    document_count: int
    filename: str
    doc_type: str
    regulatory_type: str
    chunks_created: int

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
            
            # Initialize with global knowledge base if available
            global_kb = get_global_knowledge_base(api_key)
            if global_kb:
                print(f"📚 Merging global knowledge base into session {session_id}")
                session["global_kb"] = global_kb
                session["has_global_kb"] = True
        return session_id
    
    new_session_id = str(uuid.uuid4())
    
    # Always create VectorDatabase with embedding model that has API key
    if api_key:
        embedding_model = EmbeddingModel(api_key=api_key)
        vector_db = VectorDatabase(embedding_model=embedding_model)
        
        # Try to initialize with global knowledge base
        global_kb = get_global_knowledge_base(api_key)
        has_global_kb = global_kb is not None
        
        user_sessions[new_session_id] = {
            "vector_db": vector_db,
            "documents": [],
            "created_at": datetime.now().isoformat(),
            "rag_pipeline": None,
            "api_key": api_key,  # Store the API key in session
            "global_kb": global_kb,
            "has_global_kb": has_global_kb
        }
        
        if has_global_kb:
            print(f"📚 New session {new_session_id} initialized with global knowledge base ({global_kb['chunk_count']} chunks)")
    else:
        # Create a vector database without embedding model - will need to be initialized later
        vector_db = VectorDatabase()
        user_sessions[new_session_id] = {
            "vector_db": vector_db,
            "documents": [],
            "created_at": datetime.now().isoformat(),
            "rag_pipeline": None,
            "api_key": api_key,
            "global_kb": None,
            "has_global_kb": False
        }
    
    return new_session_id

# Startup function to load all documents from the documents folder
async def initialize_global_knowledge_base():
    """
    Initialize the global knowledge base with all documents from the documents folder.
    This runs at startup to pre-load regulatory documents for immediate use.
    """
    global global_knowledge_base
    
    if global_knowledge_base["initialized"]:
        print("📚 Global knowledge base already initialized")
        return
    
    try:
        print("🚀 Initializing global knowledge base with regulatory documents...")
        
        # Path to documents folder
        documents_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents")
        
        if not os.path.exists(documents_path):
            print(f"📂 Documents folder not found at {documents_path}")
            global_knowledge_base["initialized"] = True
            global_knowledge_base["error"] = "Documents folder not found"
            return
        
        # Get list of supported files
        supported_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.pptx', '.ppt', '.csv', '.sql', '.py', '.js', '.ts', '.md', '.txt']
        document_files = []
        
        for filename in os.listdir(documents_path):
            file_path = os.path.join(documents_path, filename)
            if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in supported_extensions):
                document_files.append(file_path)
        
        if not document_files:
            print("📄 No supported documents found in documents folder")
            global_knowledge_base["initialized"] = True
            global_knowledge_base["error"] = "No supported documents found"
            return
        
        print(f"📋 Found {len(document_files)} documents to process:")
        for file_path in document_files:
            print(f"  - {os.path.basename(file_path)}")
        
        # Don't create embedding model during startup - will be created when user provides API key
        # This allows us to process documents without requiring an API key at startup
        global_vector_db = None
        
        # Initialize document processor
        multi_doc_processor = MultiDocumentProcessor()
        
        # Process each document
        all_documents = []
        processed_files = []
        
        for file_path in document_files:
            try:
                filename = os.path.basename(file_path)
                print(f"📄 Processing {filename}...")
                
                # Determine document type
                file_extension = os.path.splitext(filename)[1].lower()
                
                # Process document based on type
                if file_extension == '.pdf':
                    # Use PDF loader
                    pdf_loader = PDFFileLoader(file_path)
                    pdf_content = pdf_loader.load_documents()
                    # Convert PDF content to document objects with metadata
                    documents = []
                    for page_num, content in enumerate(pdf_content):
                        if content.strip():
                            # Create a simple document object with content and metadata
                            simple_doc = type('Document', (), {})()
                            simple_doc.page_content = content
                            simple_doc.metadata = {
                                'source_file': filename,
                                'page_number': page_num + 1,
                                'doc_type': 'pdf',
                                'total_pages': len(pdf_content)
                            }
                            documents.append(simple_doc)
                elif file_extension in ['.xlsx', '.xls', '.docx', '.pptx', '.ppt', '.csv', '.sql', '.py', '.js', '.ts', '.md', '.txt']:
                    # Use multi-document processor
                    processed_docs = multi_doc_processor.process_document(file_path, filename)
                    # Convert ProcessedDocument objects to simple format expected by RAG pipeline
                    documents = []
                    for doc in processed_docs:
                        # Create a simple document object with content and metadata
                        simple_doc = type('Document', (), {})()
                        simple_doc.page_content = doc.content
                        simple_doc.metadata = doc.metadata
                        documents.append(simple_doc)
                else:
                    print(f"⚠️ Unsupported file type: {filename}")
                    continue
                
                if documents:
                    # Add source information to documents
                    for doc in documents:
                        if not hasattr(doc, 'metadata'):
                            doc.metadata = {}
                        doc.metadata['source_file'] = filename
                        doc.metadata['source_type'] = 'global_knowledge_base'
                        doc.metadata['file_extension'] = file_extension
                    
                    all_documents.extend(documents)
                    processed_files.append(filename)
                    print(f"✅ {filename}: {len(documents)} chunks created")
                else:
                    print(f"⚠️ No content extracted from {filename}")
                    
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                continue
        
        if not all_documents:
            print("❌ No documents were successfully processed")
            global_knowledge_base["initialized"] = True
            global_knowledge_base["error"] = "No documents were successfully processed"
            return
        
        # Split documents into chunks
        print(f"✂️ Splitting documents into chunks...")
        text_splitter = CharacterTextSplitter()
        
        # Extract text content from document objects and split
        text_chunks = []
        for doc in all_documents:
            chunks = text_splitter.split(doc.page_content)
            for chunk in chunks:
                if chunk.strip():
                    # Create new document object for each chunk
                    chunk_doc = type('Document', (), {})()
                    chunk_doc.page_content = chunk
                    chunk_doc.metadata = doc.metadata.copy()  # Copy metadata
                    text_chunks.append(chunk_doc)
        
        print(f"✅ Created {len(text_chunks)} text chunks")
        
        # Store in global knowledge base (without embeddings initially)
        global_knowledge_base["vector_db"] = None  # Will be created when user provides API key
        global_knowledge_base["documents"] = processed_files
        global_knowledge_base["chunked_documents"] = text_chunks
        global_knowledge_base["initialized"] = True
        
        print(f"🎉 Global knowledge base initialized successfully!")
        print(f"📊 Summary:")
        print(f"  - Files processed: {len(processed_files)}")
        print(f"  - Total chunks: {len(text_chunks)}")
        print(f"  - Files: {', '.join(processed_files)}")
        
    except Exception as e:
        print(f"❌ Error initializing global knowledge base: {e}")
        import traceback
        traceback.print_exc()
        global_knowledge_base["initialized"] = True
        global_knowledge_base["error"] = str(e)

# Function to get global knowledge base with user's API key
def get_global_knowledge_base(api_key: str):
    """
    Get the global knowledge base initialized with the user's API key for embeddings.
    """
    global global_knowledge_base
    
    if not global_knowledge_base["initialized"]:
        return None
    
    if global_knowledge_base["error"]:
        return None
    
    try:
        # Create vector database with user's API key
        embedding_model = EmbeddingModel(api_key=api_key)
        vector_db = VectorDatabase(embedding_model=embedding_model)
        
        # Add documents to vector database 
        chunked_documents = global_knowledge_base.get("chunked_documents", [])
        if chunked_documents:
            print(f"🔧 Initializing vector database with {len(chunked_documents)} chunks for user session...")
            vector_db.add_documents(chunked_documents)
            
            # Create RAG pipeline
            chat_model = ChatOpenAI(api_key=api_key)
            rag_pipeline = RAGPipeline(vector_db=vector_db, llm=chat_model)
            
            # Create regulatory enhancer
            regulatory_enhancer = RegulatoryRAGEnhancer(rag_pipeline)
            
            return {
                "vector_db": vector_db,
                "rag_pipeline": rag_pipeline,
                "regulatory_enhancer": regulatory_enhancer,
                "documents": global_knowledge_base["documents"],
                "chunk_count": len(chunked_documents)
            }
        else:
            print(f"⚠️ No chunked documents found in global knowledge base")
            return None
    
    except Exception as e:
        print(f"❌ Error creating user-specific global knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return None

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

# New multi-document upload endpoint for regulatory documents
@app.post("/api/upload-document", response_model=MultiDocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: str = Form(...)
):
    """
    Enhanced document upload endpoint that supports multiple file types
    for regulatory reporting while maintaining PDF compatibility.
    """
    try:
        print(f"📁 Starting multi-document upload: {file.filename}")
        
        # Initialize multi-document processor
        processor = MultiDocumentProcessor()
        
        # Validate file type
        if not processor.is_supported(file.filename):
            supported_exts = ", ".join(processor.get_supported_extensions())
            print(f"❌ Unsupported file type: {file.filename}")
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Supported types: {supported_exts}"
            )
        
        print(f"✅ File validation passed")
        
        # Get or create session with API key
        session_id = get_or_create_session(session_id, api_key)
        session = user_sessions[session_id]
        print(f"✅ Session created/retrieved: {session_id}")
        
        # Save uploaded file temporarily with appropriate extension
        file_ext = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        print(f"✅ File saved temporarily: {tmp_file_path}")
        
        try:
            # Process document using multi-document processor
            print(f"📄 Processing document with multi-document processor...")
            processed_docs = processor.process_document(tmp_file_path, file.filename)
            
            if not processed_docs:
                print(f"❌ No content extracted from document")
                raise HTTPException(status_code=400, detail="No content could be extracted from the document")
            
            print(f"✅ Extracted {len(processed_docs)} processed chunks")
            
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
            
            print(f"💾 Processing chunks and storing embeddings...")
            
            # Process chunks and add to vector database
            chunks_created = 0
            doc_type = ""
            regulatory_type = ""
            
            for i, processed_doc in enumerate(processed_docs):
                print(f"🔄 Processing chunk {i+1}/{len(processed_docs)}")
                try:
                    # Get embedding for the content
                    embedding = vector_db.embedding_model.get_embedding(processed_doc.content)
                    
                    # Enhanced metadata with regulatory context
                    enhanced_metadata = processed_doc.metadata.copy()
                    enhanced_metadata.update({
                        "upload_time": datetime.now().isoformat(),
                        "source_location": processed_doc.source_location,
                        "processed_doc_type": processed_doc.doc_type
                    })
                    
                    # Store in vector database
                    vector_db.insert(processed_doc.content, np.array(embedding), enhanced_metadata)
                    chunks_created += 1
                    
                    # Track document type and regulatory type for response
                    if i == 0:  # Use first chunk's metadata
                        doc_type = processed_doc.doc_type
                        regulatory_type = processed_doc.metadata.get("regulatory_type", "")
                    
                    print(f"✅ Chunk {i+1} processed and stored")
                except Exception as chunk_error:
                    print(f"❌ Error processing chunk {i+1}: {chunk_error}")
                    raise chunk_error
            
            print(f"✅ All {chunks_created} chunks processed successfully")
            
            # Update session info
            session["documents"].append(file.filename)
            
            # Initialize or update RAG pipeline for this session
            print(f"🤖 Initializing enhanced RAG pipeline...")
            chat_model = ChatOpenAI(model_name="gpt-4o-mini", api_key=api_key)
            base_rag_pipeline = RAGPipeline(
                llm=chat_model,
                vector_db=vector_db,
                response_style="detailed"
            )
            
            # Create regulatory enhancer
            regulatory_enhancer = RegulatoryRAGEnhancer(base_rag_pipeline)
            
            # Store both in session for flexibility
            session["rag_pipeline"] = base_rag_pipeline
            session["regulatory_enhancer"] = regulatory_enhancer
            
            print(f"✅ Enhanced RAG pipeline initialized")
            
            return MultiDocumentUploadResponse(
                success=True,
                message=f"Successfully processed {file.filename} ({doc_type}) into {chunks_created} chunks",
                session_id=session_id,
                document_count=len(session["documents"]),
                filename=file.filename,
                doc_type=doc_type,
                regulatory_type=regulatory_type,
                chunks_created=chunks_created
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

# New RAG chat endpoint
@app.post("/api/rag-chat")
async def rag_chat(request: RAGChatRequest):
    try:
        print(f"🔍 RAG chat request received:")
        print(f"  - Session ID: {request.session_id}")
        print(f"  - User message: {request.user_message}")
        print(f"  - Available sessions: {list(user_sessions.keys())}")
        
        # Check if session exists, if not create one with global knowledge base access
        if request.session_id not in user_sessions:
            print(f"🔧 Session {request.session_id} not found, checking for global knowledge base...")
            
            # Try to create session with global knowledge base if available
            if global_knowledge_base.get("initialized", False):
                print(f"🌍 Creating new session with global knowledge base access")
                session_id = get_or_create_session(request.session_id, request.api_key)
                # The session is now created and should have global KB access
            else:
                print(f"❌ No session and global knowledge base not initialized")
                raise HTTPException(status_code=404, detail="No active session. Please upload a PDF first or wait for global knowledge base to initialize.")
        
        session = user_sessions[request.session_id]
        user_doc_count = len(session['documents'])
        global_kb = session.get('global_kb')
        global_doc_count = len(global_kb['documents']) if global_kb else 0
        
        print(f"✅ Found session with {user_doc_count} user documents + {global_doc_count} global documents")
        
        # Check if session has documents (user documents OR global knowledge base)
        if not session["documents"] and not session.get("has_global_kb", False):
            print(f"❌ No documents in session and no global knowledge base")
            raise HTTPException(status_code=400, detail="No documents found in session. Please upload a document first or wait for global knowledge base to initialize.")
        
        # Determine which RAG pipeline to use
        rag_pipeline = None
        vector_db = None
        
        # Prioritize global knowledge base if user has no documents
        if session.get("has_global_kb", False) and global_kb and not session["documents"]:
            print(f"🌍 Using global knowledge base for RAG")
            rag_pipeline = global_kb["rag_pipeline"]
            vector_db = global_kb["vector_db"]
        elif session["rag_pipeline"]:
            print(f"👤 Using user session RAG pipeline")
            rag_pipeline = session["rag_pipeline"]
            vector_db = session["vector_db"]
        elif global_kb:
            print(f"🌍 Falling back to global knowledge base")
            rag_pipeline = global_kb["rag_pipeline"]
            vector_db = global_kb["vector_db"]
        
        if not rag_pipeline:
            print(f"❌ No RAG pipeline available")
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        
        # Ensure the vector database has a proper embedding model
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

# Enhanced regulatory RAG chat endpoint
@app.post("/api/regulatory-rag-chat")
async def regulatory_rag_chat(request: RegulatoryRAGRequest):
    """
    Enhanced RAG chat endpoint with regulatory-specific features including
    role-based responses, document type filtering, and enhanced citations.
    """
    try:
        print(f"🏛️ Regulatory RAG chat request received:")
        print(f"  - Session ID: {request.session_id}")
        print(f"  - User message: {request.user_message}")
        print(f"  - User role: {request.user_role}")
        print(f"  - Doc types filter: {request.doc_types}")
        print(f"  - Priority sources: {request.priority_sources}")
        
        # Check if session exists, if not create one with global knowledge base access
        if request.session_id not in user_sessions:
            print(f"🔧 Session {request.session_id} not found, checking for global knowledge base...")
            
            # Try to create session with global knowledge base if available
            if global_knowledge_base.get("initialized", False):
                print(f"🌍 Creating new session with global knowledge base access")
                session_id = get_or_create_session(request.session_id, request.api_key)
                # The session is now created and should have global KB access
            else:
                print(f"❌ No session and global knowledge base not initialized")
                raise HTTPException(status_code=404, detail="No active session. Please upload documents first or wait for global knowledge base to initialize.")
        
        session = user_sessions[request.session_id]
        user_doc_count = len(session['documents'])
        global_kb = session.get('global_kb')
        global_doc_count = len(global_kb['documents']) if global_kb else 0
        
        print(f"✅ Found session with {user_doc_count} user documents + {global_doc_count} global documents")
        
        # Check if session has documents (user documents OR global knowledge base)
        if not session["documents"] and not session.get("has_global_kb", False):
            print(f"❌ No documents in session and no global knowledge base")
            raise HTTPException(status_code=400, detail="No documents found in session. Please upload documents first or wait for global knowledge base to initialize.")
        
        # Determine which RAG pipeline to use
        regulatory_enhancer = None
        base_rag_pipeline = None
        
        # Prioritize global knowledge base if user has no documents
        if session.get("has_global_kb", False) and global_kb and not session["documents"]:
            print(f"🌍 Using global knowledge base for regulatory RAG")
            regulatory_enhancer = global_kb.get("regulatory_enhancer")
            base_rag_pipeline = global_kb.get("rag_pipeline")
        elif session.get("regulatory_enhancer"):
            print(f"👤 Using user session regulatory enhancer")
            regulatory_enhancer = session.get("regulatory_enhancer")
            base_rag_pipeline = session.get("rag_pipeline")
        elif global_kb:
            print(f"🌍 Falling back to global knowledge base for regulatory RAG")
            regulatory_enhancer = global_kb.get("regulatory_enhancer")
            base_rag_pipeline = global_kb.get("rag_pipeline")
        
        if not regulatory_enhancer and not base_rag_pipeline:
            print(f"❌ No RAG pipeline available")
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        
        # Create streaming response
        async def generate():
            try:
                if regulatory_enhancer and request.use_rag:
                    print(f"🏛️ Using enhanced regulatory RAG")
                    
                    # Check if this is a regulatory query
                    is_regulatory = regulatory_enhancer.is_regulatory_query(request.user_message)
                    print(f"📊 Regulatory query detected: {is_regulatory}")
                    
                    # Run enhanced RAG pipeline
                    rag_result = regulatory_enhancer.run_enhanced_rag(
                        query=request.user_message,
                        user_role=request.user_role,
                        k=4,
                        doc_types=request.doc_types,
                        priority_sources=request.priority_sources
                    )
                    
                    print(f"📋 Enhanced RAG result keys: {list(rag_result.keys())}")
                    
                    response = rag_result.get("response", "")
                    sources = rag_result.get("sources", [])
                    
                    # Stream the response
                    yield response
                    
                    # Optionally append source information
                    if sources:
                        yield "\n\n---\n**Sources:**\n"
                        for i, source in enumerate(sources[:3], 1):  # Limit to top 3 sources
                            yield f"{i}. {source.get('source_location', 'Unknown')}\n"
                    
                elif base_rag_pipeline and request.use_rag:
                    print(f"🔍 Falling back to base RAG pipeline")
                    
                    # Use base RAG pipeline functionality
                    search_results = base_rag_pipeline.search_documents(
                        query=request.user_message,
                        k=4,
                        return_metadata=True
                    )
                    
                    if search_results:
                        context, metadata_info = base_rag_pipeline.format_context(search_results)
                        response = base_rag_pipeline.generate_response(
                            query=request.user_message,
                            context=context,
                            metadata_info=metadata_info
                        )
                        yield response
                    else:
                        yield "I couldn't find relevant information in the uploaded documents to answer your question."
                
                else:
                    # Fallback to regular chat without RAG
                    print(f"💬 Falling back to regular chat")
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
                print(f"❌ Error in regulatory generate function: {e}")
                import traceback
                traceback.print_exc()
                yield f"Error generating regulatory response: {str(e)}"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        print(f"❌ Error in regulatory_rag_chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Session management endpoints
@app.get("/api/sessions")
async def list_sessions():
    """Debug endpoint to list all active sessions"""
    global global_knowledge_base
    
    sessions_info = []
    for session_id, session_data in user_sessions.items():
        global_kb = session_data.get('global_kb')
        sessions_info.append({
            "session_id": session_id,
            "document_count": len(session_data["documents"]),
            "documents": session_data["documents"],
            "created_at": session_data["created_at"],
            "has_global_kb": session_data.get("has_global_kb", False),
            "global_kb_document_count": len(global_kb["documents"]) if global_kb else 0,
            "total_available_documents": len(session_data["documents"]) + (len(global_kb["documents"]) if global_kb else 0)
        })
    
    return {
        "total_sessions": len(user_sessions),
        "sessions": sessions_info,
        "global_knowledge_base": {
            "status": "ready" if global_knowledge_base["initialized"] and not global_knowledge_base["error"] else "not_ready",
            "document_count": len(global_knowledge_base["documents"]) if global_knowledge_base["initialized"] else 0,
            "available_to_all_sessions": True
        }
    }

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = user_sessions[session_id]
    global_kb = session.get('global_kb')
    
    return {
        "session_id": session_id,
        "document_count": len(session["documents"]),
        "documents": session["documents"],
        "created_at": session["created_at"],
        "has_global_kb": session.get("has_global_kb", False),
        "global_kb_documents": global_kb["documents"] if global_kb else [],
        "global_kb_document_count": len(global_kb["documents"]) if global_kb else 0,
        "total_available_documents": len(session["documents"]) + (len(global_kb["documents"]) if global_kb else 0)
    }

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del user_sessions[session_id]
    return {"success": True, "message": "Session deleted successfully"}

# Health check endpoint
@app.get("/api/health")
async def health_check():
    global global_knowledge_base
    
    # Get global knowledge base status
    global_kb_status = "not_initialized"
    global_kb_docs = 0
    global_kb_chunks = 0
    
    if global_knowledge_base["initialized"]:
        if global_knowledge_base["error"]:
            global_kb_status = "error"
        else:
            global_kb_status = "ready"
            global_kb_docs = len(global_knowledge_base["documents"])
            global_kb_chunks = len(global_knowledge_base.get("chunked_documents", []))
    
    return {
        "status": "ok",
        "features": [
            "chat", 
            "pdf_upload", 
            "upload_document",  # New multi-document upload
            "rag_chat", 
            "regulatory_rag_chat",  # New regulatory RAG
            "session_management",
            "global_knowledge_base"  # New global knowledge base
        ],
        "supported_document_types": [
            ".pdf", ".xlsx", ".xls", ".docx", ".pptx", ".ppt", 
            ".csv", ".sql", ".py", 
            ".js", ".ts", ".md", ".txt"
        ],
        "regulatory_features": [
            "role_based_responses",
            "document_type_filtering", 
            "enhanced_citations",
            "regulatory_domain_expertise",
            "pre_loaded_regulatory_documents"  # New feature
        ],
        "active_sessions": len(user_sessions),
        "global_knowledge_base": {
            "status": global_kb_status,
            "document_count": global_kb_docs,
            "chunk_count": global_kb_chunks,
            "available_immediately": global_kb_status == "ready"
        }
    }

# Add new endpoints for global knowledge base
@app.get("/api/global-knowledge-base")
async def get_global_knowledge_base_info():
    """Get information about the pre-loaded global knowledge base"""
    global global_knowledge_base
    
    if not global_knowledge_base["initialized"]:
        return {
            "status": "not_initialized",
            "initialized": False,
            "error": "Global knowledge base not initialized"
        }
    
    if global_knowledge_base["error"]:
        return {
            "status": "error",
            "initialized": True,
            "error": global_knowledge_base["error"],
            "documents": []
        }
    
    return {
        "status": "ready",
        "initialized": True,
        "error": None,
        "documents": global_knowledge_base["documents"],
        "document_count": len(global_knowledge_base["documents"]),
        "chunk_count": len(global_knowledge_base.get("chunked_documents", [])),
        "description": "Pre-loaded regulatory documents including Basel III, COREP, FINREP templates, and data lineage examples"
    }

# Startup event to initialize global knowledge base
@app.on_event("startup")
async def startup_event():
    """Initialize the global knowledge base on application startup"""
    print("🚀 Application starting up...")
    await initialize_global_knowledge_base()
    print("✅ Application startup complete")

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)