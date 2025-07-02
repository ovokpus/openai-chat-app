import { KeyIcon, PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/solid'
import { useChat } from './hooks/useChat'
import { useRAG } from './hooks/useRAG'
import { WelcomeSection, MessageBubble, LoadingIndicator, PDFUpload, DocumentPanel } from './components'
import 'katex/dist/katex.min.css'
import './App.css'
import { useState } from 'react'

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
    handleSubmit: handleRegularChat
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
    clearUploadError
  } = useRAG()

  // Local state for RAG mode
  const [ragMode, setRagMode] = useState(false)
  const [showUploadError, setShowUploadError] = useState(false)

  // Enhanced submit handler that supports both regular and RAG chat
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !apiKey || isLoading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message to chat
    const newUserMessage = { role: 'user' as const, content: userMessage }
    
    try {
      if (ragMode && hasActiveSession()) {
        // Use RAG chat
        const reader = await sendRAGChat(userMessage, apiKey)
        
        if (reader) {
          const decoder = new TextDecoder()
          let assistantMessage = ''

          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            
            const chunk = decoder.decode(value)
            assistantMessage += chunk
            
            // Update messages with RAG indicator
            // Note: This is a simplified implementation - in a real app,
            // you'd want to properly integrate this with the useChat hook
          }
        }
      } else {
        // Use regular chat
        handleRegularChat(e)
      }
    } catch (error) {
      console.error('Chat error:', error)
      // Handle error appropriately
    }
  }

  const handleUploadSuccess = (response: any) => {
    console.log('Upload successful:', response)
    setRagMode(true) // Auto-enable RAG mode when PDF is uploaded
    clearUploadError()
    setShowUploadError(false)
  }

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error)
    setShowUploadError(true)
  }

  const handleClearSession = async () => {
    await clearSession()
    setRagMode(false)
  }

  const toggleRagMode = () => {
    if (hasActiveSession()) {
      setRagMode(!ragMode)
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-container">
          <div className="header-left">
            <h1 className="header-title">OpenAI Chat</h1>
            {hasActiveSession() && (
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

      {/* Upload Error Display */}
      {showUploadError && uploadError && (
        <div className="error-banner">
          <div className="error-content">
            <span>{uploadError}</span>
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
        <div className="chat-container">
          
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

          {/* Messages Area */}
          <div className="messages-area">
            {messages.length === 0 && (
              <WelcomeSection 
                apiKey={apiKey} 
                onEnterApiKey={() => setShowApiKey(true)}
                hasRAG={hasActiveSession()}
                ragMode={ragMode}
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
            {ragMode && hasActiveSession() && (
              <div className="rag-indicator-input">
                <SparklesIcon className="rag-input-icon" />
                <span>RAG mode active - asking your documents</span>
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="input-form">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={ragMode && hasActiveSession() 
                    ? "Ask a question about your uploaded documents..." 
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
      </main>
    </div>
  )
}

export default App
