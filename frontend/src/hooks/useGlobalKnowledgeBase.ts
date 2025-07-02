import { useState, useEffect, useRef } from 'react'
import { getGlobalKnowledgeBase, deleteDocument } from '../services/chatApi'
import type { GlobalKnowledgeBaseInfo } from '../types'

export const useGlobalKnowledgeBase = () => {
  const [globalKB, setGlobalKB] = useState<GlobalKnowledgeBaseInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDeleting, setIsDeleting] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(false)
  const prevDocumentCount = useRef<number | null>(null)
  const lastRefreshTime = useRef<number>(0)

  const fetchGlobalKB = async (silent: boolean = false) => {
    try {
      if (!silent) {
        setIsLoading(true)
      } else {
        setIsAutoRefreshing(true)
      }
      setError(null)
      
      const data = await getGlobalKnowledgeBase()
      
      // Check if document count changed (for notifications)
      if (prevDocumentCount.current !== null && data.document_count !== prevDocumentCount.current) {
        const diff = data.document_count - prevDocumentCount.current
        const changeType = diff > 0 ? 'Added' : 'Removed'
        const changeIcon = diff > 0 ? '📈' : '📉'
        console.log(`${changeIcon} Global KB updated: ${changeType} ${Math.abs(diff)} document(s) - Total: ${data.document_count}`)
        
        // Log detailed breakdown
        console.log(`📊 KB Status: ${data.original_document_count} original + ${data.user_uploaded_document_count} user-uploaded = ${data.document_count} total`)
      }
      
      prevDocumentCount.current = data.document_count
      setGlobalKB(data)
      lastRefreshTime.current = Date.now()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      console.error('❌ Error fetching global knowledge base:', errorMessage)
      setError(errorMessage)
    } finally {
      if (!silent) {
        setIsLoading(false)
      } else {
        setIsAutoRefreshing(false)
      }
    }
  }

  const deleteUserDocument = async (filename: string, apiKey: string): Promise<boolean> => {
    try {
      setIsDeleting(filename)
      setError(null)
      
      // Optimistic update: temporarily remove the document from local state
      if (globalKB) {
        const optimisticKB = {
          ...globalKB,
          user_uploaded_documents: globalKB.user_uploaded_documents.filter(doc => doc !== filename),
          user_uploaded_document_count: globalKB.user_uploaded_document_count - 1,
          document_count: globalKB.document_count - 1
        }
        setGlobalKB(optimisticKB)
      }
      
      await deleteDocument(filename, apiKey)
      
      // Immediate refresh after successful deletion
      console.log(`🗑️ Document "${filename}" deleted, refreshing Global KB...`)
      await fetchGlobalKB(true) // Silent refresh
      
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete document'
      console.error('Error deleting document:', errorMessage)
      setError(errorMessage)
      
      // Revert optimistic update by refreshing from server
      await fetchGlobalKB(true)
      
      return false
    } finally {
      setIsDeleting(null)
    }
  }

  // Enhanced polling for automatic updates
  useEffect(() => {
    fetchGlobalKB()
    
    // More aggressive polling for better responsiveness
    const interval = setInterval(() => {
      const timeSinceLastRefresh = Date.now() - lastRefreshTime.current
      
      if (!globalKB || globalKB.status !== 'ready') {
        // Poll every 2 seconds if not ready
        fetchGlobalKB(true)
      } else if (timeSinceLastRefresh > 5000) {
        // Poll every 5 seconds when ready to catch external changes
        fetchGlobalKB(true)
      }
    }, 1000) // Check every second for more responsiveness

    return () => clearInterval(interval)
  }, [globalKB?.status])

  // Auto-refresh when global KB becomes ready
  useEffect(() => {
    if (globalKB?.status === 'ready' && prevDocumentCount.current === null) {
      console.log('📚 Global KB initialized, setting up auto-refresh...')
      prevDocumentCount.current = globalKB.document_count
    }
  }, [globalKB?.status])

  const isReady = globalKB?.status === 'ready'
  const hasError = globalKB?.status === 'error' || error !== null
  const isInitializing = globalKB?.status === 'not_initialized' || isLoading
  const hasDocuments = globalKB && (globalKB.original_document_count > 0 || globalKB.user_uploaded_document_count > 0)

  return {
    globalKB,
    isLoading,
    isDeleting,
    error,
    isReady,
    hasError,
    hasDocuments,
    isInitializing,
    isAutoRefreshing,
    refresh: fetchGlobalKB,
    deleteUserDocument
  }
} 