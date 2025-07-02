import { KeyIcon, PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/solid'
import { useChat } from './hooks/useChat'
import { useRAG } from './hooks/useRAG'
import { useGlobalKnowledgeBase } from './hooks/useGlobalKnowledgeBase'
import { WelcomeSection, MessageBubble, LoadingIndicator, PDFUpload, DocumentPanel } from './components'
import 'katex/dist/katex.min.css'
import './App.css'
import { useState, useRef, useEffect } from 'react'

function App() {
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

  // RAG functionality
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

  // Global Knowledge Base functionality
  const {
    globalKB,
    isReady: globalKBReady,
    isInitializing: globalKBInitializing
  } = useGlobalKnowledgeBase()

  // Local state for RAG mode and UI
  const [ragMode, setRagMode] = useState(false)
  const [showUploadError, setShowUploadError] = useState(false)
  const [showUploadSuccess, setShowUploadSuccess] = useState(false)
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState('')

  // Validate session when component mounts
  useEffect(() => {
    if (sessionInfo) {
      validateSession()
    }
  }, [sessionInfo, validateSession])

  // Enhanced submit handler that supports both regular and RAG chat
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !apiKey || isLoading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message to chat immediately
    const newUserMessage = { role: 'user' as const, content: userMessage }
    addMessage(newUserMessage)
    setIsLoading(true)

    try {
      if (ragMode && hasActiveSession(globalKBReady)) {
        // If user has active session, validate it; otherwise use global KB
        if (hasActiveSession(false)) { // Check only user session, not global KB
          const isValidSession = await validateSession()
          if (!isValidSession) {
            // Fall back to global KB if available
            if (!globalKBReady) {
              addMessage({ 
                role: 'assistant', 
                content: 'Your session has expired. Please upload a document again to continue using RAG mode.' 
              })
              setRagMode(false)
              setIsLoading(false)
              return
            }
          }
        }

        // Use RAG chat - stream the response (works with both user docs and global KB)
        const reader = await sendRAGChat(userMessage, apiKey)
        
        if (reader) {
          const decoder = new TextDecoder()
          let assistantMessage = ''

          // Add initial assistant message
          const assistantMsg = { role: 'assistant' as const, content: '' }
          addMessage(assistantMsg)

          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            
            const chunk = decoder.decode(value)
            assistantMessage += chunk
            
            // Update the last message (assistant response)
            assistantMsg.content = assistantMessage
          }
        }
      } else {
        // Use regular chat (useChat handles the streaming internally)
        try {
          const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
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

          // Add initial assistant message
          const assistantMsg = { role: 'assistant' as const, content: '' }
          addMessage(assistantMsg)

          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            
            const chunk = decoder.decode(value)
            assistantMessage += chunk
            
            // Update the last message (assistant response)
            assistantMsg.content = assistantMessage
          }
        } catch (error) {
          console.error('Regular chat error:', error)
          addMessage({ 
            role: 'assistant', 
            content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}` 
          })
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      addMessage({ 
        role: 'assistant', 
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleUploadSuccess = async (response: any) => {
    console.log('Upload successful in App:', response)
    setRagMode(true) // Auto-enable RAG mode when PDF is uploaded
    clearUploadError()
    setShowUploadError(false)
    
    // Show success message
    setUploadSuccessMessage(`Successfully uploaded "${response.filename}" with ${response.document_count} documents`)
    setShowUploadSuccess(true)
    
    // Hide success message after 5 seconds
    setTimeout(() => setShowUploadSuccess(false), 5000)
    
    // Force refresh session info to update the document panel
    if (response.session_id) {
      console.log('Refreshing session info for:', response.session_id)
      await refreshSessionInfo(response.session_id)
    }
  }

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error)
    setShowUploadError(true)
  }

  const handleClearSession = async () => {
    await clearSession()
    setRagMode(false)
    setShowUploadSuccess(false)
  }

  const toggleRagMode = () => {
    if (hasActiveSession(globalKBReady)) {
      setRagMode(!ragMode)
    }
  }

  const handleTryGlobalKB = () => {
    if (globalKBReady) {
      setRagMode(true)
      setInput("What are the Basel III minimum capital requirements for CET1 ratio?")
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-container">
          <div className="header-left">
            <h1 className="header-title">OpenAI Chat</h1>
            {hasActiveSession(globalKBReady) && (
              <div className="rag-toggle">
                <button
                  onClick={toggleRagMode}
                  className={`rag-toggle-button ${ragMode ? 'active' : ''}`}
                  title={ragMode ? 'Disable RAG mode' : 'Enable RAG mode'}
                >
                  <SparklesIcon className="rag-toggle-icon" />
                  {ragMode ? 'RAG ON' : 'RAG OFF'}
                </button>
              </div>
            )}
          </div>
          <div>
            <button
              onClick={() => setShowApiKey(!showApiKey)}
              className="api-key-button"
            >
              <KeyIcon className="api-key-icon" />
              <span className="hidden-mobile">API Key</span>
            </button>
          </div>
        </div>
      </header>

      {/* API Key Input Section */}
      {showApiKey && (
        <div className="api-key-section">
          <div className="api-key-form">
            <label className="api-key-label">
              OpenAI API Key:
            </label>
            <input
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="api-key-input"
            />
            <button
              onClick={() => setShowApiKey(false)}
              className="done-button"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Upload Success Display */}
      {showUploadSuccess && (
        <div className="success-banner">
          <div className="success-content">
            <span>✅ {uploadSuccessMessage}</span>
            <button
              onClick={() => setShowUploadSuccess(false)}
              className="success-close"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Upload Error Display */}
      {showUploadError && uploadError && (
        <div className="error-banner">
          <div className="error-content">
            <span>❌ {uploadError}</span>
            <button
              onClick={() => setShowUploadError(false)}
              className="error-close"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Main Chat Container */}
      <main className="main-container">
        <div className="layout-container">
          
          {/* Sidebar for PDF Upload and Document Management */}
          {apiKey && (
            <div className="sidebar">
              <PDFUpload
                apiKey={apiKey}
                sessionId={sessionInfo?.session_id}
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                disabled={isUploading}
              />
              
              <DocumentPanel
                sessionInfo={sessionInfo}
                onClearSession={handleClearSession}
                isLoading={isUploading}
              />
            </div>
          )}

          {/* Chat Container */}
          <div className="chat-container">
            {/* Messages Area */}
            <div className="messages-area">
              {messages.length === 0 && (
                <WelcomeSection 
                  apiKey={apiKey} 
                  onEnterApiKey={() => setShowApiKey(true)}
                  hasRAG={hasActiveSession(globalKBReady)}
                  ragMode={ragMode}
                  globalKB={globalKB}
                  onTryGlobalKB={handleTryGlobalKB}
                />
              )}
              
              {messages.map((message, index) => (
                <MessageBubble 
                  key={index} 
                  message={message} 
                  index={index} 
                />
              ))}
              
              {isLoading && <LoadingIndicator />}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="input-area">
              {ragMode && hasActiveSession(globalKBReady) && (
                <div className="rag-indicator-input">
                  <SparklesIcon className="rag-input-icon" />
                  <span>
                    {hasActiveSession(false) 
                      ? 'RAG mode active - asking your documents' 
                      : 'RAG mode active - asking regulatory knowledge base'}
                  </span>
                </div>
              )}
              
              <form onSubmit={handleSubmit} className="input-form">
                <div className="input-wrapper">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={ragMode && hasActiveSession(globalKBReady)
                      ? hasActiveSession(false) 
                        ? "Ask a question about your uploaded documents..." 
                        : "Ask about Basel III, COREP, FINREP, or regulatory reporting..."
                      : "Type your message..."}
                    className="message-input"
                    disabled={isLoading || !apiKey}
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading || !apiKey || !input.trim()}
                  className="send-button"
                >
                  <PaperAirplaneIcon className="send-icon" />
                  <span className="hidden-mobile">
                    {isLoading ? 'Sending...' : 'Send'}
                  </span>
                </button>
              </form>
              
              {!apiKey && (
                <p className="help-text">
                  Please enter your OpenAI API key to start chatting
                </p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
