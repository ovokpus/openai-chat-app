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
    "user_uploaded_documents": [],  # Track user-uploaded documents separately
    "rag_pipeline": None,
    "regulatory_enhancer": None,
    "initialized": False,
    "error": None,
    "chunked_documents": [],  # Keep chunked documents for re-initialization
    "embedding_model": None,  # Store embedding model for adding new documents
    "chat_model": None  # Store chat model for re-creating pipelines
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
async def get_or_create_session(session_id: Optional[str] = None, api_key: Optional[str] = None) -> str:
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
            global_kb = await get_global_knowledge_base(api_key)
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
        global_kb = await get_global_knowledge_base(api_key)
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
                                'total_pages': len(pdf_content),
                                'source': 'original',
                                'is_original': True  # Mark as original document
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
                        simple_doc.metadata = doc.metadata.copy()
                        # Mark as original document
                        simple_doc.metadata.update({
                            'source': 'original',
                            'is_original': True
                        })
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
async def get_global_knowledge_base(api_key: str):
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
            
            # Extract all text content for batch embedding generation
            texts = [doc.page_content for doc in chunked_documents]
            
            # Define async helper function for embedding generation
            async def generate_and_insert_embeddings():
                print(f"🚀 Generating embeddings for {len(texts)} chunks using async batch processing...")
                
                # Generate all embeddings in parallel batches
                embeddings = await embedding_model.async_get_embeddings(texts)
                
                print(f"✅ Generated {len(embeddings)} embeddings, inserting into vector database...")
                
                # Insert all documents with their embeddings
                upload_time = datetime.now().isoformat()
                for i, (doc, embedding) in enumerate(zip(chunked_documents, embeddings)):
                    try:
                        # Create metadata
                        metadata = doc.metadata.copy() if hasattr(doc, 'metadata') and doc.metadata else {}
                        metadata.update({
                            "chunk_index": i,
                            "source": "global_knowledge_base", 
                            "upload_time": upload_time
                        })
                        
                        # Insert into vector database
                        vector_db.insert(doc.page_content, np.array(embedding), metadata)
                        
                        if (i + 1) % 100 == 0:  # Progress update every 100 insertions
                            print(f"🔄 Inserted {i + 1}/{len(chunked_documents)} chunks...")
                            
                    except Exception as e:
                        print(f"❌ Error inserting chunk {i+1}: {e}")
                        continue
                
                print(f"✅ Successfully added {len(chunked_documents)} chunks to vector database")
                
            try:
                # Use await since we'll make this function async
                await generate_and_insert_embeddings()
                
            except Exception as e:
                print(f"❌ Error during batch embedding generation: {e}")
                raise
            
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

