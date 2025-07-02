export interface Message {
  role: 'user' | 'assistant'
  content: string
  isRag?: boolean  // Indicates if message was generated using RAG
  sourceDocuments?: string[]  // Documents used for RAG response
}

export interface ChatState {
  messages: Message[]
  input: string
  isLoading: boolean
  apiKey: string
  showApiKey: boolean
}

// New types for PDF and RAG functionality
export interface UploadResponse {
  success: boolean
  message: string
  session_id: string
  document_count: number
  filename: string
}

export interface MultiDocumentUploadResponse {
  success: boolean
  message: string
  session_id: string
  document_count: number
  filename: string
  doc_type: string
  regulatory_type: string
  chunks_created: number
}

export interface SessionInfo {
  session_id: string
  document_count: number
  documents: string[]
  created_at: string
}

export interface GlobalKnowledgeBaseInfo {
  status: 'not_initialized' | 'error' | 'ready'
  initialized: boolean
  error: string | null
  documents: string[]  // Original documents
  user_uploaded_documents: string[]  // User-uploaded documents
  document_count: number
  original_document_count: number
  user_uploaded_document_count: number
  chunk_count: number
  description: string
}

export interface PDFUploadState {
  isUploading: boolean
  uploadProgress: number
  uploadedFiles: string[]
  sessionId: string | null
  error: string | null
}

export interface RAGChatRequest {
  userMessage: string
  sessionId: string
  apiKey: string
  model?: string
  useRag?: boolean
} 