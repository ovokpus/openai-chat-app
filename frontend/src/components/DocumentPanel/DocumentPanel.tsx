import React from 'react'
import { DocumentIcon, TrashIcon, SparklesIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import type { SessionInfo } from '../../types'
import './DocumentPanel.css'

interface DocumentPanelProps {
  sessionInfo: SessionInfo | null
  onClearSession: () => void
  isLoading?: boolean
}

export const DocumentPanel: React.FC<DocumentPanelProps> = ({
  sessionInfo,
  onClearSession,
  isLoading = false
}) => {
  if (!sessionInfo || sessionInfo.document_count === 0) {
    return (
      <div className="document-panel empty">
        <div className="empty-state">
          <DocumentIcon className="empty-icon" />
          <p className="empty-text">No documents uploaded</p>
          <p className="empty-hint">Upload a PDF to start chatting with your documents</p>
        </div>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  // Check if session might be stale (created more than 1 hour ago)
  const sessionAge = Date.now() - new Date(sessionInfo.created_at).getTime()
  const isStaleSession = sessionAge > 60 * 60 * 1000 // 1 hour

  return (
    <div className="document-panel">
      <div className="document-panel-header">
        <div className="session-info">
          <SparklesIcon className="rag-icon" />
          <div>
            <h3 className="session-title">RAG Session Active</h3>
            <p className="session-subtitle">
              {sessionInfo.document_count} document{sessionInfo.document_count !== 1 ? 's' : ''} loaded
            </p>
          </div>
        </div>
        <button
          onClick={onClearSession}
          className="clear-button"
          title="Clear all documents"
          disabled={isLoading}
        >
          <TrashIcon className="clear-icon" />
        </button>
      </div>

      {isStaleSession && (
        <div className="session-warning">
          <ExclamationTriangleIcon className="warning-icon" />
          <div className="warning-content">
            <p className="warning-text">Session may have expired</p>
            <p className="warning-hint">If RAG chat isn't working, try uploading your PDF again</p>
          </div>
        </div>
      )}

      <div className="documents-list">
        {sessionInfo.documents.map((document, index) => (
          <div key={index} className="document-item">
            <DocumentIcon className="document-icon" />
            <div className="document-info">
              <span className="document-name">{document}</span>
              <span className="document-status">✓ Indexed</span>
            </div>
          </div>
        ))}
      </div>

      <div className="session-details">
        <p className="session-created">
          Session created: {formatDate(sessionInfo.created_at)}
        </p>
        <p className="session-id">
          Session ID: <code>{sessionInfo.session_id.slice(0, 8)}...</code>
        </p>
      </div>

      <div className="rag-status">
        <div className="rag-indicator active">
          <div className="rag-dot"></div>
          <span>RAG mode enabled</span>
        </div>
        <p className="rag-description">
          Your questions will be answered using content from uploaded documents
        </p>
      </div>
    </div>
  )
} 