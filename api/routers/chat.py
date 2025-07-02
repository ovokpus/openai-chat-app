from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from models.request_models import ChatRequest, RAGChatRequest, RegulatoryRAGRequest

router = APIRouter()

# Services - using shared instances
from services.dependencies import session_service, global_kb_service

DEVELOPER_MESSAGE = """You are a helpful AI assistant that creates beautifully formatted, professional responses. 

📋 **FORMATTING EXCELLENCE RULES:**

**STRUCTURE & HEADERS:**
- Start with a clear, descriptive title using # for main topics
- Use ## for major sections and ### for subsections
- Create logical information hierarchy with proper nesting

**TEXT FORMATTING:**
- **Bold** for key concepts, important terms, and section highlights
- *Italics* for emphasis, definitions, or secondary information
- `Code formatting` for technical terms, formulas, or specific values
- Use > blockquotes for important notes or warnings

**LISTS & ORGANIZATION:**
- Use numbered lists (1. 2. 3.) for sequential steps or ranked items
- Use bullet points (•) for related items or features
- Create sub-bullets with proper indentation for detailed breakdowns
- Add spacing between list sections for readability

**MATHEMATICAL EXPRESSIONS:**
- Inline math: $expression$ for simple formulas within text
- Display math: $$expression$$ for complex formulas on separate lines
- NEVER use brackets [ ] or parentheses ( ) around math expressions
- Always use proper LaTeX syntax within markdown delimiters

**VISUAL ENHANCEMENTS:**
- Use emojis sparingly but effectively (📊 for data, 💡 for insights, ⚠️ for warnings)
- Create tables using markdown table syntax when presenting structured data
- Add horizontal rules (---) to separate major sections
- Use proper spacing between paragraphs and sections

**EXAMPLES:**
✅ EXCELLENT: 
# Capital Requirements Analysis
## **Key Components**
### 📊 Tier 1 Capital
- **Common Equity Tier 1 (CET1)**: Use proper LaTeX math notation for formulas

❌ POOR: The CET1 ratio is [CET1 Capital / RWA * 100%]

Create responses that are visually appealing, easy to scan, and professionally structured."""

@router.post("/chat")
async def chat(request: ChatRequest):
    """Basic chat endpoint without RAG functionality"""
    try:
        client = OpenAI(api_key=request.api_key)
        
        async def generate():
            try:
                # Create a non-streaming chat completion request first, then stream the response
                response = client.chat.completions.create(
                    model=request.model,
                    messages=[
                        {"role": "system", "content": DEVELOPER_MESSAGE},
                        {"role": "user", "content": request.user_message}
                    ],
                    stream=False
                )
                
                # Get the full response content
                full_response = response.choices[0].message.content or "No response generated"
                
                # Stream the response by paragraphs to preserve formatting and ensure proper termination
                paragraphs = full_response.split('\n\n')
                
                for paragraph in paragraphs:
                    if paragraph.strip():
                        yield f"{paragraph.strip()}\n\n"
                        
            except Exception as e:
                yield f"Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate(), 
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
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
                rag_result = rag_pipeline.run(
                    query=request.user_message,
                    k=4
                )
                
                # Extract the response text from the result dictionary
                response_text = rag_result.get("response", "No response generated")
                
                # Stream the response by paragraphs to preserve formatting structure
                # Split by double newlines (paragraph breaks) to keep content blocks together
                paragraphs = response_text.split('\n\n')
                
                for paragraph in paragraphs:
                    if paragraph.strip():
                        yield f"{paragraph.strip()}\n\n"

                
            except Exception as e:
                yield f"Error: {str(e)}\n\n"

        
        return StreamingResponse(
            generate(), 
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
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
                
                # Stream the response by paragraphs to preserve formatting structure
                response_text = response_data.get("response", "No response generated")
                # Split by double newlines (paragraph breaks) to keep content blocks together
                paragraphs = response_text.split('\n\n')
                
                for paragraph in paragraphs:
                    if paragraph.strip():
                        yield f"{paragraph.strip()}\n\n"
                
            except Exception as e:
                yield f"Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate(), 
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 