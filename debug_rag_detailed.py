#!/usr/bin/env python3
"""
Detailed RAG Debug Script
This script tests each step of the RAG pipeline to identify the specific issue.
"""

import sys
import os
import numpy as np
from pprint import pprint

# Add the current directory to Python path
sys.path.insert(0, '.')

def test_session_state():
    """Test the current session state"""
    print("🔍 TESTING SESSION STATE")
    print("=" * 50)
    
    try:
        from api.app import user_sessions
        
        if not user_sessions:
            print("❌ No active sessions found!")
            return None
            
        print(f"📊 Found {len(user_sessions)} active sessions")
        
        for session_id, session in user_sessions.items():
            print(f"\n📝 Session: {session_id}")
            print(f"  - Documents: {session.get('documents', [])}")
            print(f"  - Has vector_db: {'vector_db' in session}")
            print(f"  - Has rag_pipeline: {'rag_pipeline' in session and session['rag_pipeline'] is not None}")
            
            if 'vector_db' in session:
                vdb = session['vector_db']
                print(f"  - Vector count: {len(vdb.vectors)}")
                print(f"  - Has embedding_model: {hasattr(vdb, 'embedding_model') and vdb.embedding_model is not None}")
                
                if hasattr(vdb, 'embedding_model') and vdb.embedding_model:
                    em = vdb.embedding_model
                    print(f"  - Embedding model has API key: {hasattr(em, 'openai_api_key') and bool(em.openai_api_key)}")
                
                # Test a sample vector search
                if len(vdb.vectors) > 0:
                    print(f"  - Sample vectors:")
                    for i, (key, vector) in enumerate(list(vdb.vectors.items())[:2]):
                        print(f"    {i+1}. Key length: {len(key)} chars")
                        print(f"       Preview: {key[:100]}...")
                        print(f"       Vector shape: {vector.shape if hasattr(vector, 'shape') else 'Unknown'}")
        
        return list(user_sessions.keys())[0] if user_sessions else None
        
    except Exception as e:
        print(f"❌ Error testing session state: {e}")
        return None

def test_vector_search(session_id, test_query="What are AWS services?"):
    """Test vector search functionality"""
    print(f"\n🔍 TESTING VECTOR SEARCH")
    print("=" * 50)
    
    try:
        from api.app import user_sessions
        
        if session_id not in user_sessions:
            print(f"❌ Session {session_id} not found")
            return False
            
        session = user_sessions[session_id]
        vector_db = session['vector_db']
        
        print(f"📋 Testing search for: '{test_query}'")
        
        # Check if we have an embedding model
        if not hasattr(vector_db, 'embedding_model') or not vector_db.embedding_model:
            print("❌ No embedding model found")
            return False
            
        print("✅ Embedding model found")
        
        # Test getting query embedding
        try:
            query_embedding = vector_db.embedding_model.get_embedding(test_query)
            print(f"✅ Generated query embedding, shape: {len(query_embedding)}")
        except Exception as e:
            print(f"❌ Failed to generate query embedding: {e}")
            return False
        
        # Test vector search
        try:
            search_results = vector_db.search(np.array(query_embedding), k=4)
            print(f"✅ Vector search completed, found {len(search_results)} results")
            
            for i, (key, score) in enumerate(search_results):
                print(f"  {i+1}. Score: {score:.4f}")
                print(f"      Text preview: {key[:150]}...")
                metadata = vector_db.get_metadata(key)
                print(f"      Metadata: {metadata}")
                print()
                
            return len(search_results) > 0
            
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error in vector search test: {e}")
        return False

def test_rag_pipeline(session_id, test_query="What are AWS services?"):
    """Test the full RAG pipeline"""
    print(f"\n🔍 TESTING RAG PIPELINE")
    print("=" * 50)
    
    try:
        from api.app import user_sessions
        
        if session_id not in user_sessions:
            print(f"❌ Session {session_id} not found")
            return False
            
        session = user_sessions[session_id]
        rag_pipeline = session.get('rag_pipeline')
        
        if not rag_pipeline:
            print("❌ No RAG pipeline found")
            return False
            
        print("✅ RAG pipeline found")
        
        # Test search_documents
        print(f"🔎 Testing search_documents with: '{test_query}'")
        try:
            search_results = rag_pipeline.search_documents(test_query, k=4, return_metadata=True)
            print(f"✅ Search completed, found {len(search_results)} results")
            
            if not search_results:
                print("❌ No search results found!")
                return False
                
            for i, result in enumerate(search_results):
                print(f"  Result {i+1}:")
                print(f"    Score: {result.get('score', 'N/A')}")
                print(f"    Text preview: {result.get('text', '')[:100]}...")
                print(f"    Metadata: {result.get('metadata', {})}")
                print()
                
        except Exception as e:
            print(f"❌ Search documents failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test format_context
        print("📝 Testing format_context...")
        try:
            context, metadata_info = rag_pipeline.format_context(search_results)
            print(f"✅ Context formatted, length: {len(context)} characters")
            print(f"📋 Metadata info: {metadata_info}")
            print(f"🎯 Context preview:\n{context[:500]}...")
            
        except Exception as e:
            print(f"❌ Format context failed: {e}")
            return False
        
        # Test generate_response (this would require a real API key, so we'll simulate)
        print("💬 Testing response generation...")
        try:
            # We'll test the prompt creation without actually calling the LLM
            user_prompt_text = f"""Question: {test_query}

Context from documents:
{context}

Please answer the question based on the provided context."""
            
            print(f"✅ Generated prompt, length: {len(user_prompt_text)} characters")
            print(f"🎯 Prompt preview:\n{user_prompt_text[:300]}...")
            
            # If we have a test API key, we could actually test the LLM call here
            
        except Exception as e:
            print(f"❌ Response generation setup failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error in RAG pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("🚀 STARTING DETAILED RAG DEBUG")
    print("=" * 60)
    
    # Test 1: Session state
    session_id = test_session_state()
    if not session_id:
        print("\n❌ CRITICAL: No active sessions found!")
        print("💡 Please upload a PDF first to create a session.")
        return
    
    # Test 2: Vector search
    search_ok = test_vector_search(session_id)
    if not search_ok:
        print("\n❌ CRITICAL: Vector search failed!")
        return
    
    # Test 3: RAG pipeline
    rag_ok = test_rag_pipeline(session_id)
    if not rag_ok:
        print("\n❌ CRITICAL: RAG pipeline failed!")
        return
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ The RAG pipeline components are working correctly.")
    print("💡 If you're still getting generic responses, the issue might be:")
    print("   1. API key issues during actual LLM calls")
    print("   2. Context not being properly passed to the LLM")
    print("   3. LLM prompt formatting issues")

if __name__ == "__main__":
    main() 