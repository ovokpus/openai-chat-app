import './LoadingIndicator.css'

export const LoadingIndicator = () => {
  return (
    <div className="loading-container">
      <div className="loading-bubble">
        <div className="loading-dots">
          <div className="loading-dot"></div>
          <div className="loading-dot"></div>
          <div className="loading-dot"></div>
        </div>
        <span className="loading-text">Thinking...</span>
      </div>
    </div>
  )
} 