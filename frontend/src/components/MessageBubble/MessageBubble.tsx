import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import type { Message } from '../../types'
import './MessageBubble.css'

interface MessageBubbleProps {
  message: Message
  index: number
}

const MemoizedMarkdown = memo(({ content }: { content: string }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm, remarkMath]}
    rehypePlugins={[rehypeKatex]}
    skipHtml={true}
    components={{
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      code({ inline, className, children, ...props }: any) {
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
), (prevProps, nextProps) => prevProps.content === nextProps.content)

export const MessageBubble = ({ message, index }: MessageBubbleProps) => {
  return (
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
} 