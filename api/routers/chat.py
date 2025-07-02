from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from models.request_models import ChatRequest, RAGChatRequest, RegulatoryRAGRequest
from services.session_service import SessionService
from services.global_kb_service import GlobalKnowledgeBaseService

router = APIRouter()

# Services
session_service = SessionService()
global_kb_service = GlobalKnowledgeBaseService()

DEVELOPER_MESSAGE = """You are a helpful AI assistant. When providing responses:

FORMATTING RULES:
- Use proper markdown formatting for all text
- For mathematical expressions, ALWAYS use standard markdown math delimiters:
  - Inline math: $expression$ 
  - Display math: $$expression$$
- NEVER use brackets [ ] or parentheses ( ) around math expressions
- NEVER use \\[ \\] LaTeX delimiters
- Use **bold** for emphasis and *italics* when needed
- Use numbered lists (1. 2. 3.) and bullet points (- item) properly
- Use ### for headings when structuring responses

MATH EXAMPLES:
✅ CORRECT: The formula is $$\\frac{12}{4} = 3$$
❌ WRONG: The formula is [\\frac{12}{4} = 3]
❌ WRONG: The formula is (\\frac{12}{4} = 3)

Always format mathematical calculations using proper markdown math syntax with $$ delimiters."""

@router.post("/chat")
async def chat(request: ChatRequest):
    """Basic chat endpoint without RAG functionality"""
    try:
        client = OpenAI(api_key=request.api_key)
        
        async def generate():
            # Create a streaming chat completion request
            stream = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": request.developer_message},
                    {"role": "user", "content": request.user_message}
                ],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag-chat")
async def rag_chat(request: RAGChatRequest):
    """RAG chat endpoint using uploaded documents and global knowledge base"""
    try:
        # Get or create session
        session_id = await session_service.get_or_create_session(request.session_id, request.api_key)
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get global knowledge base
        global_kb = await global_kb_service.get_global_knowledge_base(request.api_key)
        if not global_kb:
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Use global knowledge base for RAG
        try:
            rag_pipeline = global_kb["rag_pipeline"]
        except Exception as e:
            raise HTTPException(status_code=500, detail="Could not access global knowledge base")
        
        if not rag_pipeline:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized in global knowledge base")
        
        async def generate():
            try:
                # Use RAG pipeline to get response
                response = rag_pipeline.run_rag(
                    query=request.user_message,
                    k=4,
                    system_prompt=DEVELOPER_MESSAGE
                )
                
                # Stream the response
                for token in response.split():
                    yield f"data: {token} \n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regulatory-rag-chat")
async def regulatory_rag_chat(request: RegulatoryRAGRequest):
    """Enhanced RAG chat with regulatory-specific features"""
    try:
        # Get or create session
        session_id = await session_service.get_or_create_session(request.session_id, request.api_key)
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get global knowledge base
        global_kb = await global_kb_service.get_global_knowledge_base(request.api_key)
        if not global_kb:
            raise HTTPException(status_code=503, detail="Global knowledge base not initialized. Please try again later.")
        
        # Use regulatory enhancer
        try:
            regulatory_enhancer = global_kb["regulatory_enhancer"]
        except Exception as e:
            raise HTTPException(status_code=500, detail="Could not access global knowledge base")
        
        if not regulatory_enhancer:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized in global knowledge base")
        
        async def generate():
            try:
                # Use regulatory RAG enhancer
                response_data = regulatory_enhancer.run_enhanced_rag(
                    query=request.user_message,
                    user_role=request.user_role,
                    k=4,
                    doc_types=request.doc_types,
                    priority_sources=request.priority_sources
                )
                
                # Stream the response
                response_text = response_data.get("response", "No response generated")
                for token in response_text.split():
                    yield f"data: {token} \n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 