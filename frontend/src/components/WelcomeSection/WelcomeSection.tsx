import React from 'react'
import { KeyIcon, SparklesIcon } from '@heroicons/react/24/outline'
import './WelcomeSection.css'

interface WelcomeSectionProps {
  apiKey: string
  onEnterApiKey: () => void
  hasRAG?: boolean
  ragMode?: boolean
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({ 
  apiKey, 
  onEnterApiKey,
  hasRAG = false,
  ragMode = false
}) => {
  return (
    <div className="welcome-section">
      <div className="welcome-content">
        <div className="welcome-header">
          <h2 className="welcome-title">Welcome to OpenAI Chat</h2>
          {hasRAG && (
            <div className="rag-status-welcome">
              <SparklesIcon className="rag-icon-welcome" />
              <span>{ragMode ? 'RAG Mode Active' : 'RAG Mode Available'}</span>
            </div>
          )}
        </div>
        
        {!apiKey ? (
          <div className="welcome-setup">
            <p className="welcome-description">
              To get started, please enter your OpenAI API key
            </p>
            <button onClick={onEnterApiKey} className="setup-button">
              <KeyIcon className="setup-icon" />
              Enter API Key
            </button>
          </div>
        ) : hasRAG ? (
          <div className="welcome-rag">
            <p className="welcome-description">
              {ragMode 
                ? "You're in RAG mode! Your questions will be answered using content from your uploaded documents."
                : "You have documents uploaded. Toggle RAG mode to chat with your documents, or continue with regular chat."
              }
            </p>
            <div className="welcome-features">
              <div className="feature-item">
                <span className="feature-icon">📄</span>
                <span>Chat with your documents (PDF, DOCX, TXT, MD, CSV)</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🔍</span>
                <span>Get answers from document content</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">⚡</span>
                <span>Real-time streaming responses</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="welcome-chat">
            <p className="welcome-description">
              Start a conversation with AI! Upload a document (PDF, DOCX, TXT, MD, CSV) to enable RAG mode and chat with your documents.
            </p>
            <div className="welcome-features">
              <div className="feature-item">
                <span className="feature-icon">💬</span>
                <span>Natural conversation with AI</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">📝</span>
                <span>Markdown formatting support</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🧮</span>
                <span>Mathematical expressions</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 