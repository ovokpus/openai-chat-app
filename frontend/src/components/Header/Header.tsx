import React from 'react'
import { KeyIcon, SparklesIcon } from '@heroicons/react/24/solid'
import './Header.css'

interface HeaderProps {
  hasActiveSession: boolean
  ragMode: boolean
  onToggleRagMode: () => void
  onToggleApiKey: () => void
}

export const Header: React.FC<HeaderProps> = ({
  hasActiveSession,
  ragMode,
  onToggleRagMode,
  onToggleApiKey
}) => {
  return (
    <header className="header">
      <div className="header-container">
        <div className="header-left">
          <h1 className="header-title">OpenAI Chat</h1>
        </div>
        <div className="header-right">
          {hasActiveSession && (
            <button
              onClick={onToggleRagMode}
              className={`rag-toggle-button ${ragMode ? 'active' : ''}`}
              title={ragMode ? 'Disable RAG mode' : 'Enable RAG mode'}
            >
              <SparklesIcon className="rag-toggle-icon" />
              {ragMode ? 'RAG ON' : 'RAG OFF'}
            </button>
          )}
          <button
            onClick={onToggleApiKey}
            className="api-key-button"
          >
            <KeyIcon className="api-key-icon" />
            <span className="hidden-mobile">API Key</span>
          </button>
        </div>
      </div>
    </header>
  )
} 