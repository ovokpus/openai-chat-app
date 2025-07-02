import React, { useCallback } from 'react'
import { DocumentIcon, TrashIcon, SparklesIcon, ExclamationTriangleIcon, ServerIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { useGlobalKnowledgeBase } from '../../hooks/useGlobalKnowledgeBase'
import './DocumentPanel.css'

interface DocumentPanelProps {
  apiKey: string | null
  onRefresh?: () => void
  onDeleteDocument?: (filename: string) => void
}

export const DocumentPanel: React.FC<DocumentPanelProps> = ({
  apiKey,
  onRefresh,
  onDeleteDocument
}) => {
  const { 
    globalKB, 
    isLoading, 
    isDeleting, 
    error, 
    isReady, 
    hasError, 
    hasDocuments, 
    isInitializing,
    isAutoRefreshing,
    deleteUserDocument,
    refresh: refreshGlobalKB
  } = useGlobalKnowledgeBase()

  const handleDeleteDocument = useCallback((filename: string) => {
    if (onDeleteDocument) {
      onDeleteDocument(filename)
    }
  }, [onDeleteDocument])

  const handleRefresh = async () => {
    await refreshGlobalKB()
    onRefresh?.()
  }

  // Loading state
  if (isLoading && !globalKB) {
    return (
      <div className="document-panel loading">
        <div className="empty-state">
          <ServerIcon className="empty-icon spinning" />
          <p className="empty-text">Loading knowledge base...</p>
          <p className="empty-hint">Please wait while we initialize the system</p>
        </div>
      </div>
    )
  }

  // Error state
  if (hasError) {
    return (
      <div className="document-panel error">
        <div className="empty-state">
          <ExclamationTriangleIcon className="empty-icon error" />
          <p className="empty-text">Knowledge base error</p>
          <p className="empty-hint">{error || 'Failed to load knowledge base'}</p>
        </div>
      </div>
    )
  }

  // Initializing state
  if (isInitializing) {
    return (
      <div className="document-panel initializing">
        <div className="empty-state">
          <ServerIcon className="empty-icon spinning" />
          <p className="empty-text">Initializing knowledge base...</p>
          <p className="empty-hint">Setting up knowledge base documents and embeddings</p>
        </div>
      </div>
    )
  }

  // No documents state (shouldn't happen with global KB, but just in case)
  if (!hasDocuments) {
    return (
      <div className="document-panel empty">
        <div className="empty-state">
          <DocumentIcon className="empty-icon" />
          <p className="empty-text">No documents available</p>
          <p className="empty-hint">Upload a document to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="document-panel">
      <div className="document-panel-header">
        <div className="kb-info">
          <SparklesIcon className="rag-icon" />
          <div>
            <h3 className="kb-title">Global Knowledge Base</h3>
            <p className="kb-subtitle">
              {globalKB?.document_count} document{globalKB?.document_count !== 1 ? 's' : ''} • {globalKB?.chunk_count} chunks
              {isLoading && <span className="updating-indicator"> • Updating...</span>}
              {isAutoRefreshing && !isLoading && <span className="auto-refresh-indicator"> • Auto-refreshing...</span>}
            </p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          className="refresh-button"
          title="Refresh knowledge base"
          disabled={isLoading}
        >
          <ArrowPathIcon className={`refresh-icon ${isLoading || isAutoRefreshing ? 'spinning' : ''}`} />
        </button>
      </div>

      <div className="kb-status">
        <div className="kb-indicator ready">
          <div className="kb-dot"></div>
          <span>Knowledge base ready</span>
        </div>
        <p className="kb-description">
          {globalKB?.description}
        </p>
      </div>

      {/* Original Documents Section */}
      {globalKB && globalKB.documents.length > 0 && (
        <div className="documents-section">
          <h4 className="section-title">Original Documents</h4>
          <div className="documents-list">
            {globalKB.documents.map((document, index) => (
              <div key={`original-${index}`} className="document-item original">
                <DocumentIcon className="document-icon" />
                <div className="document-info">
                  <span className="document-name">{document}</span>
                  <span className="document-status">✓ Pre-loaded</span>
                </div>
                <div className="document-type-badge">Original</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* User Uploaded Documents Section */}
      {globalKB && globalKB.user_uploaded_documents.length > 0 && (
        <div className="documents-section">
          <h4 className="section-title">Your Uploaded Documents</h4>
          <div className="documents-list">
            {globalKB.user_uploaded_documents.map((document, index) => (
              <div key={`user-${index}`} className="document-item user-uploaded">
                <DocumentIcon className="document-icon" />
                <div className="document-info">
                  <span className="document-name">{document}</span>
                  <span className="document-status">✓ Indexed</span>
                </div>
                <button
                  onClick={() => handleDeleteDocument(document)}
                  className="delete-button"
                  title={`Delete ${document}`}
                  disabled={isDeleting === document}
                >
                  {isDeleting === document ? (
                    <div className="loading-spinner"></div>
                  ) : (
                    <TrashIcon className="delete-icon" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

             {/* Upload prompt if no user documents */}
       {globalKB && globalKB.user_uploaded_documents.length === 0 && (
         <div className="upload-prompt">
           <p className="prompt-text">Upload documents to add to the knowledge base</p>
           <p className="prompt-hint">Your uploaded documents will be available to everyone</p>
         </div>
       )}


     </div>
   )
 } 