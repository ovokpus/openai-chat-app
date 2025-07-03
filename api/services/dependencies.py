"""
Shared service dependencies for the FastAPI application.
Ensures single instances of services across all modules.
"""

import os
import sys

from .session_service import SessionService
from .global_kb_service import GlobalKnowledgeBaseService

# Create single shared instances
_session_service = SessionService()
_global_kb_service = GlobalKnowledgeBaseService()

def get_session_service() -> SessionService:
    """Get the shared session service instance"""
    return _session_service

def get_global_kb_service() -> GlobalKnowledgeBaseService:
    """Get the shared global knowledge base service instance"""
    return _global_kb_service

# Export the instances for direct access if needed
session_service = _session_service
global_kb_service = _global_kb_service 