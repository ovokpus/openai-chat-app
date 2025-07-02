#!/usr/bin/env python3
"""
Comprehensive RAG System Debug Script
This script tests the RAG system step by step to identify any issues.
"""

import requests
import json
import time
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, '.')

def test_backend_health():
    """Test if the backend is running and healthy"""
    try:
        response = requests.get('http://localhost:8000/api/health')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data}")
            return True
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_sessions_endpoint():
    """Test the sessions debug endpoint"""
    try:
        response = requests.get('http://localhost:8000/api/sessions')
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Current sessions: {data}")
            return data
        else:
            print(f"❌ Sessions endpoint failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Sessions endpoint error: {e}")
        return None

def test_pdf_upload():
    """Test PDF upload with a simple text file (since we're debugging)"""
    try:
        # Create a simple test text file that will be treated as PDF for upload testing
        test_content = """
        AWS (Amazon Web Services) is a comprehensive cloud computing platform.
        
        Key AWS Services:
        1. EC2 (Elastic Compute Cloud) - Virtual servers in the cloud
        2. S3 (Simple Storage Service) - Object storage service
        3. RDS (Relational Database Service) - Managed database service
        4. Lambda - Serverless computing platform
        5. CloudFormation - Infrastructure as code service
        
        AWS provides scalable, reliable, and secure cloud infrastructure.
        Companies can use AWS to reduce costs and increase agility.
        """
        
        # Write test content to a file
        with open('test_aws_doc.txt', 'w') as f:
            f.write(test_content)
        
        # Upload the file (even though it's not a real PDF, we can test the pipeline)
        with open('test_aws_doc.txt', 'rb') as f:
            files = {'file': ('test_aws_doc.pdf', f, 'application/pdf')}
            # Get API key from environment variable
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ No OPENAI_API_KEY found in environment. Skipping upload test.")
                return None
            
            data = {
                'api_key': api_key
            }
            
            print("📤 Uploading test document...")
            response = requests.post('http://localhost:8000/api/upload-pdf', files=files, data=data)
            
            print(f"Upload status: {response.status_code}")
            print(f"Upload response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful: {result}")
                return result.get('session_id')
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return None
    finally:
        # Clean up test file
        if os.path.exists('test_aws_doc.txt'):
            os.remove('test_aws_doc.txt')

def test_rag_chat(session_id):
    """Test RAG chat functionality"""
    try:
        # Get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ No OPENAI_API_KEY found in environment. Skipping RAG test.")
            return False
            
        data = {
            "user_message": "What are the key AWS services?",
            "session_id": session_id,
            "api_key": api_key,
            "use_rag": True
        }
        
        print("💬 Testing RAG chat...")
        response = requests.post('http://localhost:8000/api/rag-chat', json=data)
        
        print(f"RAG chat status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ RAG response: {response.text}")
            return True
        else:
            print(f"❌ RAG chat failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ RAG chat error: {e}")
        return False

def test_aimakerspace_directly():
    """Test aimakerspace library directly"""
    try:
        print("🧪 Testing aimakerspace library directly...")
        
        from aimakerspace.vectordatabase import VectorDatabase
        from aimakerspace.openai_utils.embedding import EmbeddingModel
        from aimakerspace.rag_pipeline import RAGPipeline
        from aimakerspace.openai_utils.chatmodel import ChatOpenAI
        from aimakerspace.text_utils import CharacterTextSplitter
        import numpy as np
        
        # Skip aimakerspace test if no API key (requires real key for embeddings)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ No OPENAI_API_KEY found. Skipping aimakerspace test.")
            return True
        
        print("📊 Creating components...")
        embedding_model = EmbeddingModel(api_key=api_key)
        vector_db = VectorDatabase(embedding_model=embedding_model)
        chat_model = ChatOpenAI(api_key=api_key)
        rag_pipeline = RAGPipeline(llm=chat_model, vector_db=vector_db)
        
        print("📝 Testing text splitting...")
        text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        test_text = "This is a test document about AWS services. EC2 provides virtual servers. S3 provides storage."
        chunks = text_splitter.split_texts([test_text])
        print(f"✅ Text split into {len(chunks)} chunks: {chunks}")
        
        print("💾 Testing vector storage...")
        for i, chunk in enumerate(chunks):
            # Use dummy embeddings for testing
            dummy_embedding = np.random.rand(1536)
            metadata = {"filename": "test.pdf", "chunk_index": i}
            vector_db.insert(chunk, dummy_embedding, metadata)
        
        print(f"✅ Stored {len(chunks)} chunks in vector database")
        
        # Test search
        print("🔍 Testing vector search...")
        test_query_vector = np.random.rand(1536)
        search_results = vector_db.search(test_query_vector, k=2)
        print(f"✅ Search returned {len(search_results)} results")
        
        print("🎉 Direct aimakerspace test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Direct aimakerspace test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting RAG System Debug...\n")
    
    # Test 1: Backend health
    print("=" * 50)
    print("TEST 1: Backend Health")
    print("=" * 50)
    if not test_backend_health():
        print("❌ Backend is not running. Please start the backend first.")
        return
    
    # Test 2: Sessions
    print("\n" + "=" * 50)
    print("TEST 2: Sessions Status")
    print("=" * 50)
    sessions = test_sessions_endpoint()
    
    # Test 3: Direct aimakerspace test
    print("\n" + "=" * 50)
    print("TEST 3: Direct Aimakerspace Library Test")
    print("=" * 50)
    test_aimakerspace_directly()
    
    # Test 4: PDF Upload (commented out since it needs real API key)
    print("\n" + "=" * 50)
    print("TEST 4: PDF Upload (Skipped - needs real API key)")
    print("=" * 50)
    print("⚠️  PDF upload test skipped because it requires a real OpenAI API key")
    print("⚠️  To test upload, add your API key to the test_pdf_upload() function")
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")
    print("=" * 50)
    print("Summary:")
    print("- Backend health: Check if running on http://localhost:8000")
    print("- Sessions: Check if any sessions exist")  
    print("- Aimakerspace: Check if library works correctly")
    print("- To test full pipeline: Add real API key and upload a PDF")

if __name__ == "__main__":
    main() 