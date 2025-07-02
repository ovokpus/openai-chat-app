#!/usr/bin/env python3
"""
Test script to get debug information from RAG pipeline
"""

import requests
import json
import tempfile

BASE_URL = "http://localhost:8000"

def create_debug_rag_endpoint():
    """Create a temporary debug endpoint that shows what's happening"""
    
    # Get session info
    response = requests.get(f"{BASE_URL}/api/sessions")
    sessions_data = response.json()
    session_id = sessions_data["sessions"][0]["session_id"]
    
    print(f"Using session: {session_id}")
    
    # Create a custom debug request
    debug_request = f"""
import sys
import requests
import json

# Test the vector database directly through Python imports
sys.path.append('.')

try:
    from api.app import user_sessions
    
    session_id = "{session_id}"
    if session_id in user_sessions:
        session = user_sessions[session_id]
        vector_db = session['vector_db']
        
        print("=== VECTOR DATABASE DEBUG ===")
        print(f"Vector count: {{len(vector_db.vectors)}}")
        print(f"Has embedding model: {{hasattr(vector_db, 'embedding_model') and vector_db.embedding_model is not None}}")
        
        # Check sample vectors
        print("\\n=== SAMPLE VECTORS ===")
        for i, (key, vector) in enumerate(list(vector_db.vectors.items())[:3]):
            print(f"Vector {{i+1}}:")
            print(f"  Key type: {{type(key)}}")
            print(f"  Key length: {{len(str(key))}}")
            print(f"  Key preview: {{str(key)[:200]}}...")
            print(f"  Vector shape: {{vector.shape if hasattr(vector, 'shape') else 'No shape'}}")
            
            # Check metadata
            metadata = vector_db.get_metadata(key)
            print(f"  Metadata: {{metadata}}")
            print()
            
        # Test search
        if vector_db.embedding_model:
            print("\\n=== TESTING SEARCH ===")
            try:
                import numpy as np
                query_vector = vector_db.embedding_model.get_embedding("What is AWS?")
                search_results = vector_db.search(np.array(query_vector), k=2)
                
                print(f"Search results count: {{len(search_results)}}")
                for i, (key, score) in enumerate(search_results):
                    print(f"Result {{i+1}}:")
                    print(f"  Score: {{score}}")
                    print(f"  Key type: {{type(key)}}")
                    print(f"  Key preview: {{str(key)[:150]}}...")
                    print()
            except Exception as e:
                print(f"Search failed: {{e}}")
                import traceback
                traceback.print_exc()
        
    else:
        print(f"Session {{session_id}} not found!")
        print(f"Available sessions: {{list(user_sessions.keys())}}")
        
except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
"""
    
    # Write to temporary file and execute
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(debug_request)
        temp_file = f.name
    
    print(f"Created debug script: {temp_file}")
    return temp_file

def main():
    print("🚀 CREATING DEBUG INSPECTION")
    print("=" * 50)
    
    debug_file = create_debug_rag_endpoint()
    print(f"Debug file created: {debug_file}")
    
    print("\nTo debug, run:")
    print(f"python {debug_file}")

if __name__ == "__main__":
    main() 