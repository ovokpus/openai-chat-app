import React from 'react'
import './NotificationBanner.css'

interface NotificationBannerProps {
  type: 'success' | 'error'
  message: string
  show: boolean
  onClose: () => void
}

export const NotificationBanner: React.FC<NotificationBannerProps> = ({
  type,
  message,
  show,
  onClose
}) => {
  if (!show) return null

  return (
    <div className={`notification-banner ${type}`}>
      <div className="notification-content">
        <span>
          {type === 'success' ? '✅' : '❌'} {message}
        </span>
        <button
          onClick={onClose}
          className="notification-close"
        >
          ×
        </button>
      </div>
    </div>
  )
} 