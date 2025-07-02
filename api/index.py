"""
Vercel-compatible entry point for the FastAPI application
"""
from app import app

# This is the handler that Vercel will call
def handler(request, response):
    return app(request, response)

# Export the app for Vercel
__all__ = ["app"] 