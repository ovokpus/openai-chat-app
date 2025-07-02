import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aimakerspace.multi_document_processor import MultiDocumentProcessor
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.rag_pipeline import RAGPipeline
from aimakerspace.regulatory_rag_enhancer import RegulatoryRAGEnhancer

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
        """Initialize the global knowledge base with documents from the documents folder"""
        if self.global_knowledge_base["initialized"]:
            print("📚 Global knowledge base already initialized")
            return
        
        try:
            print("🚀 Initializing global knowledge base with regulatory documents...")
            
            # Path to documents folder - handle both local and Vercel deployment
            if os.getenv('VERCEL'):
                # In Vercel, documents are at the root level
                documents_path = os.path.join("/var/task", "documents")
            else:
                # Local development path
                documents_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "documents")
            
            if not os.path.exists(documents_path):
                print(f"📂 Documents folder not found at {documents_path}")
                self.global_knowledge_base["initialized"] = True
                self.global_knowledge_base["error"] = "Documents folder not found"
                return
            
            # Get list of supported files
            supported_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.pptx', '.ppt', '.csv', '.sql', '.py', '.js', '.ts', '.md', '.txt']
            
            document_files = []
            for file in os.listdir(documents_path):
                if any(file.lower().endswith(ext) for ext in supported_extensions):
                    document_files.append(os.path.join(documents_path, file))
            
            if not document_files:
                print("📂 No supported documents found in documents folder")
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
            
        except Exception as e:
            print(f"❌ Failed to initialize global knowledge base: {e}")
            self.global_knowledge_base["error"] = str(e)
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
    
    async def add_document_to_global_kb(self, processed_docs: List, filename: str, api_key: str) -> bool:
        """Add a user-uploaded document to the global knowledge base"""
        if not self.global_knowledge_base["initialized"]:
            print(f"❌ Global knowledge base not initialized")
            return False
        
        try:
            print(f"🌍 Adding {filename} to global knowledge base with {len(processed_docs)} chunks...")
            
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
        
        return {
            "status": "ready",
            "initialized": True,
            "error": None,
            "documents": original_docs,
            "user_uploaded_documents": user_docs,
            "document_count": len(original_docs) + len(user_docs),
            "original_document_count": len(original_docs),
            "user_uploaded_document_count": len(user_docs),
            "chunk_count": chunk_count,
            "description": f"Global knowledge base ready with {len(original_docs)} regulatory documents and {len(user_docs)} user uploads ({chunk_count} chunks total)"
        } 