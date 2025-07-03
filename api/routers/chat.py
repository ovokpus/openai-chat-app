from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add the project root to the Python path for aimakerspace imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aimakerspace.openai_utils.chatmodel import ChatOpenAI

router = APIRouter()

class ChatRequest(BaseModel):
    user_message: str
    model: Optional[str] = "gpt-4o-mini"
    api_key: str

@router.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        chat_model = ChatOpenAI(api_key=request.api_key)
        
        async def generate():
            async for chunk in chat_model.agenerate_response(request.user_message):
                yield chunk
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 