# Helper functions to manage global knowledge base
async def add_document_to_global_kb(chunks: List[str], filename: str, api_key: str, doc_type: str = "pdf", metadata_extra: Dict[str, Any] = None) -> bool:
    """
    Add a new document to the global knowledge base.
    """
    global global_knowledge_base
    
    if not global_knowledge_base["initialized"]:
        print(f"❌ Global knowledge base not initialized")
        return False
    
    try:
        # Ensure we have the necessary models
        if not global_knowledge_base["embedding_model"]:
            global_knowledge_base["embedding_model"] = EmbeddingModel(api_key=api_key)
        
        if not global_knowledge_base["chat_model"]:
            global_knowledge_base["chat_model"] = ChatOpenAI(api_key=api_key)
        
        # Get or create the global vector database with current API key
        global_kb = await get_global_knowledge_base(api_key)
        if not global_kb:
            print(f"❌ Could not get global knowledge base")
            return False
        
        vector_db = global_kb["vector_db"]
        print(f"🌍 Adding {filename} to global knowledge base with {len(chunks)} chunks...")
        
        # Add chunks to global vector database
        chunks_added = 0
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding = vector_db.embedding_model.get_embedding(chunk)
                
                # Create metadata
                metadata = {
                    "filename": filename,
                    "chunk_index": i,
                    "upload_time": datetime.now().isoformat(),
                    "source": "user_uploaded",
                    "doc_type": doc_type,
                    "is_original": False  # Mark as user-uploaded, not original
                }
                
                # Add extra metadata if provided
                if metadata_extra:
                    metadata.update(metadata_extra)
                
                # Insert into global vector database
                vector_db.insert(chunk, np.array(embedding), metadata)
                chunks_added += 1
                
                # Create document object for chunked_documents list
                chunk_doc = type('Document', (), {})()
                chunk_doc.page_content = chunk
                chunk_doc.metadata = metadata
                global_knowledge_base["chunked_documents"].append(chunk_doc)
                
                if (i + 1) % 10 == 0:
                    print(f"🔄 Added chunk {i + 1}/{len(chunks)} to global KB...")
                    
            except Exception as e:
                print(f"⚠️ Error adding chunk {i+1} to global KB: {e}")
                continue
        
        # Update global knowledge base tracking
        if filename not in global_knowledge_base["user_uploaded_documents"]:
            global_knowledge_base["user_uploaded_documents"].append(filename)
        
        # Update the global vector database reference
        global_knowledge_base["vector_db"] = vector_db
        
        # Recreate RAG pipeline with updated vector database
        global_knowledge_base["rag_pipeline"] = RAGPipeline(
            llm=global_knowledge_base["chat_model"],
            vector_db=vector_db,
            response_style="detailed"
        )
        
        # Recreate regulatory enhancer
        regulatory_enhancer = RegulatoryRAGEnhancer(global_knowledge_base["rag_pipeline"])
        global_knowledge_base["regulatory_enhancer"] = regulatory_enhancer
        
        print(f"✅ Successfully added {chunks_added} chunks from {filename} to global knowledge base")
        return True
        
    except Exception as e:
        print(f"❌ Error adding document to global knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return False

async def remove_document_from_global_kb(filename: str, api_key: str) -> bool:
    """
    Remove a user-uploaded document from the global knowledge base.
    Original documents cannot be removed.
    """
    global global_knowledge_base
    
    if not global_knowledge_base["initialized"]:
        print(f"❌ Global knowledge base not initialized")
        return False
    
    # Check if this is a user-uploaded document
    if filename not in global_knowledge_base["user_uploaded_documents"]:
        print(f"❌ Cannot remove {filename} - not a user-uploaded document or doesn't exist")
        return False
    
    try:
        print(f"🗑️ Removing {filename} from global knowledge base...")
        
        # Get current global knowledge base
        global_kb = await get_global_knowledge_base(api_key)
        if not global_kb:
            print(f"❌ Could not get global knowledge base")
            return False
        
        vector_db = global_kb["vector_db"]
        
        # Find and remove all chunks for this filename
        chunks_removed = 0
        if hasattr(vector_db, 'vectors') and vector_db.vectors:
            # Create new vectors dict without the chunks from this file
            new_vectors = {}
            new_metadata = {}
            
            for text, vector in vector_db.vectors.items():
                metadata = vector_db.get_metadata(text)
                if metadata and metadata.get("filename") != filename:
                    # Keep this chunk (it's not from the file we're removing)
                    new_vectors[text] = vector
                    new_metadata[text] = metadata
                else:
                    chunks_removed += 1
            
            # Replace the vectors
            vector_db.vectors = new_vectors
            vector_db.metadata = new_metadata
        
        # Remove from chunked_documents list
        global_knowledge_base["chunked_documents"] = [
            doc for doc in global_knowledge_base["chunked_documents"]
            if not (hasattr(doc, 'metadata') and doc.metadata and doc.metadata.get("filename") == filename)
        ]
        
        # Remove from user_uploaded_documents list
        global_knowledge_base["user_uploaded_documents"].remove(filename)
        
        # Update the global vector database reference
        global_knowledge_base["vector_db"] = vector_db
        
        # Recreate RAG pipeline with updated vector database
        if global_knowledge_base["chat_model"]:
            global_knowledge_base["rag_pipeline"] = RAGPipeline(
                llm=global_knowledge_base["chat_model"],
                vector_db=vector_db,
                response_style="detailed"
            )
            
            # Recreate regulatory enhancer
            regulatory_enhancer = RegulatoryRAGEnhancer(global_knowledge_base["rag_pipeline"])
            global_knowledge_base["regulatory_enhancer"] = regulatory_enhancer
        
        print(f"✅ Successfully removed {chunks_removed} chunks from {filename} from global knowledge base")
        return True
        
    except Exception as e:
        print(f"❌ Error removing document from global knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return False

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
        print(f"📁 Starting PDF upload to global knowledge base: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            print(f"❌ Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        print(f"✅ File validation passed")
        
        # Check if global knowledge base is initialized
        if not global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Get or create session (for tracking purposes only)
        session_id = await get_or_create_session(session_id, api_key)
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
            
            # Add document to global knowledge base
            success = await add_document_to_global_kb(
                chunks=chunks,
                filename=file.filename,
                api_key=api_key,
                doc_type="pdf"
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to add document to global knowledge base")
            
            print(f"✅ Successfully added {file.filename} to global knowledge base")
            
            return UploadResponse(
                success=True,
                message=f"Successfully processed {file.filename} into {len(chunks)} chunks and added to global knowledge base",
                session_id=session_id,
                document_count=len(global_knowledge_base["user_uploaded_documents"]),
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
    for regulatory reporting and adds documents to the global knowledge base.
    """
    try:
        print(f"📁 Starting multi-document upload to global knowledge base: {file.filename}")
        
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
        
        # Check if global knowledge base is initialized
        if not global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Get or create session (for tracking purposes only)
        session_id = await get_or_create_session(session_id, api_key)
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
            
            # Extract text chunks and metadata
            chunks = []
            doc_type = ""
            regulatory_type = ""
            metadata_extra = {}
            
            for i, processed_doc in enumerate(processed_docs):
                chunks.append(processed_doc.content)
                
                # Track document type and regulatory type for response
                if i == 0:  # Use first chunk's metadata
                    doc_type = processed_doc.doc_type
                    regulatory_type = processed_doc.metadata.get("regulatory_type", "")
                    metadata_extra = {
                        "source_location": processed_doc.source_location,
                        "processed_doc_type": processed_doc.doc_type,
                        "regulatory_type": regulatory_type
                    }
            
            # Add document to global knowledge base
            success = await add_document_to_global_kb(
                chunks=chunks,
                filename=file.filename,
                api_key=api_key,
                doc_type=doc_type,
                metadata_extra=metadata_extra
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to add document to global knowledge base")
            
            print(f"✅ Successfully added {file.filename} to global knowledge base")
            
            return MultiDocumentUploadResponse(
                success=True,
                message=f"Successfully processed {file.filename} ({doc_type}) into {len(chunks)} chunks and added to global knowledge base",
                session_id=session_id,
                document_count=len(global_knowledge_base["user_uploaded_documents"]),
                filename=file.filename,
                doc_type=doc_type,
                regulatory_type=regulatory_type,
                chunks_created=len(chunks)
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
        print(f"  - Global KB initialized: {global_knowledge_base['initialized']}")
        
        # Check if global knowledge base is initialized
        if not global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Get or create session (for tracking purposes only)
        session_id = await get_or_create_session(request.session_id, request.api_key)
        print(f"✅ Session created/retrieved: {session_id}")
        
        # Always use global knowledge base
        global_kb = await get_global_knowledge_base(request.api_key)
        if not global_kb:
            print(f"❌ Could not get global knowledge base")
            raise HTTPException(status_code=500, detail="Could not access global knowledge base")
        
        total_docs = len(global_knowledge_base["documents"]) + len(global_knowledge_base["user_uploaded_documents"])
        print(f"✅ Using global knowledge base with {total_docs} total documents")
        print(f"  - Original documents: {len(global_knowledge_base['documents'])}")
        print(f"  - User uploaded documents: {len(global_knowledge_base['user_uploaded_documents'])}")
        
        rag_pipeline = global_kb["rag_pipeline"]
        vector_db = global_kb["vector_db"]
        
        if not rag_pipeline:
            print(f"❌ No RAG pipeline available in global knowledge base")
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized in global knowledge base")
        
        print(f"✅ RAG pipeline ready from global knowledge base")
        
        # Create streaming response
        async def generate():
            try:
                # Run RAG pipeline to get context and generate response
                if request.use_rag:
                    print(f"🔎 Searching global knowledge base for: {request.user_message}")
                    # Search for relevant documents
                    search_results = rag_pipeline.search_documents(
                        query=request.user_message,
                        k=4,
                        return_metadata=True
                    )
                    
                    print(f"📋 Found {len(search_results)} search results from global KB")
                    
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
                        print(f"❌ No relevant search results found in global knowledge base")
                        yield "I couldn't find relevant information in the knowledge base to answer your question."
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
    Always uses the global knowledge base.
    """
    try:
        print(f"🏛️ Regulatory RAG chat request received:")
        print(f"  - Session ID: {request.session_id}")
        print(f"  - User message: {request.user_message}")
        print(f"  - User role: {request.user_role}")
        print(f"  - Doc types filter: {request.doc_types}")
        print(f"  - Priority sources: {request.priority_sources}")
        print(f"  - Global KB initialized: {global_knowledge_base['initialized']}")
        
        # Check if global knowledge base is initialized
        if not global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Get or create session (for tracking purposes only)
        session_id = await get_or_create_session(request.session_id, request.api_key)
        print(f"✅ Session created/retrieved: {session_id}")
        
        # Always use global knowledge base
        global_kb = await get_global_knowledge_base(request.api_key)
        if not global_kb:
            print(f"❌ Could not get global knowledge base")
            raise HTTPException(status_code=500, detail="Could not access global knowledge base")
        
        total_docs = len(global_knowledge_base["documents"]) + len(global_knowledge_base["user_uploaded_documents"])
        print(f"✅ Using global knowledge base with {total_docs} total documents")
        
        regulatory_enhancer = global_kb.get("regulatory_enhancer")
        base_rag_pipeline = global_kb.get("rag_pipeline")
        
        if not regulatory_enhancer and not base_rag_pipeline:
            print(f"❌ No RAG pipeline available in global knowledge base")
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized in global knowledge base")
        
        print(f"✅ Regulatory RAG pipeline ready from global knowledge base")
        
        # Create streaming response
        async def generate():
            try:
                if request.use_rag:
                    print(f"🔎 Searching global knowledge base with regulatory enhancement...")
                    
                    if regulatory_enhancer:
                        # Use regulatory enhancer for better results
                        response = regulatory_enhancer.enhanced_rag_query(
                            query=request.user_message,
                            user_role=request.user_role,
                            doc_types=request.doc_types,
                            priority_sources=request.priority_sources,
                            k=4
                        )
                        
                        print(f"💼 Generated regulatory-enhanced response")
                        yield response
                    else:
                        # Fallback to base RAG pipeline
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
                            yield "I couldn't find relevant regulatory information in the knowledge base to answer your question."
                else:
                    # Fallback to regular chat without RAG
                    client = OpenAI(api_key=request.api_key)
                    stream = client.chat.completions.create(
                        model=request.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful regulatory compliance assistant."},
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
    """Delete a user session"""
    if session_id in user_sessions:
        del user_sessions[session_id]
        return {"message": f"Session {session_id} deleted successfully"}
    raise HTTPException(status_code=404, detail="Session not found")

# New endpoint for deleting user-uploaded documents
@app.delete("/api/document/{filename}")
async def delete_document(filename: str, api_key: str):
    """
    Delete a user-uploaded document from the global knowledge base.
    Original documents cannot be deleted.
    """
    try:
        print(f"🗑️ Delete request for document: {filename}")
        
        # Check if global knowledge base is initialized
        if not global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized")
        
        # Attempt to remove the document
        success = await remove_document_from_global_kb(filename, api_key)
        
        if success:
            print(f"✅ Successfully deleted {filename} from global knowledge base")
            return {
                "success": True,
                "message": f"Successfully deleted {filename} from global knowledge base",
                "remaining_user_documents": global_knowledge_base["user_uploaded_documents"],
                "total_documents": len(global_knowledge_base["documents"]) + len(global_knowledge_base["user_uploaded_documents"])
            }
        else:
            raise HTTPException(status_code=400, detail=f"Could not delete {filename}. Either it doesn't exist, is not a user-uploaded document, or an error occurred.")
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Unexpected error in delete_document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

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
    """Get information about the global knowledge base status and contents"""
    if not global_knowledge_base["initialized"]:
        return {
            "status": "not_initialized" if global_knowledge_base["error"] is None else "error",
            "initialized": False,
            "error": global_knowledge_base["error"],
            "documents": [],
            "user_uploaded_documents": [],
            "document_count": 0,
            "chunk_count": 0,
            "description": "Global knowledge base is not yet initialized"
        }
    
    total_chunks = len(global_knowledge_base.get("chunked_documents", []))
    total_original_docs = len(global_knowledge_base["documents"])
    total_user_docs = len(global_knowledge_base["user_uploaded_documents"])
    total_docs = total_original_docs + total_user_docs
    
    return {
        "status": "ready",
        "initialized": True,
        "error": None,
        "documents": global_knowledge_base["documents"],
        "user_uploaded_documents": global_knowledge_base["user_uploaded_documents"],
        "document_count": total_docs,
        "original_document_count": total_original_docs,
        "user_uploaded_document_count": total_user_docs,
        "chunk_count": total_chunks,
        "description": f"Global knowledge base with {total_original_docs} original documents, {total_user_docs} user-uploaded documents, and {total_chunks} total chunks"
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