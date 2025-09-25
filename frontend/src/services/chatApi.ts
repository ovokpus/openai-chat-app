import { API_ENDPOINTS, CHAT_CONFIG } from '../constants';
import type { Message, UploadResponse, SessionInfo, RAGChatRequest } from '../types'

const DEVELOPER_MESSAGE = `You are a helpful AI assistant. When providing responses:

FORMATTING RULES:
- Use proper markdown formatting for all text
- For mathematical expressions, ALWAYS use standard markdown math delimiters:
  - Inline math: $expression$ 
  - Display math: $$expression$$
- NEVER use brackets [ ] or parentheses ( ) around math expressions
- NEVER use \\[ \\] LaTeX delimiters
- Use **bold** for emphasis and *italics* when needed
- Use numbered lists (1. 2. 3.) and bullet points (- item) properly
- Use ### for headings when structuring responses

MATH EXAMPLES:
✅ CORRECT: The formula is $$\\frac{12}{4} = 3$$
❌ WRONG: The formula is [\\frac{12}{4} = 3]
❌ WRONG: The formula is (\\frac{12}{4} = 3)

Always format mathematical calculations using proper markdown math syntax with $$ delimiters.`

export interface ChatRequest {
  userMessage: string
  apiKey: string
  model?: string
}

export const sendChatMessage = async (
  { userMessage, apiKey, model = "gpt-4o-mini" }: ChatRequest
): Promise<ReadableStreamDefaultReader<Uint8Array> | null> => {
  const response = await fetch(API_ENDPOINTS.CHAT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_message: userMessage,
      developer_message: DEVELOPER_MESSAGE,
      api_key: apiKey,
      model
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return response.body?.getReader() || null
}

export const uploadDocument = async (
  file: File,
  apiKey: string,
  sessionId?: string
): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('api_key', apiKey)
  if (sessionId) {
    formData.append('session_id', sessionId)
  }

  const response = await fetch(API_ENDPOINTS.UPLOAD, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

// Legacy function for backward compatibility
export const uploadPDF = async (
  file: File,
  apiKey: string,
  sessionId?: string
): Promise<UploadResponse> => {
  return uploadDocument(file, apiKey, sessionId)
}

export const sendRAGMessage = async (
  request: RAGChatRequest
): Promise<ReadableStreamDefaultReader<Uint8Array> | null> => {
  const requestBody = {
    user_message: request.userMessage,
    session_id: request.sessionId,
    api_key: request.apiKey,
    model: request.model || CHAT_CONFIG.DEFAULT_MODEL,
    use_rag: request.useRag !== false
  }
  
  console.log('Sending RAG request:', requestBody) // Debug log
  
  const response = await fetch(API_ENDPOINTS.RAG_CHAT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  })

  if (!response.ok) {
    const errorText = await response.text()
    console.error('RAG request failed:', response.status, errorText) // Debug log
    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
  }

  return response.body?.getReader() || null
}

export const getSessionInfo = async (sessionId: string): Promise<SessionInfo> => {
  const response = await fetch(`${API_ENDPOINTS.SESSION_INFO}/${sessionId}`)
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return response.json()
}

export const deleteSession = async (sessionId: string): Promise<void> => {
  const response = await fetch(`${API_ENDPOINTS.SESSION_INFO}/${sessionId}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
}

export const deleteDocument = async (
  sessionId: string,
  documentName: string,
  apiKey: string
): Promise<{
  success: boolean;
  message: string;
  remaining_documents?: string[];
  document_count?: number;
}> => {
  const response = await fetch(`${API_ENDPOINTS.DELETE_DOCUMENT}/${sessionId}/${encodeURIComponent(documentName)}?api_key=${apiKey}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}; 