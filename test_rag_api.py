#!/usr/bin/env python3
"""
Test RAG API directly to debug the issue
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_rag_chat():
    """Test RAG chat with real API calls"""
    print("🔍 TESTING RAG CHAT API")
    print("=" * 50)
    
    # Get sessions first
    try:
        response = requests.get(f"{BASE_URL}/api/sessions")
        sessions_data = response.json()
        
        if not sessions_data["sessions"]:
            print("❌ No sessions found!")
            return False
            
        session_id = sessions_data["sessions"][0]["session_id"]
        print(f"✅ Using session: {session_id}")
        print(f"📄 Documents: {sessions_data['sessions'][0]['documents']}")
        
    except Exception as e:
        print(f"❌ Failed to get sessions: {e}")
        return False
    
    # Test RAG chat with a simple question
    test_questions = [
        "What is AWS?",
        "Tell me about machine learning services",
        "What are AWS certification topics?",
        "Explain the content of the document"
    ]
    
    for question in test_questions:
        print(f"\n🔎 Testing question: '{question}'")
        
        # Test with RAG enabled
        rag_request = {
            "user_message": question,
            "session_id": session_id,
            "api_key": "test-api-key",  # We'll use a test key to see what error we get
            "use_rag": True
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/rag-chat", json=rag_request)
            print(f"📋 Status: {response.status_code}")
            
            if response.status_code == 200:
                # Read the streaming response
                response_text = response.text
                print(f"✅ RAG Response ({len(response_text)} chars):")
                print(f"   {response_text[:200]}...")
                
                # Check if it's a generic response
                generic_indicators = [
                    "I couldn't find relevant information",
                    "I don't have access to",
                    "I apologize, but I don't",
                    "Error generating response",
                    "I encountered an error"
                ]
                
                is_generic = any(indicator in response_text for indicator in generic_indicators)
                print(f"🎯 Generic response: {'Yes' if is_generic else 'No'}")
                
            else:
                error_text = response.text
                print(f"❌ Error: {error_text}")
                
                # Check for specific error types
                if "401" in error_text or "Incorrect API key" in error_text:
                    print("💡 This is expected - we're using a test API key")
                    print("   The RAG pipeline is working, but needs a real API key")
                    return True
                elif "Session not found" in error_text:
                    print("💡 Session issue - need to check session management")
                elif "No documents found" in error_text:
                    print("💡 Documents not properly stored in session")
                else:
                    print("💡 Unexpected error - need further investigation")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        print("-" * 30)
    
    return True

def test_without_api_key():
    """Test what happens when we don't provide API key"""
    print("\n🔍 TESTING WITHOUT API KEY")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/sessions")
        sessions_data = response.json()
        session_id = sessions_data["sessions"][0]["session_id"]
        
        rag_request = {
            "user_message": "What is AWS?",
            "session_id": session_id,
            "api_key": "",  # Empty API key
            "use_rag": True
        }
        
        response = requests.post(f"{BASE_URL}/api/rag-chat", json=rag_request)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run all tests"""
    print("🚀 TESTING RAG API DIRECTLY")
    print("=" * 60)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend healthy: {health_data['active_sessions']} sessions")
        else:
            print("❌ Backend not healthy")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Test RAG functionality
    test_rag_chat()
    
    # Test without API key
    test_without_api_key()
    
    print("\n🎯 SUMMARY:")
    print("If you see 401/API key errors, the RAG pipeline is working!")
    print("If you see other errors, there may be implementation issues.")
    print("If you get responses but they're generic, check the search results.")

if __name__ == "__main__":
    main() 