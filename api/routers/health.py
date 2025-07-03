from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "healthy"} 