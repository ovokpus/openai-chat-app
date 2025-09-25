import { API_ENDPOINTS, CHAT_CONFIG } from '../../constants';
import type { RAGChatRequest } from '../../types';

export const sendRAGMessage = async (request: RAGChatRequest): Promise<ReadableStreamDefaultReader<Uint8Array> | null> => {
  const response = await fetch(API_ENDPOINTS.RAG_CHAT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('No response body received');
  }

  return response.body.getReader();
}; 