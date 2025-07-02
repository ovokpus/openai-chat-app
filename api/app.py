"""
FastAPI application for OpenAI Chat with RAG capabilities.
Refactored from monolithic structure to modular architecture.
"""

import os
import sys
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add parent directory to Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modular routers
from routers import chat_router, documents_router
from services.dependencies import global_kb_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup: Initialize global knowledge base
    print("🚀 Starting OpenAI Chat App with RAG...")
    asyncio.create_task(global_kb_service.initialize_global_knowledge_base())
    
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

# Configure CORS (PRODUCTION: Replace with specific origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
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
    from fastapi import HTTPException
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