import type { Message, UploadResponse, SessionInfo, RAGChatRequest, MultiDocumentUploadResponse } from '../types'

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
  const response = await fetch('/api/chat', {
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

export const uploadPDF = async (
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

  const response = await fetch('/api/upload-pdf', {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

export const uploadDocument = async (
  file: File,
  apiKey: string,
  sessionId?: string
): Promise<MultiDocumentUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('api_key', apiKey)
  if (sessionId) {
    formData.append('session_id', sessionId)
  }

  const response = await fetch('/api/upload-document', {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

export const sendRAGMessage = async (
  request: RAGChatRequest
): Promise<ReadableStreamDefaultReader<Uint8Array> | null> => {
  const requestBody = {
    user_message: request.userMessage,
    session_id: request.sessionId,
    api_key: request.apiKey,
    model: request.model || "gpt-4o-mini",
    use_rag: request.useRag !== false
  }
  
  console.log('Sending RAG request:', requestBody) // Debug log
  
  const response = await fetch('/api/rag-chat', {
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
  const response = await fetch(`/api/session/${sessionId}`)
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return response.json()
}

export const deleteSession = async (sessionId: string): Promise<void> => {
  const response = await fetch(`/api/session/${sessionId}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
} 