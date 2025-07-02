import React, { useEffect } from 'react'
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import './ConfirmationModal.css'

interface ConfirmationModalProps {
  isOpen: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  type?: 'danger' | 'warning' | 'info'
  isLoading?: boolean
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  type = 'danger',
  isLoading = false
}) => {
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) {
        onCancel()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onCancel, isLoading])

  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isLoading) {
      onCancel()
    }
  }

  const getIconColorClass = () => {
    switch (type) {
      case 'danger':
        return 'icon-danger'
      case 'warning':
        return 'icon-warning'
      case 'info':
        return 'icon-info'
      default:
        return 'icon-danger'
    }
  }

  const getConfirmButtonClass = () => {
    switch (type) {
      case 'danger':
        return 'confirm-button-danger'
      case 'warning':
        return 'confirm-button-warning'
      case 'info':
        return 'confirm-button-info'
      default:
        return 'confirm-button-danger'
    }
  }

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-container" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-header">
          <div className="modal-icon-container">
            <ExclamationTriangleIcon className={`modal-icon ${getIconColorClass()}`} />
          </div>
          <div className="modal-title-section">
            <h3 id="modal-title" className="modal-title">{title}</h3>
            <p className="modal-message">{message}</p>
          </div>
          <button
            onClick={onCancel}
            className="modal-close-button"
            disabled={isLoading}
            aria-label="Close modal"
          >
            <XMarkIcon className="close-icon" />
          </button>
        </div>
        
        <div className="modal-actions">
          <button
            onClick={onCancel}
            className="cancel-button"
            disabled={isLoading}
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`confirm-button ${getConfirmButtonClass()}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="loading-spinner-small"></div>
                Deleting...
              </>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  )
} 