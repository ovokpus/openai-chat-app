import React, { useCallback, useMemo } from 'react'
import { CheckCircleIcon, ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import './NotificationManager.css'

interface NotificationProps {
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  isVisible: boolean
  onClose: () => void
  autoClose?: boolean
  duration?: number
}

interface NotificationManagerProps {
  successNotification?: {
    message: string
    isVisible: boolean
    onClose: () => void
  }
  errorNotification?: {
    message: string
    isVisible: boolean
    onClose: () => void
  }
  warningNotification?: {
    message: string
    isVisible: boolean
    onClose: () => void
  }
}

const Notification: React.FC<NotificationProps> = ({
  type,
  message,
  isVisible,
  onClose,
  autoClose = true,
  duration = 5000
}) => {
  const handleClose = useCallback(() => {
    onClose()
  }, [onClose])

  const notificationConfig = useMemo(() => {
    switch (type) {
      case 'success':
        return {
          icon: CheckCircleIcon,
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          iconColor: 'text-green-400',
          textColor: 'text-green-800',
          closeColor: 'text-green-500'
        }
      case 'error':
        return {
          icon: ExclamationTriangleIcon,
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          iconColor: 'text-red-400',
          textColor: 'text-red-800',
          closeColor: 'text-red-500'
        }
      case 'warning':
        return {
          icon: ExclamationTriangleIcon,
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          iconColor: 'text-yellow-400',
          textColor: 'text-yellow-800',
          closeColor: 'text-yellow-500'
        }
      default:
        return {
          icon: ExclamationTriangleIcon,
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          iconColor: 'text-blue-400',
          textColor: 'text-blue-800',
          closeColor: 'text-blue-500'
        }
    }
  }, [type])

  // Auto-close functionality
  React.useEffect(() => {
    if (isVisible && autoClose) {
      const timer = setTimeout(() => {
        onClose()
      }, duration)
      
      return () => clearTimeout(timer)
    }
  }, [isVisible, autoClose, duration, onClose])

  if (!isVisible) return null

  const IconComponent = notificationConfig.icon

  return (
    <div className={`notification notification-${type} ${isVisible ? 'visible' : ''}`}>
      <div className="notification-content">
        <div className="notification-icon">
          <IconComponent className="icon" />
        </div>
        <div className="notification-message">
          {message}
        </div>
        <button
          onClick={handleClose}
          className="notification-close"
          aria-label="Close notification"
        >
          <XMarkIcon className="close-icon" />
        </button>
      </div>
      {autoClose && (
        <div 
          className="notification-progress"
          style={{
            animationDuration: `${duration}ms`
          }}
        />
      )}
    </div>
  )
}

export const NotificationManager: React.FC<NotificationManagerProps> = ({
  successNotification,
  errorNotification,
  warningNotification
}) => {
  const hasNotifications = useMemo(() => {
    return successNotification?.isVisible || 
           errorNotification?.isVisible || 
           warningNotification?.isVisible
  }, [successNotification?.isVisible, errorNotification?.isVisible, warningNotification?.isVisible])

  if (!hasNotifications) return null

  return (
    <div className="notification-manager">
      <div className="notifications-container">
        {successNotification?.isVisible && (
          <Notification
            type="success"
            message={successNotification.message}
            isVisible={successNotification.isVisible}
            onClose={successNotification.onClose}
          />
        )}
        
        {errorNotification?.isVisible && (
          <Notification
            type="error"
            message={errorNotification.message}
            isVisible={errorNotification.isVisible}
            onClose={errorNotification.onClose}
            autoClose={false} // Don't auto-close errors
          />
        )}
        
        {warningNotification?.isVisible && (
          <Notification
            type="warning"
            message={warningNotification.message}
            isVisible={warningNotification.isVisible}
            onClose={warningNotification.onClose}
          />
        )}
      </div>
    </div>
  )
} 