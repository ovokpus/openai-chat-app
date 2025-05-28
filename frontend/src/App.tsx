import { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon, KeyIcon } from '@heroicons/react/24/solid'
import './App.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !apiKey) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_message: userMessage,
          developer_message: "You are a helpful AI assistant.",
          api_key: apiKey,
          model: "gpt-4o-mini"
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          assistantMessage += chunk
          setMessages(prev => {
            const newMessages = [...prev]
            const lastMessage = newMessages[newMessages.length - 1]
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.content = assistantMessage
              return [...newMessages]
            } else {
              return [...newMessages, { role: 'assistant', content: assistantMessage }]
            }
          })
        }
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, there was an error processing your request.' 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const renderWelcomeSection = () => (
    <div className="welcome-section">
      <div>
        <h2 className="welcome-title">Welcome to OpenAI Chat!</h2>
        <p className="welcome-text">
          {apiKey ? 'Start a conversation below.' : 'Please enter your API key to get started.'}
        </p>
        {!apiKey && (
          <button
            onClick={() => setShowApiKey(true)}
            className="enter-key-button"
          >
            <KeyIcon className="api-key-icon" />
            Enter API Key
          </button>
        )}
      </div>
    </div>
  )

  const renderMessage = (message: Message, index: number) => (
    <div key={index} className={`message-container ${message.role}`}>
      <div className="message-wrapper">
        <div className={`message-bubble ${message.role}`}>
          {message.content}
        </div>
        <div className={`message-label ${message.role}`}>
          {message.role === 'user' ? 'You' : 'Assistant'}
        </div>
      </div>
    </div>
  )

  const renderLoadingIndicator = () => (
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
            {messages.length === 0 && renderWelcomeSection()}
            
            {messages.map((message, index) => renderMessage(message, index))}
            
            {isLoading && renderLoadingIndicator()}
            
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
