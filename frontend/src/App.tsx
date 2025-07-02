import React, { useState, useCallback, useMemo, useEffect } from 'react'
import { KeyIcon, SparklesIcon } from '@heroicons/react/24/solid'
import { useChat } from './hooks/useChat'
import { useRAG } from './hooks/useRAG'
import { useGlobalKnowledgeBase } from './hooks/useGlobalKnowledgeBase'
import { 
  WelcomeSection, 
  PDFUpload, 
  DocumentPanel, 
  ConfirmationModal,
  ErrorBoundary,
  ChatContainer,
  NotificationManager
} from './components'
import { logger } from './utils/logger'
import 'katex/dist/katex.min.css'
import './App.css'

// Main App Component with Error Boundary and Performance Optimizations
function App() {
  // ===============================
  // HOOKS AND STATE MANAGEMENT
  // ===============================
  
  const {
    messages,
    input,
    setInput,
    isLoading,
    apiKey,
    setApiKey,
    showApiKey,
    setShowApiKey,
    messagesEndRef,
    addMessage,
    setIsLoading
  } = useChat()

  const {
    sessionInfo,
    isUploading,
    uploadError,
    handlePDFUpload,
    sendRAGChat,
    clearSession,
    hasActiveSession,
    clearUploadError,
    refreshSessionInfo,
    validateSession
  } = useRAG()

  const {
    globalKB,
    isReady: globalKBReady,
    isInitializing: globalKBInitializing,
    refresh: refreshGlobalKB,
    deleteUserDocument,
    isDeleting
  } = useGlobalKnowledgeBase()

  // ===============================
  // LOCAL STATE
  // ===============================
  
  const [ragMode, setRagMode] = useState(false)
  const [showUploadError, setShowUploadError] = useState(false)
  const [showUploadSuccess, setShowUploadSuccess] = useState(false)
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState('')

  // Modal state for document deletion
  const [deleteModalState, setDeleteModalState] = useState<{
    isOpen: boolean
    filename: string | null
  }>({
    isOpen: false,
    filename: null
  })

  // ===============================
  // MEMOIZED VALUES FOR PERFORMANCE
  // ===============================
  
  const hasMessages = useMemo(() => messages.length > 0, [messages.length])
  
  const canChat = useMemo(() => {
    return apiKey && !isLoading
  }, [apiKey, isLoading])

  const ragStatus = useMemo(() => {
    if (!ragMode) return 'disabled'
    if (globalKBReady || hasActiveSession(false)) return 'ready'
    return 'unavailable'
  }, [ragMode, globalKBReady, hasActiveSession])

     const hasKnowledgeBase = useMemo(() => {
     return globalKBReady || hasActiveSession(globalKBReady)
   }, [globalKBReady, hasActiveSession])

  // ===============================
  // OPTIMIZED EVENT HANDLERS
  // ===============================
  
  // Validate session when component mounts
  useEffect(() => {
    if (sessionInfo) {
      validateSession()
    }
  }, [sessionInfo, validateSession])

  // Memoized chat submission handler
  const handleChatSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !apiKey || isLoading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message to chat immediately
    const newUserMessage = { role: 'user' as const, content: userMessage }
    addMessage(newUserMessage)
    setIsLoading(true)

    try {
             if (ragMode && (globalKBReady || hasActiveSession(globalKBReady))) {
        // Validate session if needed
                 if (hasActiveSession(globalKBReady)) {
          const isValidSession = await validateSession()
          if (!isValidSession && !globalKBReady) {
            addMessage({ 
              role: 'assistant', 
              content: 'Your session has expired. Please upload a document again to continue using RAG mode.' 
            })
            setRagMode(false)
            setIsLoading(false)
            return
          }
        }

        // Use RAG chat with streaming
        const reader = await sendRAGChat(userMessage, apiKey)
        
        if (reader) {
          const decoder = new TextDecoder()
          let assistantMessage = ''
          const assistantMsg = { role: 'assistant' as const, content: '' }
          addMessage(assistantMsg)

          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            
            const chunk = decoder.decode(value)
            assistantMessage += chunk
            assistantMsg.content = assistantMessage
          }
        }
      } else {
        // Regular chat
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            developer_message: 'You are a helpful assistant.',
            user_message: userMessage,
            model: 'gpt-4o-mini',
            api_key: apiKey
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) throw new Error('No reader available')

        const decoder = new TextDecoder()
        let assistantMessage = ''
        const assistantMsg = { role: 'assistant' as const, content: '' }
        addMessage(assistantMsg)

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          assistantMessage += chunk
          assistantMsg.content = assistantMessage
        }
      }
    } catch (error) {
      logger.error('Chat error:', error)
      addMessage({ 
        role: 'assistant', 
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      })
    } finally {
      setIsLoading(false)
    }
  }, [input, apiKey, isLoading, ragMode, globalKBReady, hasActiveSession, validateSession, sendRAGChat, addMessage, setInput, setIsLoading])

  // Memoized upload success handler
  const handleUploadSuccess = useCallback(async (response: any) => {
    logger.debug('Upload successful in App:', response)
    setRagMode(true)
    clearUploadError()
    setShowUploadError(false)
    
    setUploadSuccessMessage(`Successfully uploaded "${response.filename}" - added to global knowledge base`)
    setShowUploadSuccess(true)
    
    setTimeout(() => setShowUploadSuccess(false), 5000)
    
         if (response.session_id) {
       await refreshSessionInfo(response.session_id)
     }
    
    await refreshGlobalKB()
  }, [clearUploadError, refreshSessionInfo, refreshGlobalKB])

  // Memoized upload error handler
  const handleUploadError = useCallback((error: string) => {
    setShowUploadError(true)
    setShowUploadSuccess(false)
  }, [])

  // Memoized RAG mode toggle
  const toggleRagMode = useCallback(() => {
    setRagMode(prev => !prev)
  }, [])

  // Memoized global KB try handler
  const handleTryGlobalKB = useCallback(() => {
    if (globalKBReady) {
      setRagMode(true)
    }
  }, [globalKBReady])

  // Memoized delete document handlers
  const handleDeleteDocumentRequest = useCallback((filename: string) => {
    setDeleteModalState({
      isOpen: true,
      filename
    })
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    const { filename } = deleteModalState
    if (!filename) return

    try {
      logger.debug(`Deleting document: ${filename}`)
      setDeleteModalState({ isOpen: false, filename: null })
      
      await deleteUserDocument(filename)
      
      logger.debug('Document deleted successfully, refreshing data...')
      await Promise.all([
        refreshSessionInfo(sessionInfo?.session_id),
        refreshGlobalKB()
      ])
      
    } catch (error) {
      logger.error('Error in delete confirmation:', error)
    }
  }, [deleteModalState, deleteUserDocument, refreshSessionInfo, refreshGlobalKB])

  const handleCancelDelete = useCallback(() => {
    setDeleteModalState({ isOpen: false, filename: null })
  }, [])

  // Memoized notification handlers
  const handleCloseSuccessNotification = useCallback(() => {
    setShowUploadSuccess(false)
  }, [])

  const handleCloseErrorNotification = useCallback(() => {
    setShowUploadError(false)
  }, [])

  // ===============================
  // MEMOIZED NOTIFICATION CONFIG
  // ===============================
  
  const notificationConfig = useMemo(() => ({
    successNotification: showUploadSuccess ? {
      message: uploadSuccessMessage,
      isVisible: showUploadSuccess,
      onClose: handleCloseSuccessNotification
    } : undefined,
    errorNotification: showUploadError ? {
      message: uploadError || 'Upload failed',
      isVisible: showUploadError,
      onClose: handleCloseErrorNotification
    } : undefined
  }), [showUploadSuccess, uploadSuccessMessage, showUploadError, uploadError, handleCloseSuccessNotification, handleCloseErrorNotification])

  // ===============================
  // RENDER
  // ===============================
  
  return (
    <ErrorBoundary>
      <div className="app">
        {/* Header Section */}
        <header className="app-header">
          <h1 className="app-title">
            <SparklesIcon className="title-icon" />
            AI Chat Assistant
          </h1>
          
          <div className="header-controls">
            {/* RAG Mode Toggle */}
            {hasKnowledgeBase && (
              <button
                onClick={toggleRagMode}
                className={`rag-toggle ${ragMode ? 'active' : ''}`}
                title={ragMode ? 'Disable RAG mode' : 'Enable RAG mode'}
              >
                <SparklesIcon className="toggle-icon" />
                RAG Mode
              </button>
            )}
            
            {/* API Key Toggle */}
            <button
              onClick={() => setShowApiKey(!showApiKey)}
              className="api-key-toggle"
              title="Configure API Key"
            >
              <KeyIcon className="toggle-icon" />
              API Key
            </button>
          </div>
        </header>

        {/* API Key Configuration */}
        {showApiKey && (
          <div className="api-key-section">
            <div className="api-key-content">
              <input
                type="password"
                value={apiKey || ''}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your OpenAI API key..."
                className="api-key-input"
              />
              <button
                onClick={() => setShowApiKey(false)}
                className="api-key-done"
              >
                Done
              </button>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div className="app-content">
          {/* Sidebar */}
          <aside className="app-sidebar">
            {/* Upload Section */}
            <div className="upload-section">
              <PDFUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                disabled={isUploading}
                apiKey={apiKey}
              />
            </div>

            {/* Document Panel */}
            <div className="document-section">
              <DocumentPanel
                apiKey={apiKey}
                onRefresh={refreshGlobalKB}
                onDeleteDocument={handleDeleteDocumentRequest}
              />
            </div>
          </aside>

          {/* Chat Area */}
          <main className="app-main">
            {hasMessages || apiKey ? (
              <ChatContainer
                messages={messages}
                input={input}
                setInput={setInput}
                isLoading={isLoading}
                apiKey={apiKey}
                ragMode={ragMode}
                onSubmit={handleChatSubmit}
                messagesEndRef={messagesEndRef}
                globalKBReady={globalKBReady}
                                 hasActiveSession={hasActiveSession(globalKBReady)}
              />
            ) : (
                             <WelcomeSection
                 apiKey={apiKey}
                 onEnterApiKey={() => setShowApiKey(true)}
                 onTryGlobalKB={handleTryGlobalKB}
               />
            )}
          </main>
        </div>

        {/* Notifications */}
        <NotificationManager {...notificationConfig} />

        {/* Confirmation Modal */}
        {deleteModalState.isOpen && (
          <ConfirmationModal
            isOpen={deleteModalState.isOpen}
            title="Delete Document"
            message={`Are you sure you want to delete "${deleteModalState.filename}"? This action cannot be undone.`}
            confirmText="Delete"
            cancelText="Cancel"
            onConfirm={handleConfirmDelete}
            onCancel={handleCancelDelete}
            isLoading={isDeleting === deleteModalState.filename}
          />
        )}
      </div>
    </ErrorBoundary>
  )
}

export default App 