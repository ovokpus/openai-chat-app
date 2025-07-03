import logging
from typing import List, Dict, Any, Tuple, Optional
from .vectordatabase import VectorDatabase
from .openai_utils.chatmodel import ChatOpenAI
from .openai_utils.prompts import SystemRolePrompt, UserRolePrompt

class RAGPipeline:
    """
    A pipeline for Retrieval-Augmented Generation (RAG) that combines 
    document retrieval with language model generation.
    """
    
    def __init__(
        self, 
        llm: ChatOpenAI,
        vector_db: VectorDatabase,
        response_style: str = "concise"
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            llm: The language model for generation
            vector_db: The vector database for retrieval
            response_style: Style of responses ("concise" or "detailed")
        """
        self.llm = llm
        self.vector_db = vector_db
        self.response_style = response_style
        
        # System prompt for RAG responses
        self.system_prompt = SystemRolePrompt("""You are a helpful assistant that answers questions based on provided document context. 

When answering:
1. Use ONLY the information provided in the context
2. If the context doesn't contain relevant information, clearly state that
3. Cite specific parts of the context when possible
4. Be accurate and don't make assumptions beyond the provided context
5. Format your response clearly with proper markdown

Context format: Each piece of context will be marked with [Source: filename] followed by the content.""")

    def search_documents(
        self, 
        query: str, 
        k: int = 4, 
        return_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using vector similarity.
        
        Args:
            query: The search query
            k: Number of top results to return
            return_metadata: Whether to include metadata in results
            
        Returns:
            List of search results with content and metadata
        """
        try:
            print(f"🔍 RAG DEBUG: Searching for query: {query}")
            
            # Get query embedding
            query_vector = self.vector_db.embedding_model.get_embedding(query)
            print(f"🔍 RAG DEBUG: Generated query embedding, shape: {len(query_vector)}")
            
            # Use the vector database's search method
            search_results = self.vector_db.search(query_vector, k=k)
            print(f"🔍 RAG DEBUG: Raw search results count: {len(search_results)}")
            
            formatted_results = []
            for i, (key, score) in enumerate(search_results):
                print(f"🔍 RAG DEBUG: Result {i+1}:")
                print(f"  - Score: {score}")
                print(f"  - Key type: {type(key)}")
                print(f"  - Key preview: {str(key)[:200]}...")
                
                formatted_result = {
                    "text": key,  # The key is the text content
                    "score": score
                }
                
                if return_metadata:
                    metadata = self.vector_db.get_metadata(key)
                    if metadata:
                        formatted_result["metadata"] = metadata
                        print(f"  - Metadata: {metadata}")
                
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logging.error(f"Error searching documents: {e}")
            return []

    def format_context(
        self, 
        search_results: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Format search results into context for the language model.
        
        Args:
            search_results: List of search results
            
        Returns:
            Tuple of (formatted_context, metadata_info)
        """
        print(f"📝 RAG DEBUG: Formatting context from {len(search_results)} results")
        
        if not search_results:
            return "", ""
        
        context_parts = []
        metadata_parts = []
        
        for i, result in enumerate(search_results):
            content = result.get("text", "").strip()
            metadata = result.get("metadata", {})
            score = result.get("score", 0.0)
            
            print(f"📝 RAG DEBUG: Processing result {i+1}:")
            print(f"  - Content type: {type(content)}")
            print(f"  - Content length: {len(content)}")
            print(f"  - Content preview: {content[:100]}...")
            
            if content:
                # Format with source information
                filename = metadata.get("filename", f"Document {i+1}")
                context_parts.append(f"[Source: {filename}]\n{content}")
                
                # Collect metadata info
                metadata_info = f"Source: {filename}, Relevance: {score:.3f}"
                if "chunk_index" in metadata:
                    metadata_info += f", Chunk: {metadata['chunk_index']}"
                metadata_parts.append(metadata_info)
        
        formatted_context = "\n\n---\n\n".join(context_parts)
        metadata_info = " | ".join(metadata_parts)
        
        print(f"📝 RAG DEBUG: Final context length: {len(formatted_context)}")
        print(f"📝 RAG DEBUG: Final context preview: {formatted_context[:300]}...")
        
        return formatted_context, metadata_info

    def generate_response(
        self, 
        query: str, 
        context: str, 
        metadata_info: str = ""
    ) -> str:
        """
        Generate a response using the language model with provided context.
        
        Args:
            query: The user's question
            context: The relevant document context
            metadata_info: Information about the sources
            
        Returns:
            The generated response
        """
        try:
            # Create the user prompt with context
            user_prompt_text = f"""Question: {query}

Context from documents:
{context}

Please answer the question based on the provided context."""

            user_prompt = UserRolePrompt(user_prompt_text)
            
            # Generate response using the chat model
            messages = [self.system_prompt, user_prompt]
            response = self.llm.run(messages)
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"I encountered an error while generating a response: {str(e)}"

    def run(
        self, 
        query: str, 
        k: int = 4
    ) -> Dict[str, Any]:
        """
        Run the complete RAG pipeline: search, format, and generate.
        
        Args:
            query: The user's question
            k: Number of documents to retrieve
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Search for relevant documents
            search_results = self.search_documents(query, k=k)
            
            # Format context
            context, metadata_info = self.format_context(search_results)
            
            # Generate response
            response = self.generate_response(query, context, metadata_info)
            
            # Return response with metadata
            return {
                "response": response,
                "metadata": {
                    "query": query,
                    "num_chunks": len(search_results),
                    "sources": metadata_info
                }
            }
            
        except Exception as e:
            logging.error(f"Error in RAG pipeline: {e}")
            return {
                "response": f"I encountered an error while processing your query: {str(e)}",
                "metadata": {
                    "error": str(e),
                    "query": query
                }
            } 