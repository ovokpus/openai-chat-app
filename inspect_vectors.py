#!/usr/bin/env python3
"""
Direct inspection of vector database content
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '.')

def inspect_stored_content():
    """Inspect what's actually stored in vector database"""
    print("🔍 INSPECTING VECTOR STORAGE")
    print("=" * 50)
    
    # Try to import the session data
    try:
        # This won't work because the sessions are in the FastAPI process
        # But let's try to create a test scenario
        
        from aimakerspace.vectordatabase import VectorDatabase
        from aimakerspace.openai_utils.embedding import EmbeddingModel
        from aimakerspace.rag_pipeline import RAGPipeline
        from aimakerspace.openai_utils.chatmodel import ChatOpenAI
        from aimakerspace.text_utils import CharacterTextSplitter
        import numpy as np
        
        print("✅ Imported aimakerspace modules")
        
        # Create test instances to see how they work
        print("\n🧪 TESTING COMPONENTS")
        print("-" * 30)
        
        # Test text splitter
        text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        test_text = "AWS (Amazon Web Services) is a comprehensive cloud computing platform. It provides EC2 for virtual servers, S3 for storage, and many machine learning services."
        chunks = text_splitter.split_texts([test_text])
        
        print(f"📝 Text splitting test:")
        print(f"  Original text: {test_text}")
        print(f"  Number of chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {chunk}")
        
        # Test vector database with dummy data
        print(f"\n💾 Vector database test:")
        vector_db = VectorDatabase()
        
        # Create dummy embeddings and store chunks
        for i, chunk in enumerate(chunks):
            dummy_embedding = np.random.rand(10)  # Small dummy embedding
            metadata = {"filename": "test.pdf", "chunk_index": i}
            vector_db.insert(chunk, dummy_embedding, metadata)
            print(f"  Stored chunk {i+1}: {chunk[:50]}...")
        
        print(f"  Total vectors stored: {len(vector_db.vectors)}")
        
        # Test search
        print(f"\n🔍 Search test:")
        query_vector = np.random.rand(10)
        search_results = vector_db.search(query_vector, k=2)
        
        print(f"  Search results count: {len(search_results)}")
        for i, (key, score) in enumerate(search_results):
            print(f"  Result {i+1}:")
            print(f"    Key type: {type(key)}")
            print(f"    Key content: {key}")
            print(f"    Score: {score}")
            metadata = vector_db.get_metadata(key)
            print(f"    Metadata: {metadata}")
            print()
        
        # Test RAG pipeline formatting
        print(f"🎯 RAG pipeline formatting test:")
        formatted_results = []
        for key, score in search_results:
            formatted_results.append({
                "text": key,
                "score": score,
                "metadata": vector_db.get_metadata(key)
            })
        
        # Test format_context (create a minimal RAG pipeline)
        chat_model = ChatOpenAI(api_key="dummy")  # This will fail but that's OK
        rag_pipeline = RAGPipeline(llm=chat_model, vector_db=vector_db)
        
        context, metadata_info = rag_pipeline.format_context(formatted_results)
        print(f"  Formatted context length: {len(context)}")
        print(f"  Context content: {context}")
        print(f"  Metadata info: {metadata_info}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_stored_content() 