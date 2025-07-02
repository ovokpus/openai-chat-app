#!/usr/bin/env python3
"""
Preprocess Knowledge Base Documents for Deployment

This script processes all knowledge base documents into text chunks and saves them
as a lightweight JSON file for efficient deployment and initialization.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Add paths for imports
sys.path.append('.')
sys.path.append('aimakerspace')

from aimakerspace.multi_document_processor import MultiDocumentProcessor

def preprocess_knowledge_base():
    """Process all knowledge base documents and save as JSON chunks"""
    print("🚀 Starting knowledge base preprocessing...")
    
    # Path to knowledge base documents
    knowledge_base_path = os.path.join("api", "services", "knowledge_base", "regulatory_docs")
    
    if not os.path.exists(knowledge_base_path):
        print(f"❌ Knowledge base path not found: {knowledge_base_path}")
        return False
    
    # Get list of supported files from organized subfolders
    supported_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.pptx', '.ppt', '.csv', '.sql', '.py', '.js', '.ts', '.md', '.txt']
    
    document_files = []
    print(f"📂 Scanning knowledge base folders...")
    
    # Scan through all regulatory document subfolders
    for subfolder in os.listdir(knowledge_base_path):
        subfolder_path = os.path.join(knowledge_base_path, subfolder)
        if os.path.isdir(subfolder_path):
            print(f"  📁 Scanning {subfolder}/")
            for file in os.listdir(subfolder_path):
                if any(file.lower().endswith(ext) for ext in supported_extensions):
                    document_files.append(os.path.join(subfolder_path, file))
                    print(f"    📄 Found: {file}")
    
    if not document_files:
        print("❌ No supported documents found in knowledge base folders")
        return False
    
    print(f"📚 Found {len(document_files)} documents to process")
    
    # Process documents using MultiDocumentProcessor with text chunking
    multi_doc_processor = MultiDocumentProcessor(enable_text_chunking=True, chunk_size=800)
    all_chunks = []
    processed_files = []
    
    for doc_path in document_files:
        try:
            filename = os.path.basename(doc_path)
            subfolder = os.path.basename(os.path.dirname(doc_path))
            print(f"📄 Processing {subfolder}/{filename}...")
            
            processed_docs = multi_doc_processor.process_document(doc_path, filename)
            
            file_chunks = 0
            for doc in processed_docs:
                chunk_data = {
                    "text": doc.content,
                    "metadata": {
                        "filename": filename,
                        "subfolder": subfolder,
                        "doc_type": doc.doc_type,
                        "source_location": doc.source_location,
                        "source": "global_kb",
                        "preprocessed_at": datetime.now().isoformat()
                    }
                }
                all_chunks.append(chunk_data)
                file_chunks += 1
            
            print(f"  ✅ Processed: {file_chunks} chunks")
            processed_files.append({
                "filename": filename,
                "subfolder": subfolder,
                "chunk_count": file_chunks,
                "doc_type": processed_docs[0].doc_type if processed_docs else "unknown"
            })
            
        except Exception as e:
            print(f"  ❌ Failed to process {doc_path}: {e}")
            continue
    
    # Create the preprocessed knowledge base data
    preprocessed_data = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_chunks": len(all_chunks),
            "total_documents": len(processed_files),
            "processed_files": processed_files,
            "version": "1.0"
        },
        "chunks": all_chunks
    }
    
    # Save to JSON file
    output_path = os.path.join("api", "services", "preprocessed_knowledge_base.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(preprocessed_data, f, ensure_ascii=False, indent=2)
    
    # Calculate file size
    file_size = os.path.getsize(output_path)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"\n🎉 Preprocessing completed successfully!")
    print(f"📊 Summary:")
    print(f"  📄 Documents processed: {len(processed_files)}")
    print(f"  📝 Total chunks created: {len(all_chunks)}")
    print(f"  💾 Output file: {output_path}")
    print(f"  📏 File size: {file_size_mb:.2f} MB")
    print(f"\n📋 Processed files by category:")
    
    # Group by subfolder
    by_subfolder = {}
    for file_info in processed_files:
        subfolder = file_info["subfolder"]
        if subfolder not in by_subfolder:
            by_subfolder[subfolder] = []
        by_subfolder[subfolder].append(file_info)
    
    for subfolder, files in by_subfolder.items():
        total_chunks = sum(f["chunk_count"] for f in files)
        print(f"  📁 {subfolder}: {len(files)} files, {total_chunks} chunks")
        for file_info in files:
            print(f"    📄 {file_info['filename']} ({file_info['doc_type']}): {file_info['chunk_count']} chunks")
    
    return True

if __name__ == "__main__":
    success = preprocess_knowledge_base()
    if success:
        print(f"\n✅ Knowledge base preprocessing completed!")
        print(f"🚀 You can now deploy with the lightweight preprocessed_knowledge_base.json file")
    else:
        print(f"\n❌ Knowledge base preprocessing failed!")
        sys.exit(1) 