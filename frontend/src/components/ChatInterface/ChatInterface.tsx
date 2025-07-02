import React from 'react'
import { PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/solid'
import { MessageBubble, LoadingIndicator } from '../'
import type { Message } from '../../types'
import './ChatInterface.css'

interface ChatInterfaceProps {
  messages: Message[]
  input: string
  setInput: (value: string) => void
  isLoading: boolean
  apiKey: string
  onSubmit: (e: React.FormEvent) => void
  ragMode: boolean
  hasActiveSession: boolean
  messagesEndRef: React.RefObject<HTMLDivElement>
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  input,
  setInput,
  isLoading,
  apiKey,
  onSubmit,
  ragMode,
  hasActiveSession,
  messagesEndRef
}) => {
  return (
    <div className="chat-container">
      {/* Messages Area */}
      <div className="messages-area">
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
        {ragMode && hasActiveSession && (
          <div className="rag-indicator-input">
            <SparklesIcon className="rag-input-icon" />
            <span>
              {hasActiveSession 
                ? 'RAG mode active - asking your documents' 
                : 'RAG mode active - asking regulatory knowledge base'}
            </span>
          </div>
        )}
        
        <form onSubmit={onSubmit} className="input-form">
          <div className="input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={ragMode && hasActiveSession
                ? hasActiveSession 
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
  )
} 