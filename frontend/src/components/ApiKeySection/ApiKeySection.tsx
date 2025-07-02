import React from 'react'
import './ApiKeySection.css'

interface ApiKeySectionProps {
  show: boolean
  apiKey: string
  onApiKeyChange: (value: string) => void
  onDone: () => void
}

export const ApiKeySection: React.FC<ApiKeySectionProps> = ({
  show,
  apiKey,
  onApiKeyChange,
  onDone
}) => {
  if (!show) return null

  return (
    <div className="api-key-section">
      <div className="api-key-form">
        <label className="api-key-label">
          OpenAI API Key:
        </label>
        <input
          type="password"
          placeholder="sk-..."
          value={apiKey}
          onChange={(e) => onApiKeyChange(e.target.value)}
          className="api-key-input"
        />
        <button
          onClick={onDone}
          className="done-button"
        >
          Done
        </button>
      </div>
    </div>
  )
} 