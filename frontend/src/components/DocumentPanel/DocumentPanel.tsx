import React, { useState } from 'react'
import { createPortal } from 'react-dom'
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
  React.useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  return createPortal(
    <div className="confirmation-overlay" onClick={handleOverlayClick}>
      <div className="confirmation-dialog">
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="confirmation-buttons">
          <button onClick={onCancel} className="cancel-button">Cancel</button>
          <button onClick={onConfirm} className="confirm-button">Delete</button>
        </div>
      </div>
    </div>,
    document.body
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
            <p className="backup-text">Session Restored from Backup</p>
            <p className="backup-hint">Your documents are available, but you may need to re-upload them if RAG chat doesn't work properly.</p>
          </div>
        </div>
      )}

      {/* Session Age Warning */}
      {isStaleSession && !isUsingBackup && (
        <div className="session-warning">
          <ExclamationTriangleIcon className="warning-icon" />
          <div className="warning-content">
            <p className="warning-text">Session May Be Expired</p>
            <p className="warning-hint">If your questions aren't getting document-based answers, try re-uploading your documents.</p>
          </div>
        </div>
      )}

      <div className="documents-list">
        <h4 className="documents-title">Your Documents</h4>
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
                  <TrashIcon className="clear-icon" />
                )}
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="rag-info-section">
        <div className={`rag-indicator ${ragMode ? 'active' : ''}`}>
          <div className="rag-dot"></div>
          <span>{ragMode ? 'Smart Answers Active' : 'Basic Chat Mode'}</span>
        </div>
        <p className="rag-description">
          {ragMode 
            ? "🧠 Your questions will be answered using information from your uploaded documents, providing more accurate and relevant responses."
            : "💬 Switch to RAG mode in the header to get answers based on your document content."
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