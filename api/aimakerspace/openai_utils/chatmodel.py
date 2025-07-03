import logging
from openai import OpenAI
from typing import List, Optional
import os
from dotenv import load_dotenv

class ChatOpenAI:
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        load_dotenv()
        
        # Use provided API key or fallback to environment variable
        if api_key:
            self.openai_api_key = api_key
        else:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.openai_api_key is None:
            raise ValueError(
                "OpenAI API key must be provided either as a parameter or through OPENAI_API_KEY environment variable."
            )
        
        self.model_name = model_name
        self.client = OpenAI(api_key=self.openai_api_key)

    def run(self, messages, text_only: bool = True, **kwargs):
        """
        Run the chat model with the given messages.
        
        Args:
            messages: List of message objects or prompts
            text_only: Whether to return only the text content
            **kwargs: Additional arguments for the chat completion
            
        Returns:
            String response if text_only=True, otherwise full response object
        """
        try:
            # Convert messages to the format expected by OpenAI
            formatted_messages = []
            for message in messages:
                if hasattr(message, 'create_message'):
                    # RolePrompt object with create_message method
                    formatted_messages.append(message.create_message())
                elif hasattr(message, 'role') and hasattr(message, 'prompt'):
                    # RolePrompt object without using create_message
                    formatted_messages.append({
                        "role": message.role,
                        "content": message.prompt
                    })
                elif hasattr(message, 'role') and hasattr(message, 'content'):
                    # Message object with role and content attributes
                    formatted_messages.append({
                        "role": message.role,
                        "content": message.content
                    })
                elif isinstance(message, dict):
                    # Already in dict format
                    formatted_messages.append(message)
                else:
                    # Assume it's a string and treat as user message
                    formatted_messages.append({
                        "role": "user",
                        "content": str(message)
                    })
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                **kwargs
            )
            
            if text_only:
                return response.choices[0].message.content
            else:
                return response
                
        except Exception as e:
            logging.error(f"Error in ChatOpenAI.run: {e}")
            raise
