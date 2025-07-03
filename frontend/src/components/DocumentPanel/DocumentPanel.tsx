import React, { useState } from 'react'
import { DocumentIcon, TrashIcon, SparklesIcon, ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import type { SessionInfo } from '../../types'
import { deleteDocument } from '../../services/chatApi'
import './DocumentPanel.css'

interface DocumentPanelProps {
  sessionInfo: SessionInfo | null
  onClearSession: () => void
  isLoading?: boolean
  apiKey: string
  onDocumentDeleted?: (documentName: string) => void
  ragMode: boolean
}

interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  message: string
  onConfirm: () => void
  onCancel: () => void
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel
}) => {
  if (!isOpen) return null;

  return (
    <div className="confirm-dialog-overlay">
      <div className="confirm-dialog">
        <h3 className="confirm-title">{title}</h3>
        <p className="confirm-message">{message}</p>
        <div className="confirm-buttons">
          <button onClick={onCancel} className="cancel-button">Cancel</button>
          <button onClick={onConfirm} className="confirm-button">Delete</button>
        </div>
      </div>
    </div>
  );
};

export const DocumentPanel: React.FC<DocumentPanelProps> = ({
  sessionInfo,
  onClearSession,
  isLoading = false,
  apiKey,
  onDocumentDeleted,
  ragMode
}) => {
  const [deletingDocument, setDeletingDocument] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });

  if (!sessionInfo || sessionInfo.document_count === 0) {
    return (
      <div className="document-panel empty">
        <div className="empty-state">
          <DocumentIcon className="empty-icon" />
          <p className="empty-text">No documents uploaded</p>
          <p className="empty-hint">Upload a document to start chatting with your files</p>
        </div>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const handleDeleteDocument = async (documentName: string) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Document',
      message: `Are you sure you want to delete "${documentName}"?`,
      onConfirm: async () => {
        try {
          setDeletingDocument(documentName);
          const result = await deleteDocument(sessionInfo.session_id, documentName, apiKey);
          if (result.success) {
            onDocumentDeleted?.(documentName);
          }
        } catch (error) {
          console.error('Failed to delete document:', error);
        } finally {
          setDeletingDocument(null);
          setConfirmDialog(prev => ({ ...prev, isOpen: false }));
        }
      }
    });
  };

  const handleClearAllDocuments = () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Clear All Documents',
      message: 'Are you sure you want to clear all documents? This action cannot be undone.',
      onConfirm: () => {
        onClearSession();
        setConfirmDialog(prev => ({ ...prev, isOpen: false }));
      }
    });
  };

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
          onClick={handleClearAllDocuments}
          className="clear-button"
          title="Clear all documents"
          disabled={isLoading}
        >
          <TrashIcon className="clear-icon" />
          Clear All
        </button>
      </div>

      {isStaleSession && (
        <div className="session-warning">
          <ExclamationTriangleIcon className="warning-icon" />
          <div className="warning-content">
            <p className="warning-text">Session may have expired</p>
            <p className="warning-hint">If RAG chat isn't working, try uploading your document again</p>
          </div>
        </div>
      )}

      <div className="documents-list">
        {sessionInfo.documents.map((document, index) => (
          <div key={index} className="document-item">
            <DocumentIcon className="document-icon" />
            <div className="document-info">
              <h4 className="document-name">{document}</h4>
              <span className="document-status">Added to chat context</span>
            </div>
            <button
              onClick={() => handleDeleteDocument(document)}
              className="delete-document-button"
              disabled={isLoading || deletingDocument === document}
              title="Delete document"
            >
              {deletingDocument === document ? (
                <div className="button-spinner" />
              ) : (
                <XMarkIcon className="delete-icon" />
              )}
            </button>
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
        <div className={`rag-indicator ${ragMode ? 'active' : ''}`}>
          <div className="rag-dot"></div>
          <span>{ragMode ? 'RAG mode enabled' : 'RAG mode disabled'}</span>
        </div>
        <p className="rag-description">
          {ragMode 
            ? "Your questions will be answered using content from uploaded documents"
            : "Toggle RAG mode in the header to use document content for answers"
          }
        </p>
      </div>

      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog(prev => ({ ...prev, isOpen: false }))}
      />
    </div>
  )
} 