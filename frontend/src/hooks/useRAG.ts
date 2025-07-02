import { useState, useEffect } from 'react'
import { uploadPDF, sendRAGMessage, getSessionInfo, deleteSession } from '../services/chatApi'
import type { UploadResponse, SessionInfo, RAGChatRequest } from '../types'

export const useRAG = () => {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // Load session info when sessionId changes
  useEffect(() => {
    if (sessionId) {
      loadSessionInfo(sessionId)
    }
  }, [sessionId])

  const loadSessionInfo = async (id: string) => {
    try {
      const info = await getSessionInfo(id)
      setSessionInfo(info)
    } catch (error) {
      console.error('Failed to load session info:', error)
      // If session not found, reset
      setSessionInfo(null)
      setSessionId(null)
    }
  }

  const handlePDFUpload = async (file: File, apiKey: string): Promise<boolean> => {
    setIsUploading(true)
    setUploadError(null)

    try {
      const response: UploadResponse = await uploadPDF(file, apiKey, sessionId || undefined)
      
      // Update session info
      setSessionId(response.session_id)
      await loadSessionInfo(response.session_id)
      
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
      setUploadError(errorMessage)
      return false
    } finally {
      setIsUploading(false)
    }
  }

  const sendRAGChat = async (
    userMessage: string,
    apiKey: string,
    model?: string,
    useRag: boolean = true
  ): Promise<ReadableStreamDefaultReader<Uint8Array> | null> => {
    if (!sessionId) {
      throw new Error('No active session. Please upload a PDF first.')
    }

    const request: RAGChatRequest = {
      userMessage,
      sessionId,
      apiKey,
      model,
      useRag
    }

    return sendRAGMessage(request)
  }

  const clearSession = async () => {
    if (sessionId) {
      try {
        await deleteSession(sessionId)
      } catch (error) {
        console.error('Failed to delete session:', error)
      }
    }
    
    // Reset local state
    setSessionInfo(null)
    setSessionId(null)
    setUploadError(null)
  }

  const hasActiveSession = (): boolean => {
    return !!(sessionInfo && sessionInfo.document_count > 0)
  }

  const getDocumentCount = (): number => {
    return sessionInfo?.document_count || 0
  }

  const getUploadedDocuments = (): string[] => {
    return sessionInfo?.documents || []
  }

  return {
    // State
    sessionInfo,
    sessionId,
    isUploading,
    uploadError,
    
    // Actions
    handlePDFUpload,
    sendRAGChat,
    clearSession,
    
    // Utilities
    hasActiveSession,
    getDocumentCount,
    getUploadedDocuments,
    
    // Error handling
    clearUploadError: () => setUploadError(null)
  }
} 