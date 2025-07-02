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

  const handlePDFUpload = async (file: File, apiKey: string): Promise<UploadResponse | null> => {
    setIsUploading(true)
    setUploadError(null)

    try {
      const response: UploadResponse = await uploadPDF(file, apiKey, sessionId || undefined)
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
    let activeSessionId = sessionId || sessionInfo?.session_id
    
    console.log('SendRAGChat - sessionId:', sessionId, 'sessionInfo.session_id:', sessionInfo?.session_id, 'using:', activeSessionId)
    
    // If no session exists, generate a temporary one for global knowledge base access
    if (!activeSessionId) {
      console.log('No active session, generating temporary session for global knowledge base access')
      activeSessionId = `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      console.log('Generated temporary session ID:', activeSessionId)
    }

    const request: RAGChatRequest = {
      userMessage,
      sessionId: activeSessionId,
      apiKey,
      model,
      useRag
    }

    try {
      const response = await sendRAGMessage(request)
      
      // If we used a temporary session and got a successful response, 
      // check if the backend created a real session for us
      if (!sessionId && !sessionInfo && activeSessionId.startsWith('temp-')) {
        console.log('Checking if backend created a session for temporary session')
        try {
          // Try to get session info for the temporary session
          const newSessionInfo = await getSessionInfo(activeSessionId)
          if (newSessionInfo) {
            console.log('Backend created session for us:', newSessionInfo)
            setSessionId(activeSessionId)
            setSessionInfo(newSessionInfo)
          }
        } catch (error) {
          // Session might not exist on backend, that's ok for global KB access
          console.log('Temporary session not found on backend, using global knowledge base')
        }
      }
      
      return response
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

  const hasActiveSession = (globalKBReady: boolean = false): boolean => {
    const hasSession = !!(sessionInfo && sessionInfo.document_count > 0)
    const hasSessionId = !!(sessionId || sessionInfo?.session_id)
    console.log('Has active session:', hasSession, 'hasSessionId:', hasSessionId, 'globalKBReady:', globalKBReady, 'sessionInfo:', sessionInfo, 'sessionId:', sessionId) // Debug log
    
    // Return true if user has uploaded documents OR if global knowledge base is ready
    return (hasSession && hasSessionId) || globalKBReady
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
    handlePDFUpload,
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