import React, { useCallback, useMemo, memo } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'
import { MessageBubble, LoadingIndicator } from '..'
import { logger } from '../../utils/logger'
import type { Message } from '../../types'
import './ChatContainer.css'

interface ChatContainerProps {
  messages: Message[]
  input: string
  setInput: (input: string) => void
  isLoading: boolean
  apiKey: string | null
  ragMode: boolean
  onSubmit: (e: React.FormEvent) => Promise<void>
  messagesEndRef: React.RefObject<HTMLDivElement>
  globalKBReady: boolean
  hasActiveSession: boolean
}

// Memoized messages list to prevent unnecessary re-renders
const MessagesList = memo(({ 
  messages, 
  messagesEndRef 
}: { 
  messages: Message[]
  messagesEndRef: React.RefObject<HTMLDivElement>
}) => {
  return (
    <div className="messages-container">
      {messages.map((message, index) => (
        <MessageBubble 
          key={`${message.role}-${index}-${message.content.slice(0, 20)}`}
          message={message} 
          index={index} 
        />
      ))}
      <div ref={messagesEndRef} />
    </div>
  )
})

// Memoized chat input to prevent re-renders when not needed
const ChatInput = memo(({ 
  input, 
  setInput, 
  onSubmit, 
  isLoading, 
  disabled 
}: {
  input: string
  setInput: (input: string) => void
  onSubmit: (e: React.FormEvent) => Promise<void>
  isLoading: boolean
  disabled: boolean
}) => {
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
  }, [setInput])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && input.trim()) {
        onSubmit(e as unknown as React.FormEvent)
      }
    }
  }, [onSubmit, disabled, input])

  return (
    <form onSubmit={onSubmit} className="chat-input-form">
      <div className="input-container">
        <textarea
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
          className="message-input"
          disabled={disabled}
          rows={1}
          style={{
            minHeight: '44px',
            maxHeight: '120px',
            resize: 'none',
            overflow: 'auto'
          }}
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="send-button"
          aria-label="Send message"
        >
          {isLoading ? (
            <div className="loading-spinner" />
          ) : (
            <PaperAirplaneIcon className="send-icon" />
          )}
        </button>
      </div>
    </form>
  )
})

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  input,
  setInput,
  isLoading,
  apiKey,
  ragMode,
  onSubmit,
  messagesEndRef,
  globalKBReady,
  hasActiveSession
}) => {
  // Memoize expensive computations
  const isInputDisabled = useMemo(() => {
    return !apiKey || isLoading
  }, [apiKey, isLoading])

  const chatStatus = useMemo(() => {
    if (!apiKey) return 'Enter API key to start chatting'
    if (ragMode && !globalKBReady && !hasActiveSession) return 'RAG mode enabled but no knowledge base available'
    if (ragMode && (globalKBReady || hasActiveSession)) return 'RAG mode: Enhanced with knowledge base'
    return 'Regular chat mode'
  }, [apiKey, ragMode, globalKBReady, hasActiveSession])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    try {
      await onSubmit(e)
    } catch (error) {
      logger.error('Chat submission error:', error)
    }
  }, [onSubmit])

  return (
    <div className="chat-container">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="chat-status">
          <div className={`status-indicator ${ragMode ? 'rag-active' : 'regular'}`} />
          <span className="status-text">{chatStatus}</span>
        </div>
        {ragMode && (globalKBReady || hasActiveSession) && (
          <div className="rag-badge">
            <span className="rag-label">RAG Enhanced</span>
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-content">
              <h3>Start a conversation</h3>
              <p>
                {apiKey 
                  ? 'Ask me anything! I can help with general questions or analyze your documents if you upload them.'
                  : 'Please enter your OpenAI API key to begin chatting.'
                }
              </p>
            </div>
          </div>
        ) : (
          <MessagesList messages={messages} messagesEndRef={messagesEndRef} />
        )}
        
        {isLoading && (
          <div className="loading-container">
            <LoadingIndicator />
            <span className="loading-text">
              {ragMode ? 'Analyzing documents and generating response...' : 'Generating response...'}
            </span>
          </div>
        )}
      </div>

      {/* Chat Input */}
      <div className="chat-input-area">
        <ChatInput
          input={input}
          setInput={setInput}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          disabled={isInputDisabled}
        />
        
        {!apiKey && (
          <div className="input-help">
            <span>🔑 API key required to send messages</span>
          </div>
        )}
      </div>
    </div>
  )
} 