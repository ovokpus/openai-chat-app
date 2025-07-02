#!/usr/bin/env python3
"""
Debug what's actually stored in the vector database
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def inspect_search_results():
    """Inspect what the search actually returns"""
    print("🔍 INSPECTING SEARCH RESULTS")
    print("=" * 50)
    
    # Get a session
    response = requests.get(f"{BASE_URL}/api/sessions")
    sessions_data = response.json()
    session_id = sessions_data["sessions"][0]["session_id"]
    
    print(f"Session ID: {session_id}")
    
    # Make a RAG request but capture the backend logs
    # We'll use a test API key to trigger the search without calling OpenAI
    rag_request = {
        "user_message": "What is AWS?",
        "session_id": session_id,
        "api_key": "test-key-to-trigger-search",
        "use_rag": True
    }
    
    print("Making RAG request to see backend logs...")
    response = requests.post(f"{BASE_URL}/api/rag-chat", json=rag_request)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text[:500]}...")

if __name__ == "__main__":
    inspect_search_results() 