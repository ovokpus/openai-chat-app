#!/usr/bin/env python3
"""
Multi-Format RAG System Debug Script
This script tests the RAG system with various file formats from the regulatory reporting documents.
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
import pandas as pd

# Add the current directory to Python path
sys.path.insert(0, '.')

# Import our file processing utilities
from aimakerspace.file_utils import UniversalFileProcessor
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.rag_pipeline import RAGPipeline
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.text_utils import CharacterTextSplitter

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

def test_file_processing(file_path):
    """Test processing of a single file"""
    try:
        print(f"\n📄 Testing file: {file_path}")
        processor = UniversalFileProcessor(file_path)
        
        # Process the file
        start_time = time.time()
        text_content = processor.load_documents()
        processing_time = time.time() - start_time
        
        # Join multiple documents if any
        text_content = "\n\n".join(text_content) if isinstance(text_content, list) else text_content
        
        # Calculate stats
        char_count = len(text_content)
        word_count = len(text_content.split())
        line_count = len(text_content.splitlines())
        
        print(f"✅ Successfully processed {Path(file_path).name}")
        print(f"📊 Stats:")
        print(f"  - Processing time: {processing_time:.2f} seconds")
        print(f"  - Characters: {char_count}")
        print(f"  - Words: {word_count}")
        print(f"  - Lines: {line_count}")
        
        # Preview first 200 characters
        preview = text_content[:200].replace('\n', ' ').strip()
        print(f"📝 Preview: {preview}...")
        
        return text_content
        
    except Exception as e:
        print(f"❌ Failed to process {Path(file_path).name}: {str(e)}")
        return None

def test_rag_pipeline(texts, api_key):
    """Test RAG pipeline with processed texts"""
    try:
        print("\n🔄 Testing RAG Pipeline...")
        
        # Initialize components
        embedding_model = EmbeddingModel(api_key=api_key)
        vector_db = VectorDatabase(embedding_model=embedding_model)
        chat_model = ChatOpenAI(api_key=api_key)
        rag_pipeline = RAGPipeline(llm=chat_model, vector_db=vector_db)
        
        # Create text splitter for chunking
        text_splitter = CharacterTextSplitter(
            chunk_size=2000,  # Smaller chunks to fit in context window
            chunk_overlap=200  # Overlap to maintain context between chunks
        )
        
        # Add texts to vector database
        print("💾 Adding documents to vector database...")
        total_chunks = 0
        for text in texts:
            if text:  # Only process non-None texts
                # Split text into chunks
                chunks = text_splitter.split_texts([text])
                print(f"  - Split into {len(chunks)} chunks")
                total_chunks += len(chunks)
                
                # Process each chunk
                for i, chunk in enumerate(chunks):
                    # Get embedding and insert into vector database
                    embedding = embedding_model.get_embedding(chunk)
                    vector_db.insert(
                        chunk, 
                        embedding, 
                        {
                            "source": "regulatory_docs",
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
        
        print(f"✅ Added {total_chunks} chunks from {len([t for t in texts if t])} documents to vector database")
        
        # Test queries
        test_queries = [
            "What are the key requirements in Basel III?",
            "How is data lineage tracked in the regulatory reporting process?",
            "What are the main FINREP templates we use?"
        ]
        
        print("\n🔍 Testing queries...")
        for query in test_queries:
            print(f"\nQuery: {query}")
            try:
                result = rag_pipeline.run(query)
                print(f"Response: {result['response'][:500]}...")
                print(f"Sources: {result['metadata']['sources']}")
                print(f"Chunks used: {result['metadata']['num_chunks']}")
            except Exception as e:
                print(f"❌ Query failed: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG pipeline test failed: {str(e)}")
        return False

def main():
    """Run all tests with regulatory reporting documents"""
    print("🚀 Starting Multi-Format RAG System Debug...\n")
    
    # Check backend health
    print("=" * 50)
    print("TEST 1: Backend Health")
    print("=" * 50)
    if not test_backend_health():
        print("❌ Backend is not running. Please start the backend first.")
        return
    
    # Test file processing
    print("\n" + "=" * 50)
    print("TEST 2: Multi-Format File Processing")
    print("=" * 50)
    
    # Define test files
    test_files = [
        "regulatory_reporting/documents/Basel_III_Implementation_Policy.md",
        "regulatory_reporting/documents/data_lineage_sample.csv",
        "regulatory_reporting/documents/FINREP_IFRS_templates_Annex_III.xlsx",
        "regulatory_reporting/documents/Basel_III_Finalising_post-crisis_reforms.pdf",
        "regulatory_reporting/documents/SQL_Data_Lineage_Sample.sql",
        "regulatory_reporting/documents/Regulatory_Steering_Committee_Presentation.txt"
    ]
    
    # Process each file
    processed_texts = []
    for file_path in test_files:
        if os.path.exists(file_path):
            text = test_file_processing(file_path)
            processed_texts.append(text)
        else:
            print(f"❌ File not found: {file_path}")
    
    # Test RAG pipeline if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("\n" + "=" * 50)
        print("TEST 3: RAG Pipeline with Processed Documents")
        print("=" * 50)
        test_rag_pipeline(processed_texts, api_key)
    else:
        print("\n⚠️  Skipping RAG pipeline test - OPENAI_API_KEY not found")
    
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")
    print("=" * 50)
    print("Summary:")
    print("- Backend health: Check if running on http://localhost:8000")
    print("- File processing: Tested multiple file formats")
    print("- RAG pipeline: Tested with processed documents (if API key available)")
    print("\nTo test with OpenAI API:")
    print("export OPENAI_API_KEY='your-api-key'")

if __name__ == "__main__":
    main() 