import { useState, useRef, useEffect, memo } from 'react'
import { PaperAirplaneIcon, KeyIcon } from '@heroicons/react/24/solid'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
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
          developer_message: `You are a helpful AI assistant. When providing responses:

FORMATTING RULES:
- Use proper markdown formatting for all text
- For mathematical expressions, ALWAYS use standard markdown math delimiters:
  - Inline math: $expression$ 
  - Display math: $$expression$$
- NEVER use brackets [ ] or parentheses ( ) around math expressions
- NEVER use \\[ \\] LaTeX delimiters
- Use **bold** for emphasis and *italics* when needed
- Use numbered lists (1. 2. 3.) and bullet points (- item) properly
- Use ### for headings when structuring responses

MATH EXAMPLES:
✅ CORRECT: The formula is $$\\frac{12}{4} = 3$$
❌ WRONG: The formula is [\\frac{12}{4} = 3]
❌ WRONG: The formula is (\\frac{12}{4} = 3)

Always format mathematical calculations using proper markdown math syntax with $$ delimiters.`,
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

    const MemoizedMarkdown = memo(({ content }: { content: string }) => (
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        skipHtml={true}
        components={{
        code({ inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '')
          return !inline ? (
            <pre className="code-block">
              <code className={className} {...props}>
                {String(children).replace(/\n$/, '')}
              </code>
            </pre>
          ) : (
            <code className="inline-code" {...props}>
              {children}
            </code>
          )
        },
        ol: ({ children }) => (
          <ol className="markdown-ordered-list">{children}</ol>
        ),
        ul: ({ children }) => (
          <ul className="markdown-unordered-list">{children}</ul>
        ),
        li: ({ children }) => (
          <li className="markdown-list-item">{children}</li>
        ),
        p: ({ children }) => (
          <p className="markdown-paragraph">{children}</p>
        ),
        h1: ({ children }) => (
          <h1 className="markdown-h1">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="markdown-h2">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="markdown-h3">{children}</h3>
        ),
              }}
      >
        {content}
      </ReactMarkdown>
  ), (prevProps, nextProps) => prevProps.content === nextProps.content);

  const renderMessage = (message: Message, index: number) => (
    <div key={index} className={`message-container ${message.role}`}>
      <div className="message-wrapper">
        <div className={`message-bubble ${message.role}`}>
          {message.role === 'assistant' ? (
            <MemoizedMarkdown content={message.content} />
          ) : (
            message.content
          )}
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
      <main className={`main-container ${showApiKey ? 'with-api-key' : ''}`}>
        <div className="chat-container">
          
          {/* Messages Area */}
          <div className="messages-area">
            {messages.length === 0 && renderWelcomeSection()}
            
            {messages.map((message, index) => renderMessage(message, index))}
            
            {isLoading && renderLoadingIndicator()}
            
            <div ref={messagesEndRef} />
          </div>
        </div>
      </main>

      {/* Input Area - Fixed at bottom */}
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
  )
}

export default App
