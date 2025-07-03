import { useState, useEffect } from 'react'
import { uploadDocument, sendRAGMessage, getSessionInfo, deleteSession } from '../services/chatApi'
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
      console.log('Loaded session info:', info) // Debug log
      setSessionInfo(info)
      // Ensure sessionId is always set when we have session info
      if (info && info.session_id) {
        setSessionId(info.session_id)
      }
    } catch (error) {
      console.error('Failed to load session info:', error)
      // If session not found, reset
      setSessionInfo(null)
      setSessionId(null)
    }
  }

  const handleDocumentUpload = async (file: File, apiKey: string): Promise<UploadResponse | null> => {
    setIsUploading(true)
    setUploadError(null)

    try {
      const response: UploadResponse = await uploadDocument(file, apiKey, sessionId || undefined)
      console.log('Upload response:', response) // Debug log
      
      // Update session ID first
      setSessionId(response.session_id)
      
      // Then update session info directly from response
      const updatedSessionInfo: SessionInfo = {
        session_id: response.session_id,
        document_count: response.document_count,
        documents: [response.filename], // Add the new document
        created_at: new Date().toISOString()
      }
      
      // If we already have session info, merge the documents
      if (sessionInfo) {
        updatedSessionInfo.documents = [...new Set([...sessionInfo.documents, response.filename])]
        updatedSessionInfo.created_at = sessionInfo.created_at
      }
      
      console.log('Setting session info:', updatedSessionInfo) // Debug log
      setSessionInfo(updatedSessionInfo)
      
      // Also load fresh session info from server to be sure
      setTimeout(() => loadSessionInfo(response.session_id), 100)
      
      return response
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
      setUploadError(errorMessage)
      return null
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
    // Use sessionId from sessionInfo if sessionId state is null
    const activeSessionId = sessionId || sessionInfo?.session_id
    
    console.log('SendRAGChat - sessionId:', sessionId, 'sessionInfo.session_id:', sessionInfo?.session_id, 'using:', activeSessionId)
    
    if (!activeSessionId) {
      throw new Error('No active session. Please upload a PDF first.')
    }

    const request: RAGChatRequest = {
      userMessage,
      sessionId: activeSessionId,
      apiKey,
      model,
      useRag
    }

    try {
      return await sendRAGMessage(request)
    } catch (error) {
      // If we get a session not found error, clear the invalid session
      if (error instanceof Error && error.message.includes('Session not found')) {
        console.log('Session no longer exists on server, clearing local session state')
        setSessionInfo(null)
        setSessionId(null)
        setUploadError('Your session has expired. Please upload your PDF again.')
      }
      throw error
    }
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
    const hasSession = !!(sessionInfo && sessionInfo.document_count > 0)
    const hasSessionId = !!(sessionId || sessionInfo?.session_id)
    console.log('Has active session:', hasSession, 'hasSessionId:', hasSessionId, 'sessionInfo:', sessionInfo, 'sessionId:', sessionId) // Debug log
    return hasSession && hasSessionId
  }

  const getDocumentCount = (): number => {
    return sessionInfo?.document_count || 0
  }

  const getUploadedDocuments = (): string[] => {
    return sessionInfo?.documents || []
  }

  const validateSession = async () => {
    if (!sessionId && !sessionInfo?.session_id) return false
    
    const activeSessionId = sessionId || sessionInfo?.session_id
    if (!activeSessionId) return false
    
    try {
      await getSessionInfo(activeSessionId)
      return true
    } catch (error) {
      console.log('Session validation failed, clearing local state')
      setSessionInfo(null)
      setSessionId(null)
      setUploadError('Your session has expired. Please upload your PDF again.')
      return false
    }
  }

  const refreshSessionInfo = async (id?: string) => {
    const targetId = id || sessionId
    if (targetId) {
      await loadSessionInfo(targetId)
    }
  }

  return {
    // State
    sessionInfo,
    sessionId,
    isUploading,
    uploadError,
    
    // Actions
    handleDocumentUpload,
    handlePDFUpload: handleDocumentUpload, // Legacy alias for backward compatibility
    sendRAGChat,
    clearSession,
    refreshSessionInfo,
    validateSession,
    
    // Utilities
    hasActiveSession,
    getDocumentCount,
    getUploadedDocuments,
    
    // Error handling
    clearUploadError: () => setUploadError(null)
  }
} 