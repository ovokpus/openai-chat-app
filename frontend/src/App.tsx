import React, { useState, useRef, useEffect } from 'react';
import { useChat } from './hooks/useChat';
import { useRAG } from './hooks/useRAG';
import { Header } from './components/Header/Header';
import { ChatContainer } from './components/ChatContainer/ChatContainer';
import { DocumentUpload } from './components/DocumentUpload/DocumentUpload';
import { DocumentPanel } from './components/DocumentPanel/DocumentPanel';
import { ERROR_MESSAGES, SUCCESS_MESSAGES } from './constants';
import 'katex/dist/katex.min.css';
import './App.css';

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
  } = useChat();

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
    validateSession,
    isUsingBackup,
    getSessionStatus
  } = useRAG();

  // Local state for RAG mode and UI
  const [ragMode, setRagMode] = useState(false);
  const [showUploadError, setShowUploadError] = useState(false);
  const [showUploadSuccess, setShowUploadSuccess] = useState(false);
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState('');

  // Validate session when component mounts
  useEffect(() => {
    // Only validate if we have session info but it might be stale/invalid
    // Don't validate if we just got fresh session info from a successful operation
    if (sessionInfo && !isUsingBackup) {
      const sessionAge = Date.now() - new Date(sessionInfo.created_at).getTime();
      // Only validate if session is older than 1 minute (to avoid constant validation)
      if (sessionAge > 60 * 1000) {
        validateSession();
      }
    }
  }, [sessionInfo?.session_id]); // Only depend on session_id, not the whole sessionInfo object

  // Enhanced submit handler that supports both regular and RAG chat
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !apiKey || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message to chat immediately
    const newUserMessage = { role: 'user' as const, content: userMessage };
    addMessage(newUserMessage);
    setIsLoading(true);

    try {
      if (ragMode && hasActiveSession()) {
        // Validate session before making RAG request
        const isValidSession = await validateSession();
        if (!isValidSession) {
          addMessage({ 
            role: 'assistant', 
            content: ERROR_MESSAGES.SESSION_EXPIRED
          });
          setRagMode(false);
          setIsLoading(false);
          return;
        }

        // Use RAG chat - stream the response
        const reader = await sendRAGChat(userMessage, apiKey);
        
        if (reader) {
          const decoder = new TextDecoder();
          let assistantMessage = '';

          // Add initial assistant message
          const assistantMsg = { role: 'assistant' as const, content: '' };
          addMessage(assistantMsg);

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            assistantMessage += chunk;
            
            // Update the last message (assistant response)
            assistantMsg.content = assistantMessage;
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
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          if (!reader) throw new Error('No reader available');

          const decoder = new TextDecoder();
          let assistantMessage = '';

          // Add initial assistant message
          const assistantMsg = { role: 'assistant' as const, content: '' };
          addMessage(assistantMsg);

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            assistantMessage += chunk;
            
            // Update the last message (assistant response)
            assistantMsg.content = assistantMessage;
          }
        } catch (error) {
          console.error('Regular chat error:', error);
          addMessage({ 
            role: 'assistant', 
            content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}` 
          });
        }
      }
    } catch (error) {
      console.error('Error in chat:', error);
      
      // Check if it's a session-related error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      let displayMessage: string = ERROR_MESSAGES.NETWORK_ERROR;
      
      if (errorMessage.includes('Session not found') || 
          errorMessage.includes('session has expired') ||
          errorMessage.includes('404')) {
        displayMessage = ERROR_MESSAGES.RAG_SESSION_LOST;
        // Clear the invalid session state
        setRagMode(false);
        await clearSession();
      } else if (errorMessage.includes('HTTP error')) {
        displayMessage = `Server error: ${errorMessage}`;
      }
      
      addMessage({
        role: 'assistant',
        content: displayMessage
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadSuccess = async (response: any) => {
    console.log('Upload successful:', response);
    setRagMode(true);
    clearUploadError();
    setShowUploadError(false);
    
    setUploadSuccessMessage(
      `${SUCCESS_MESSAGES.UPLOAD_SUCCESS} "${response.filename}" (${response.document_count} documents)`
    );
    setShowUploadSuccess(true);
    
    setTimeout(() => setShowUploadSuccess(false), 5000);
    
    if (response.session_id) {
      await refreshSessionInfo(response.session_id);
    }
  };

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error);
    setShowUploadError(true);
  };

  const handleClearSession = async () => {
    await clearSession();
    setRagMode(false);
    setShowUploadSuccess(false);
  };

  const handleDocumentDeleted = async (documentName: string) => {
    if (sessionInfo?.session_id) {
      await refreshSessionInfo(sessionInfo.session_id);
    }
  };

  const toggleRagMode = () => {
    if (hasActiveSession()) {
      setRagMode(!ragMode);
    }
  };

  return (
    <div className="app-container">
      <Header 
        showApiKey={showApiKey}
        setShowApiKey={setShowApiKey}
        apiKey={apiKey}
        setApiKey={setApiKey}
        hasRAG={hasActiveSession()}
        ragMode={ragMode}
        onToggleRAG={toggleRagMode}
      />

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

      <main className="main-container">
        <div className="layout-container">
          {/* Sidebar for Document Upload and Management */}
          {apiKey && (
            <div className="sidebar">
              <DocumentUpload
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
                apiKey={apiKey}
                onDocumentDeleted={handleDocumentDeleted}
                ragMode={ragMode}
                isUsingBackup={isUsingBackup}
                sessionStatus={getSessionStatus()}
              />
            </div>
          )}

          {/* Chat Container */}
          <ChatContainer
            messages={messages}
            input={input}
            setInput={setInput}
            isLoading={isLoading}
            apiKey={apiKey}
            onSubmit={handleSubmit}
            messagesEndRef={messagesEndRef}
            hasRAG={hasActiveSession()}
            ragMode={ragMode}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
