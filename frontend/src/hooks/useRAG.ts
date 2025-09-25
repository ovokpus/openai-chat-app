import { useState, useEffect } from 'react'
import { uploadDocument, sendRAGMessage, getSessionInfo, deleteSession } from '../services/chatApi'
import { 
  saveSessionBackup, 
  getSessionBackup, 
  clearSessionBackup, 
  getBackupDocuments,
  isSessionBackupAvailable 
} from '../services/session/sessionService'
import type { UploadResponse, SessionInfo, RAGChatRequest } from '../types'

export const useRAG = () => {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isUsingBackup, setIsUsingBackup] = useState(false)
  const [isLoadingSession, setIsLoadingSession] = useState(false)

  // Load session info when sessionId changes
  useEffect(() => {
    if (sessionId && !isLoadingSession) {
      loadSessionInfo(sessionId)
    }
  }, [sessionId])

  // Try to restore from backup on component mount
  useEffect(() => {
    const restoreFromBackup = () => {
      if (!sessionInfo && !sessionId && isSessionBackupAvailable()) {
        const backup = getSessionBackup()
        if (backup) {
          console.log('🔄 Attempting to restore session from backup')
          setSessionInfo(backup)
          setSessionId(backup.session_id)
          setIsUsingBackup(true)
          setUploadError(`Session restored from backup. ${backup.documents.length} document(s) were previously uploaded. Try asking a question - if it fails, please re-upload your documents.`)
        }
      }
    }

    restoreFromBackup()
  }, [sessionInfo, sessionId])

  const loadSessionInfo = async (id: string) => {
    // Prevent multiple simultaneous calls
    if (isLoadingSession) return;
    
    setIsLoadingSession(true);
    try {
      const info = await getSessionInfo(id)
      console.log('Loaded session info:', info) // Debug log
      setSessionInfo(info)
      setIsUsingBackup(false)
      
      // Save successful session to backup
      saveSessionBackup(info)
      
      // Ensure sessionId is always set when we have session info
      if (info && info.session_id) {
        setSessionId(info.session_id)
      }
    } catch (error) {
      console.error('Failed to load session info:', error)
      
      // Try to restore from backup if available
      const backup = getSessionBackup()
      if (backup && backup.session_id === id) {
        console.log('🔄 Server session lost, using backup')
        setSessionInfo(backup)
        setIsUsingBackup(true)
        setUploadError(`Server session expired but backup recovered. ${backup.documents.length} document(s) in backup. Re-upload if RAG chat fails.`)
      } else {
        // If session not found and no backup, reset
        setSessionInfo(null)
        setSessionId(null)
        setIsUsingBackup(false)
      }
    } finally {
      setIsLoadingSession(false);
    }
  }

  const handleDocumentUpload = async (file: File, apiKey: string): Promise<UploadResponse | null> => {
    setIsUploading(true)
    setUploadError(null)
    setIsUsingBackup(false)

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
      
      // Save to backup immediately
      saveSessionBackup(updatedSessionInfo, updatedSessionInfo.documents)
      
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
    
    console.log('SendRAGChat - sessionId:', sessionId, 'sessionInfo.session_id:', sessionInfo?.session_id, 'using:', activeSessionId, 'isUsingBackup:', isUsingBackup)
    
    if (!activeSessionId) {
      throw new Error('No active session. Please upload a document first.')
    }

    const request: RAGChatRequest = {
      userMessage,
      sessionId: activeSessionId,
      apiKey,
      model,
      useRag
    }

    try {
      const result = await sendRAGMessage(request)
      // If successful and we were using backup, we're now synced
      if (isUsingBackup) {
        setIsUsingBackup(false)
        setUploadError(null)
      }
      return result
    } catch (error) {
      // If we get a session not found error, clear the invalid session
      if (error instanceof Error && error.message.includes('Session not found')) {
        console.log('Session no longer exists on server')
        
        const backup = getSessionBackup()
        if (backup && !isUsingBackup) {
          // Try to use backup information
          setSessionInfo(backup)
          setIsUsingBackup(true)
          setUploadError(`Server session lost. Backup available with ${backup.documents.length} document(s). Please re-upload to restore RAG functionality.`)
        } else {
          // No backup or already using backup
          setSessionInfo(null)
          setSessionId(null)
          setIsUsingBackup(false)
          setUploadError('Your session has expired. Please upload your documents again.')
        }
      }
      throw error
    }
  }

  const clearSession = async () => {
    if (sessionId && !isUsingBackup) {
      try {
        await deleteSession(sessionId)
      } catch (error) {
        console.error('Failed to delete session:', error)
      }
    }
    
    // Reset local state and clear backup
    setSessionInfo(null)
    setSessionId(null)
    setUploadError(null)
    setIsUsingBackup(false)
    clearSessionBackup()
  }

  const hasActiveSession = (): boolean => {
    const hasSession = !!(sessionInfo && sessionInfo.document_count > 0)
    const hasSessionId = !!(sessionId || sessionInfo?.session_id)
    console.log('Has active session:', hasSession, 'hasSessionId:', hasSessionId, 'sessionInfo:', sessionInfo, 'sessionId:', sessionId, 'isUsingBackup:', isUsingBackup) // Debug log
    return hasSession && hasSessionId
  }

  const getDocumentCount = (): number => {
    return sessionInfo?.document_count || 0
  }

  const getUploadedDocuments = (): string[] => {
    if (isUsingBackup) {
      // For backup sessions, get documents from localStorage
      return getBackupDocuments()
    }
    return sessionInfo?.documents || []
  }

  const validateSession = async () => {
    if (!sessionId && !sessionInfo?.session_id) {
      // Try to restore from backup
      const backup = getSessionBackup()
      if (backup) {
        setSessionInfo(backup)
        setSessionId(backup.session_id)
        setIsUsingBackup(true)
        return true
      }
      return false
    }
    
    const activeSessionId = sessionId || sessionInfo?.session_id
    if (!activeSessionId) return false
    
    try {
      const info = await getSessionInfo(activeSessionId)
      // Session exists on server, update our info and backup
      setSessionInfo(info)
      setIsUsingBackup(false)
      saveSessionBackup(info)
      return true
    } catch (error) {
      console.log('Session validation failed, trying backup')
      
      const backup = getSessionBackup()
      if (backup) {
        setSessionInfo(backup)
        setIsUsingBackup(true)
        setUploadError(`Server session lost but backup available. ${backup.documents.length} document(s) in backup. Re-upload to restore full functionality.`)
        return true
      } else {
        setSessionInfo(null)
        setSessionId(null)
        setIsUsingBackup(false)
        setUploadError('Your session has expired and no backup is available. Please upload your documents again.')
        return false
      }
    }
  }

  const refreshSessionInfo = async (id?: string) => {
    const targetId = id || sessionId
    if (targetId) {
      await loadSessionInfo(targetId)
    }
  }

  const getSessionStatus = () => {
    if (!sessionInfo) return 'no-session'
    if (isUsingBackup) return 'backup'
    return 'active'
  }

  return {
    // State
    sessionInfo,
    sessionId,
    isUploading,
    uploadError,
    isUsingBackup,
    
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
    getSessionStatus,
    
    // Error handling
    clearUploadError: () => setUploadError(null)
  }
} 