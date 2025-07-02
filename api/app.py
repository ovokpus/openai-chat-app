"""
FastAPI application for OpenAI Chat with RAG capabilities.
Refactored from monolithic structure to modular architecture.
"""

import os
import sys
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import modular routers
from routers import chat_router, documents_router
from services.dependencies import global_kb_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup: Initialize global knowledge base
    print("🚀 Starting OpenAI Chat App with RAG...")
    print("📚 Initializing global knowledge base...")
    
    try:
        # Initialize synchronously during startup to ensure it's ready
        await global_kb_service.initialize_global_knowledge_base()
        info = global_kb_service.get_info()
        print(f"📊 Global KB Status: {info['status']}")
        print(f"📄 Documents: {info['original_document_count']} original, {info['user_uploaded_document_count']} uploaded")
        print(f"📚 Total chunks: {info['chunk_count']}")
    except Exception as e:
        print(f"❌ Failed to initialize global knowledge base: {e}")
        print("⚠️ App will continue but RAG features may not work")
    
    yield
    
    # Shutdown
    print("⬇️ Shutting down OpenAI Chat App...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="OpenAI Chat App with RAG",
    description="A conversational AI application with Retrieval-Augmented Generation capabilities for regulatory documents",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS for production and development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://openai-chat-cp95byr2i-ovo-okpubulukus-projects.vercel.app",
        "https://*.vercel.app"  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(documents_router, prefix="/api", tags=["documents"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenAI Chat App with RAG - Modular Architecture",
        "version": "2.0.0",
        "docs": "/docs",
        "global_kb_status": global_kb_service.get_info()["status"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "global_kb": global_kb_service.get_info()
    }

# Legacy endpoint redirects for backward compatibility
@app.post("/api/upload-pdf")
async def upload_pdf_legacy(request: Request):
    """Legacy PDF upload endpoint - redirects to new document upload"""
    raise HTTPException(
        status_code=301, 
        detail="This endpoint has been moved to /api/upload-document"
    )

@app.post("/api/chat")
async def chat_legacy(request: Request):
    """Legacy chat endpoint"""
    # This will be handled by the chat router
    pass

@app.post("/api/rag-chat")  
async def rag_chat_legacy(request: Request):
    """Legacy RAG chat endpoint"""
    # This will be handled by the chat router
    pass

@app.get("/api/test-aimakerspace")
async def test_aimakerspace():
    """Test endpoint to verify aimakerspace package installation"""
    try:
        import aimakerspace
        from aimakerspace import openai_utils, rag_pipeline
        return {
            "status": "success",
            "message": "aimakerspace package is installed and accessible",
            "version": getattr(aimakerspace, '__version__', 'unknown'),
            "location": aimakerspace.__file__
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Failed to import aimakerspace: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Vercel serverless function export
handler = app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting server on port {port}")
    print("📚 Global knowledge base will be initialized on startup")
    print("🌐 CORS configured for frontend development")
    print("📖 API documentation available at http://localhost:{port}/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )