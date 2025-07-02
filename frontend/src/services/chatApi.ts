import type { Message, UploadResponse, SessionInfo, RAGChatRequest, MultiDocumentUploadResponse, GlobalKnowledgeBaseInfo } from '../types'
import { logger, logApiRequest } from '../utils/logger'

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

/**
 * Uploads a document to the knowledge base (supports multiple file formats)
 * @deprecated Use uploadDocument instead for better multi-format support
 */
export const uploadFile = async (
  file: File,
  apiKey: string,
  sessionId?: string
): Promise<UploadResponse> => {
  logger.warn('uploadFile is deprecated. Use uploadDocument instead for enhanced multi-format support.')
  
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

/**
 * Uploads a document to the knowledge base with comprehensive format support
 * Supports: PDF, Word, Excel, PowerPoint, CSV, SQL, Python, JavaScript, TypeScript, Markdown, and Text files
 * @param file - The file to upload (max 10MB)
 * @param apiKey - OpenAI API key for processing
 * @param sessionId - Optional session ID for document management
 * @returns Promise with upload response containing document metadata
 */
export const uploadDocumentToKnowledgeBase = async (
  file: File,
  apiKey: string,
  sessionId?: string
): Promise<MultiDocumentUploadResponse> => {
  logger.debug('Initiating document upload to knowledge base', {
    fileName: file.name,
    fileSize: file.size,
    fileType: file.type,
    sessionId
  })

  const documentFormData = new FormData()
  documentFormData.append('file', file)
  documentFormData.append('api_key', apiKey)
  if (sessionId) {
    documentFormData.append('session_id', sessionId)
  }

  const uploadResponse = await fetch('/api/upload-document', {
    method: 'POST',
    body: documentFormData
  })

  if (!uploadResponse.ok) {
    const errorDetails = await uploadResponse.json()
    logger.error('Document upload failed', {
      status: uploadResponse.status,
      error: errorDetails
    })
    throw new Error(errorDetails.detail || `Document upload failed with status: ${uploadResponse.status}`)
  }

  const responseData = await uploadResponse.json()
  logger.info('Document successfully uploaded to knowledge base', responseData)
  
  return responseData
}

// Backward compatibility alias
export const uploadDocument = uploadDocumentToKnowledgeBase

/**
 * Sends a message using Retrieval-Augmented Generation (RAG) with uploaded documents
 * @param request - RAG chat request containing user message and session information
 * @returns Promise with readable stream for streaming response, or null if no stream available
 */
export const sendRAGEnhancedMessage = async (
  request: RAGChatRequest
): Promise<ReadableStreamDefaultReader<Uint8Array> | null> => {
  const ragRequestBody = {
    user_message: request.userMessage,
    session_id: request.sessionId,
    api_key: request.apiKey,
    model: request.model || "gpt-4o-mini",
    use_rag: request.useRag !== false
  }
  
  logger.debug('Sending RAG-enhanced message request', {
    sessionId: request.sessionId,
    model: request.model,
    useRag: request.useRag,
    messageLength: request.userMessage.length
  })
  
  logApiRequest('/api/rag-chat', ragRequestBody)
  
  const ragResponse = await fetch('/api/rag-chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(ragRequestBody)
  })

  if (!ragResponse.ok) {
    const errorDetails = await ragResponse.text()
    logger.error('RAG-enhanced message request failed', {
      status: ragResponse.status,
      error: errorDetails
    })
    throw new Error(`RAG request failed with status: ${ragResponse.status} - ${errorDetails}`)
  }

  logger.info('RAG-enhanced message request successful, starting stream')
  return ragResponse.body?.getReader() || null
}

// Backward compatibility alias
export const sendRAGMessage = sendRAGEnhancedMessage

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

// Global Knowledge Base API functions
export const getGlobalKnowledgeBase = async (): Promise<GlobalKnowledgeBaseInfo> => {
  const response = await fetch('/api/global-knowledge-base')
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return response.json()
}

/**
 * Removes a document from the global knowledge base
 * @param filename - Name of the document to remove
 * @param apiKey - OpenAI API key for authentication
 * @returns Promise that resolves when document is successfully deleted
 */
export const removeDocumentFromKnowledgeBase = async (filename: string, apiKey: string): Promise<void> => {
  logger.debug('Attempting to remove document from knowledge base', { filename })
  
  const deleteResponse = await fetch(
    `/api/document/${encodeURIComponent(filename)}?api_key=${encodeURIComponent(apiKey)}`, 
    {
      method: 'DELETE'
    }
  )
  
  if (!deleteResponse.ok) {
    const errorDetails = await deleteResponse.json()
    logger.error('Failed to remove document from knowledge base', {
      filename,
      status: deleteResponse.status,
      error: errorDetails
    })
    throw new Error(errorDetails.detail || `Failed to delete document with status: ${deleteResponse.status}`)
  }

  logger.info('Document successfully removed from knowledge base', { filename })
}

// Backward compatibility alias
export const deleteDocument = removeDocumentFromKnowledgeBase 