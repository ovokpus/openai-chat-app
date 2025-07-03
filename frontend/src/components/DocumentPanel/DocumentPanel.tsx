import React, { useState } from 'react'
import { DocumentIcon, TrashIcon, SparklesIcon, ExclamationTriangleIcon, XMarkIcon, CloudArrowDownIcon, ServerIcon } from '@heroicons/react/24/outline'
import type { SessionInfo } from '../../types'
import { deleteDocument } from '../../services/chatApi'
import './DocumentPanel.css'
import { CHAT_CONFIG } from '../../constants'

interface DocumentPanelProps {
  sessionInfo: SessionInfo | null
  onClearSession: () => void
  isLoading?: boolean
  apiKey: string
  onDocumentDeleted?: (documentName: string) => void
  ragMode: boolean
  isUsingBackup?: boolean
  sessionStatus?: 'no-session' | 'active' | 'backup'
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
  ragMode,
  isUsingBackup = false,
  sessionStatus = 'no-session'
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

  if (!sessionInfo || !ragMode) {
    return null;
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const handleDeleteDocument = async (documentName: string) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Document',
      message: `Are you sure you want to delete "${documentName}"? This action cannot be undone.`,
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
    const actionText = isUsingBackup ? 'clear the backup and all documents' : 'clear all documents';
    setConfirmDialog({
      isOpen: true,
      title: 'Clear All Documents',
      message: `Are you sure you want to ${actionText}? This action cannot be undone.`,
      onConfirm: () => {
        onClearSession();
        setConfirmDialog(prev => ({ ...prev, isOpen: false }));
      }
    });
  };

  // Check if session might be stale (created more than configured timeout)
  const sessionAge = Date.now() - new Date(sessionInfo.created_at).getTime()
  const isStaleSession = sessionAge > CHAT_CONFIG.SESSION_TIMEOUT // Use configured timeout (10 minutes)

  const getSessionStatusInfo = () => {
    switch (sessionStatus) {
      case 'active':
        return {
          icon: <ServerIcon className="status-icon active" />,
          text: 'Live Session',
          className: 'session-status active'
        };
      case 'backup':
        return {
          icon: <CloudArrowDownIcon className="status-icon backup" />,
          text: 'Backup Session',
          className: 'session-status backup'
        };
      default:
        return {
          icon: <SparklesIcon className="rag-icon" />,
          text: 'RAG Session',
          className: 'session-info'
        };
    }
  };

  const statusInfo = getSessionStatusInfo();

  return (
    <div className="document-panel">
      <div className="document-panel-header">
        <div className={statusInfo.className}>
          {statusInfo.icon}
          <div>
            <h3 className="session-title">{statusInfo.text} Active</h3>
            <p className="session-subtitle">
              {sessionInfo.document_count} document{sessionInfo.document_count !== 1 ? 's' : ''} loaded
              {isUsingBackup && ' (from backup)'}
            </p>
          </div>
        </div>
        <button
          onClick={handleClearAllDocuments}
          className="clear-button"
          title={isUsingBackup ? "Clear backup and all documents" : "Clear all documents"}
          disabled={isLoading}
        >
          <TrashIcon className="clear-icon" />
          Clear All
        </button>
      </div>

      {/* Backup Status Warning */}
      {isUsingBackup && (
        <div className="backup-warning">
          <CloudArrowDownIcon className="backup-icon" />
          <div className="backup-content">
            <p className="backup-text">Using Backup Session</p>
            <p className="backup-hint">Server session was lost due to serverless restart. RAG may not work - re-upload documents to restore full functionality.</p>
          </div>
        </div>
      )}

      {/* Session Age Warning */}
      {isStaleSession && !isUsingBackup && (
        <div className="session-warning">
          <ExclamationTriangleIcon className="warning-icon" />
          <div className="warning-content">
            <p className="warning-text">Session may have expired</p>
            <p className="warning-hint">Production sessions expire due to serverless function restarts. If RAG chat isn't working, re-upload your documents.</p>
          </div>
        </div>
      )}

      <div className="documents-list">
        {sessionInfo.documents.map((document, index) => (
          <div key={index} className="document-item">
            <DocumentIcon className="document-icon" />
            <div className="document-info">
              <h4 className="document-name">{document}</h4>
              {isUsingBackup && (
                <span className="backup-badge">backup</span>
              )}
            </div>
            {!isUsingBackup && (
              <button
                onClick={() => handleDeleteDocument(document)}
                className="delete-document-button"
                disabled={isLoading || deletingDocument === document}
                title={`Delete ${document}`}
              >
                {deletingDocument === document ? (
                  <div className="button-spinner" />
                ) : (
                  <XMarkIcon className="delete-icon" />
                )}
              </button>
            )}
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