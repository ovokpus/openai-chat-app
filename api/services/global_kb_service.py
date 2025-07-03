import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add api directory to path for aimakerspace imports
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

# Import aimakerspace modules
from aimakerspace.multi_document_processor import MultiDocumentProcessor
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.rag_pipeline import RAGPipeline
from aimakerspace.regulatory_rag_enhancer import RegulatoryRAGEnhancer

# Import our knowledge base data
from .knowledge_base_data import get_knowledge_base

class GlobalKnowledgeBaseService:
    def __init__(self):
        self.global_knowledge_base: Dict[str, Any] = {
            "vector_db": None,
            "documents": [],
            "user_uploaded_documents": [],
            "rag_pipeline": None,
            "regulatory_enhancer": None,
            "initialized": False,
            "error": None,
            "chunked_documents": [],
            "embedding_model": None,
            "chat_model": None
        }
    
    async def initialize_global_knowledge_base(self):
        """Initialize the global knowledge base from embedded data"""
        if self.global_knowledge_base["initialized"]:
            print("📚 Global knowledge base already initialized")
            return
        
        try:
            print("🚀 Initializing global knowledge base...")
            
            # Load data from our Python module
            preprocessed_data = get_knowledge_base()
            
            # Load the data
            await self._load_from_preprocessed_data(preprocessed_data)
            
        except Exception as e:
            print(f"❌ Failed to initialize global knowledge base: {e}")
            print("🏗️ Falling back to user-upload-only mode")
            self.global_knowledge_base["error"] = None  # Don't mark as error
            self.global_knowledge_base["initialized"] = True
    
    async def _load_from_preprocessed_data(self, preprocessed_data: Dict[str, Any]):
        """Load knowledge base from preprocessed JSON data"""
        try:
            metadata = preprocessed_data.get("metadata", {})
            chunks = preprocessed_data.get("chunks", [])
            
            print(f"📊 Loading preprocessed knowledge base:")
            print(f"  📅 Created: {metadata.get('created_at', 'unknown')}")
            print(f"  📄 Documents: {metadata.get('total_documents', 0)}")
            print(f"  📝 Chunks: {metadata.get('total_chunks', len(chunks))}")
            print(f"  📋 Version: {metadata.get('version', 'unknown')}")
            
            # Process chunks into our format
            all_chunks = []
            document_names = set()
            
            for chunk_data in chunks:
                # Convert to our internal format
                chunk_obj = {
                    "text": chunk_data["text"],
                    "metadata": chunk_data["metadata"]
                }
                all_chunks.append(chunk_obj)
                document_names.add(chunk_data["metadata"]["filename"])
            
            # Store the processed data
            self.global_knowledge_base["chunked_documents"] = all_chunks
            self.global_knowledge_base["documents"] = list(document_names)
            self.global_knowledge_base["initialized"] = True
            
            print(f"✅ Loaded {len(all_chunks)} chunks from {len(document_names)} documents")
            
            # Log the document breakdown
            if "processed_files" in metadata:
                print(f"📋 Document breakdown:")
                by_subfolder = {}
                for file_info in metadata["processed_files"]:
                    subfolder = file_info["subfolder"]
                    if subfolder not in by_subfolder:
                        by_subfolder[subfolder] = []
                    by_subfolder[subfolder].append(file_info)
                
                for subfolder, files in by_subfolder.items():
                    total_chunks = sum(f["chunk_count"] for f in files)
                    print(f"  📁 {subfolder}: {len(files)} files, {total_chunks} chunks")
            
        except Exception as e:
            print(f"❌ Error loading preprocessed data: {e}")
            raise
    
    async def _fallback_to_document_processing(self):
        """Fallback to processing documents from original folders (for local development)"""
        print("🔄 Falling back to document processing...")
        
        # Original document processing logic
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        potential_paths = [
            os.path.join(current_dir, "knowledge_base", "regulatory_docs"),  # Local development
            os.path.join(os.path.dirname(current_dir), "services", "knowledge_base", "regulatory_docs"),  # Vercel relative
            os.path.join("/var/task", "api", "services", "knowledge_base", "regulatory_docs"),  # Vercel absolute
            os.path.join(os.getcwd(), "api", "services", "knowledge_base", "regulatory_docs"),  # Working directory
        ]
        
        knowledge_base_path = None
        for path in potential_paths:
            if os.path.exists(path):
                knowledge_base_path = path
                break
        
        if knowledge_base_path:
            await self._process_knowledge_base_documents(knowledge_base_path)
        else:
            print("🏗️ No knowledge base documents found, initializing empty KB")
            self.global_knowledge_base["initialized"] = True
    
    async def _process_knowledge_base_documents(self, knowledge_base_path: str):
        """Process documents from the knowledge base folder"""
        # Get list of supported files from organized subfolders
        supported_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.pptx', '.ppt', '.csv', '.sql', '.py', '.js', '.ts', '.md', '.txt']
        
        document_files = []
        # Scan through all regulatory document subfolders
        for subfolder in os.listdir(knowledge_base_path):
            subfolder_path = os.path.join(knowledge_base_path, subfolder)
            if os.path.isdir(subfolder_path):
                for file in os.listdir(subfolder_path):
                    if any(file.lower().endswith(ext) for ext in supported_extensions):
                        document_files.append(os.path.join(subfolder_path, file))
        
        if not document_files:
            print("📂 No supported documents found in knowledge base folders")
            self.global_knowledge_base["initialized"] = True
            return
        
        print(f"📄 Found {len(document_files)} documents to process")
        
        # Process documents using MultiDocumentProcessor with text chunking for smaller chunks
        multi_doc_processor = MultiDocumentProcessor(enable_text_chunking=True, chunk_size=800)
        all_chunks = []
        
        for doc_path in document_files:
            try:
                filename = os.path.basename(doc_path)
                print(f"📄 Processing {filename}...")
                
                processed_docs = multi_doc_processor.process_document(doc_path, filename)
                
                for doc in processed_docs:
                    chunk_text = doc.content
                    metadata = doc.metadata.copy()
                    metadata.update({
                        "source": "global_kb",
                        "doc_type": doc.doc_type,
                        "source_location": doc.source_location
                    })
                    
                    all_chunks.append({
                        "text": chunk_text,
                        "metadata": metadata
                    })
                
                print(f"✅ Processed {filename}: {len(processed_docs)} chunks")
                self.global_knowledge_base["documents"].append(filename)
                
            except Exception as e:
                print(f"❌ Failed to process {doc_path}: {e}")
                continue
        
        # Store chunked documents for later re-initialization
        self.global_knowledge_base["chunked_documents"] = all_chunks
        
        print(f"📚 Global knowledge base initialized with {len(all_chunks)} total chunks from {len(document_files)} documents")
        self.global_knowledge_base["initialized"] = True
    
    async def get_global_knowledge_base(self, api_key: str):
        """Get or create global knowledge base with API key"""
        if not self.global_knowledge_base["initialized"]:
            await self.initialize_global_knowledge_base()
        
        if self.global_knowledge_base["error"]:
            return None
        
        if not self.global_knowledge_base["chunked_documents"]:
            return None
        
        try:
            # Create embedding model and vector database
            embedding_model = EmbeddingModel(api_key=api_key)
            vector_db = VectorDatabase(embedding_model=embedding_model)
            
            # Add all chunks to vector database
            chunks = self.global_knowledge_base["chunked_documents"]
            
            async def generate_and_insert_embeddings():
                print(f"🔄 Generating embeddings for {len(chunks)} chunks...")
                
                # Extract texts for batch embedding generation
                texts = [chunk["text"] for chunk in chunks]
                
                # Generate embeddings in batches
                embeddings = await embedding_model.async_get_embeddings(texts)
                
                # Insert vectors with metadata
                for chunk, embedding in zip(chunks, embeddings):
                    vector_db.insert(chunk["text"], embedding, chunk["metadata"])
                
                print(f"✅ Generated and stored {len(embeddings)} embeddings in global knowledge base")
            
            await generate_and_insert_embeddings()
            
            # Create chat model and RAG pipeline
            chat_model = ChatOpenAI(api_key=api_key)
            rag_pipeline = RAGPipeline(llm=chat_model, vector_db=vector_db)
            
            # Create regulatory enhancer
            regulatory_enhancer = RegulatoryRAGEnhancer(rag_pipeline)
            
            # Update global knowledge base
            self.global_knowledge_base.update({
                "vector_db": vector_db,
                "rag_pipeline": rag_pipeline,
                "regulatory_enhancer": regulatory_enhancer,
                "embedding_model": embedding_model,
                "chat_model": chat_model
            })
            
            return {
                "vector_db": vector_db,
                "rag_pipeline": rag_pipeline,
                "regulatory_enhancer": regulatory_enhancer,
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            print(f"❌ Failed to create global knowledge base instance: {e}")
            return None
    
    async def add_document_to_global_kb(self, processed_docs: List, filename: str, api_key: str, temp_file_path: str = None) -> bool:
        """Add a user-uploaded document to the global knowledge base"""
        if not self.global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            return False
        
        try:
            print(f"🌍 Adding {filename} to global knowledge base with {len(processed_docs)} chunks...")
            
            # Save uploaded file to organized uploaded_docs folder for persistence
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    uploaded_docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base", "uploaded_docs")
                    os.makedirs(uploaded_docs_path, exist_ok=True)
                    
                    # Create unique filename with timestamp to avoid conflicts
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_ext = os.path.splitext(filename)[1]
                    base_name = os.path.splitext(filename)[0]
                    unique_filename = f"{timestamp}_{base_name}{file_ext}"
                    
                    persistent_file_path = os.path.join(uploaded_docs_path, unique_filename)
                    import shutil
                    shutil.copy2(temp_file_path, persistent_file_path)
                    print(f"💾 Saved uploaded file to: uploaded_docs/{unique_filename}")
                except Exception as e:
                    print(f"⚠️ Could not save uploaded file to disk: {e} (continuing with in-memory storage)")
            
            # Get or create global knowledge base with API key
            global_kb = await self.get_global_knowledge_base(api_key)
            if not global_kb:
                print(f"❌ Could not get global knowledge base")
                return False
            
            vector_db = global_kb["vector_db"]
            chunks_added = 0
            
            # Process each document chunk
            for i, doc in enumerate(processed_docs):
                try:
                    # Generate embedding for the document content
                    embeddings = await vector_db.embedding_model.async_get_embeddings([doc.content])
                    
                    # Create metadata
                    metadata = doc.metadata.copy()
                    metadata.update({
                        "filename": filename,
                        "chunk_index": i,
                        "upload_time": datetime.now().isoformat(),
                        "source": "user_uploaded",
                        "is_original": False  # Mark as user-uploaded, not original
                    })
                    
                    # Insert into global vector database
                    vector_db.insert(doc.content, embeddings[0], metadata)
                    chunks_added += 1
                    
                    # Add to chunked_documents list
                    chunk_obj = {
                        "text": doc.content,
                        "metadata": metadata
                    }
                    self.global_knowledge_base["chunked_documents"].append(chunk_obj)
                    
                    if (i + 1) % 10 == 0:
                        print(f"🔄 Added chunk {i + 1}/{len(processed_docs)} to global KB...")
                        
                except Exception as e:
                    print(f"⚠️ Error adding chunk {i+1} to global KB: {e}")
                    continue
            
            # Update global knowledge base tracking
            if filename not in self.global_knowledge_base["user_uploaded_documents"]:
                self.global_knowledge_base["user_uploaded_documents"].append(filename)
            
            # Update the references
            self.global_knowledge_base.update({
                "vector_db": vector_db,
                "rag_pipeline": global_kb["rag_pipeline"],
                "regulatory_enhancer": global_kb["regulatory_enhancer"],
                "embedding_model": global_kb["rag_pipeline"].vector_db.embedding_model,
                "chat_model": global_kb["rag_pipeline"].llm
            })
            
            print(f"✅ Successfully added {chunks_added} chunks from {filename} to global knowledge base")
            return True
            
        except Exception as e:
            print(f"❌ Error adding document to global knowledge base: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def remove_document_from_global_kb(self, filename: str, api_key: str) -> bool:
        """Remove a user-uploaded document from the global knowledge base"""
        if not self.global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            return False
        
        # Check if this is a user-uploaded document
        if filename not in self.global_knowledge_base["user_uploaded_documents"]:
            print(f"❌ Cannot remove {filename} - not a user-uploaded document or doesn't exist")
            return False
        
        try:
            print(f"🗑️ Removing {filename} from global knowledge base...")
            
            # First, remove the physical file from uploaded_docs folder
            try:
                uploaded_docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base", "uploaded_docs")
                if os.path.exists(uploaded_docs_path):
                    # Find the timestamped file that corresponds to this filename
                    # Files are saved with format: {timestamp}_{original_filename}
                    base_name = os.path.splitext(filename)[0]
                    file_ext = os.path.splitext(filename)[1]
                    
                    for file in os.listdir(uploaded_docs_path):
                        # Check if this file matches the pattern and original filename
                        if file.endswith(f"_{base_name}{file_ext}") and file.startswith("20"):
                            file_path = os.path.join(uploaded_docs_path, file)
                            os.remove(file_path)
                            print(f"🗂️ Deleted physical file: uploaded_docs/{file}")
                            break
                    else:
                        print(f"⚠️ Physical file for {filename} not found in uploaded_docs folder")
                else:
                    print(f"⚠️ uploaded_docs folder not found: {uploaded_docs_path}")
            except Exception as e:
                print(f"⚠️ Could not delete physical file for {filename}: {e} (continuing with vector database cleanup)")
            
            # Get current global knowledge base
            global_kb = await self.get_global_knowledge_base(api_key)
            if not global_kb:
                print(f"❌ Could not get global knowledge base")
                return False
            
            vector_db = global_kb["vector_db"]
            chunks_removed = 0
            
            # Find and remove all chunks for this filename
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
            self.global_knowledge_base["chunked_documents"] = [
                chunk for chunk in self.global_knowledge_base["chunked_documents"]
                if chunk.get("metadata", {}).get("filename") != filename
            ]
            
            # Remove from user_uploaded_documents list
            self.global_knowledge_base["user_uploaded_documents"].remove(filename)
            
            # Update the references
            self.global_knowledge_base.update({
                "vector_db": vector_db,
                "rag_pipeline": global_kb["rag_pipeline"],
                "regulatory_enhancer": global_kb["regulatory_enhancer"]
            })
            
            print(f"✅ Successfully removed {chunks_removed} chunks from {filename} from global knowledge base")
            return True
            
        except Exception as e:
            print(f"❌ Error removing document from global knowledge base: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get global knowledge base information"""
        if not self.global_knowledge_base["initialized"]:
            return {
                "status": "not_initialized",
                "initialized": False,
                "error": None,
                "documents": [],
                "user_uploaded_documents": [],
                "document_count": 0,
                "original_document_count": 0,
                "user_uploaded_document_count": 0,
                "chunk_count": 0,
                "description": "Global knowledge base not yet initialized"
            }
        
        if self.global_knowledge_base["error"]:
            return {
                "status": "error",
                "initialized": True,
                "error": self.global_knowledge_base["error"],
                "documents": [],
                "user_uploaded_documents": [],
                "document_count": 0,
                "original_document_count": 0,
                "user_uploaded_document_count": 0,
                "chunk_count": 0,
                "description": f"Global knowledge base initialization failed: {self.global_knowledge_base['error']}"
            }
        
        original_docs = self.global_knowledge_base["documents"]
        user_docs = self.global_knowledge_base["user_uploaded_documents"]
        chunk_count = len(self.global_knowledge_base["chunked_documents"])
        
        # Determine status and description based on content
        if len(original_docs) == 0 and len(user_docs) == 0:
            status = "ready"
            description = "Global knowledge base ready for document uploads (no pre-loaded documents available)"
        elif len(original_docs) == 0:
            status = "ready"
            description = f"Global knowledge base ready with {len(user_docs)} user uploads ({chunk_count} chunks total)"
        else:
            status = "ready"
            description = f"Global knowledge base ready with {len(original_docs)} regulatory documents and {len(user_docs)} user uploads ({chunk_count} chunks total)"
        
        return {
            "status": status,
            "initialized": True,
            "error": None,
            "documents": original_docs,
            "user_uploaded_documents": user_docs,
            "document_count": len(original_docs) + len(user_docs),
            "original_document_count": len(original_docs),
            "user_uploaded_document_count": len(user_docs),
            "chunk_count": chunk_count,
            "description": description
        } 