import React from 'react'
import { KeyIcon, SparklesIcon } from '@heroicons/react/24/outline'
import './WelcomeSection.css'

interface GlobalKnowledgeBase {
  status: 'not_initialized' | 'error' | 'ready'
  documents: string[]
  document_count: number
  chunk_count: number
  description: string
}

interface WelcomeSectionProps {
  apiKey: string
  onEnterApiKey: () => void
  hasRAG?: boolean
  ragMode?: boolean
  globalKB?: GlobalKnowledgeBase | null
  onTryGlobalKB?: () => void
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({ 
  apiKey, 
  onEnterApiKey,
  hasRAG = false,
  ragMode = false,
  globalKB = null,
  onTryGlobalKB
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
                <span>Chat with your documents</span>
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
              Start a conversation with AI! Upload a document to enable RAG mode and chat with your documents.
            </p>
            
            {/* Global Knowledge Base Section */}
            {globalKB && globalKB.status === 'ready' && (
              <div className="global-kb-section">
                <h3 className="global-kb-title">
                  🏛️ Pre-loaded Regulatory Knowledge Base
                </h3>
                <p className="global-kb-description">
                  {globalKB.description}
                </p>
                <div className="global-kb-stats">
                  <div className="kb-stat">
                    <span className="kb-stat-number">{globalKB.document_count}</span>
                    <span className="kb-stat-label">Documents</span>
                  </div>
                  <div className="kb-stat">
                    <span className="kb-stat-number">{globalKB.chunk_count}</span>
                    <span className="kb-stat-label">Text Chunks</span>
                  </div>
                </div>
                <div className="global-kb-docs">
                  <summary className="kb-docs-title">📄 Available Documents:</summary>
                  <div className="kb-docs-list">
                    {globalKB.documents.slice(0, 5).map((doc, index) => (
                      <div key={index} className="kb-doc-item">
                        <span className="kb-doc-icon">
                          {doc.includes('Basel') ? '📊' : 
                           doc.includes('COREP') || doc.includes('FINREP') ? '📋' : 
                           doc.includes('SQL') ? '💾' : 
                           doc.includes('Jira') ? '🎫' : 
                           doc.includes('Policy') ? '📜' : '📄'}
                        </span>
                        <span className="kb-doc-name">{doc}</span>
                      </div>
                    ))}
                    {globalKB.documents.length > 5 && (
                      <div className="kb-doc-item">
                        <span className="kb-doc-icon">➕</span>
                        <span className="kb-doc-name">
                          +{globalKB.documents.length - 5} more documents
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                {onTryGlobalKB && (
                  <button onClick={onTryGlobalKB} className="try-global-kb-button">
                    🚀 Try asking about Basel III or regulatory reporting!
                  </button>
                )}
              </div>
            )}

            {globalKB && globalKB.status === 'not_initialized' && (
              <div className="global-kb-loading">
                <div className="loading-spinner">⏳</div>
                <p>Loading regulatory knowledge base...</p>
              </div>
            )}

            {globalKB && globalKB.status === 'error' && (
              <div className="global-kb-error">
                <div className="error-icon">⚠️</div>
                <p>Global knowledge base unavailable</p>
              </div>
            )}
            
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