import { KeyIcon } from '@heroicons/react/24/solid'
import './WelcomeSection.css'

interface WelcomeSectionProps {
  apiKey: string
  onEnterApiKey: () => void
}

export const WelcomeSection = ({ apiKey, onEnterApiKey }: WelcomeSectionProps) => {
  return (
    <div className="welcome-section">
      <div>
        <h2 className="welcome-title">Welcome to OpenAI Chat!</h2>
        <p className="welcome-text">
          {apiKey ? 'Start a conversation below.' : 'Please enter your API key to get started.'}
        </p>
        {!apiKey && (
          <button
            onClick={onEnterApiKey}
            className="enter-key-button"
          >
            <KeyIcon className="api-key-icon" />
            Enter API Key
          </button>
        )}
      </div>
    </div>
  )
} 