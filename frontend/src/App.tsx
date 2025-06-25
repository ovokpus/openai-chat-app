import { KeyIcon, PaperAirplaneIcon } from '@heroicons/react/24/solid'
import { useChat } from './hooks/useChat'
import { WelcomeSection, MessageBubble, LoadingIndicator } from './components'
import 'katex/dist/katex.min.css'
import './App.css'

function App() {
  const {
    messages,
    input,
    setInput,
    isLoading,
    apiKey,
    setApiKey,
    showApiKey,
    setShowApiKey,
    messagesEndRef,
    handleSubmit
  } = useChat()

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-container">
          <div>
            <h1 className="header-title">OpenAI Chat</h1>
          </div>
          <div>
            <button
              onClick={() => setShowApiKey(!showApiKey)}
              className="api-key-button"
            >
              <KeyIcon className="api-key-icon" />
              <span className="hidden-mobile">API Key</span>
            </button>
          </div>
        </div>
      </header>

      {/* API Key Input Section */}
      {showApiKey && (
        <div className="api-key-section">
          <div className="api-key-form">
            <label className="api-key-label">
              OpenAI API Key:
            </label>
            <input
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="api-key-input"
            />
            <button
              onClick={() => setShowApiKey(false)}
              className="done-button"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Main Chat Container */}
      <main className="main-container">
        <div className="chat-container">
          
          {/* Messages Area */}
          <div className="messages-area">
            {messages.length === 0 && (
              <WelcomeSection 
                apiKey={apiKey} 
                onEnterApiKey={() => setShowApiKey(true)} 
              />
            )}
            
            {messages.map((message, index) => (
              <MessageBubble 
                key={index} 
                message={message} 
                index={index} 
              />
            ))}
            
            {isLoading && <LoadingIndicator />}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="input-area">
            <form onSubmit={handleSubmit} className="input-form">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  className="message-input"
                  disabled={isLoading || !apiKey}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading || !apiKey || !input.trim()}
                className="send-button"
              >
                <PaperAirplaneIcon className="send-icon" />
                <span className="hidden-mobile">
                  {isLoading ? 'Sending...' : 'Send'}
                </span>
              </button>
            </form>
            
            {!apiKey && (
              <p className="help-text">
                Please enter your OpenAI API key to start chatting
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
