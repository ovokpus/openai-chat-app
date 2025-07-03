// API Configuration
export const API_ENDPOINTS = {
  UPLOAD: '/api/upload-document',
  RAG_CHAT: '/api/rag-chat',
  DELETE_DOCUMENT: '/api/documents',
  SESSION_INFO: '/api/session',
  HEALTH: '/api/health',
  CHAT: '/api/chat'
} as const;

// Chat Configuration
export const CHAT_CONFIG = {
  DEFAULT_MODEL: 'gpt-4o-mini',
  SESSION_TIMEOUT: 60 * 60 * 1000, // 1 hour in milliseconds
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000 // 1 second
} as const;

// UI Configuration
export const UI_CONFIG = {
  DOCUMENT_TYPES: {
    PDF: 'application/pdf',
    DOCX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    TXT: 'text/plain',
    MD: 'text/markdown',
    CSV: 'text/csv'
  },
  MAX_FILENAME_LENGTH: 30,
  TOAST_DURATION: 5000, // 5 seconds
  ANIMATION_DURATION: 300 // 300ms
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  UPLOAD_FAILED: 'Failed to upload document. Please try again.',
  SESSION_EXPIRED: 'Your session has expired. Please upload your document again.',
  DELETE_FAILED: 'Failed to delete document. Please try again.',
  NETWORK_ERROR: 'Network error. Please check your connection.',
  INVALID_API_KEY: 'Invalid API key. Please check your credentials.'
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  UPLOAD_SUCCESS: 'Document uploaded successfully!',
  DELETE_SUCCESS: 'Document deleted successfully!',
  CLEAR_SUCCESS: 'All documents cleared successfully!'
} as const; 