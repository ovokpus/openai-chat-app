import React from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';
import { WelcomeSection } from '../WelcomeSection/WelcomeSection';
import { MessageBubble } from '../MessageBubble/MessageBubble';
import { LoadingIndicator } from '../LoadingIndicator/LoadingIndicator';
import type { Message } from '../../types';
import './ChatContainer.css';

interface ChatContainerProps {
  messages: Message[];
  input: string;
  setInput: (input: string) => void;
  isLoading: boolean;
  apiKey: string;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  hasRAG: boolean;
  ragMode: boolean;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  input,
  setInput,
  isLoading,
  apiKey,
  onSubmit,
  messagesEndRef,
  hasRAG,
  ragMode
}) => {
  return (
    <div className="chat-container">
      <div className="messages-area">
        {messages.length === 0 && (
          <WelcomeSection 
            apiKey={apiKey}
            onEnterApiKey={() => {}}
            hasRAG={hasRAG}
            ragMode={ragMode}
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

      <div className="input-area">
        <form onSubmit={onSubmit} className="input-form">
          <div className="input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="message-input"
              disabled={!apiKey || isLoading}
            />
          </div>
          <button
            type="submit"
            className="send-button"
            disabled={!input.trim() || !apiKey || isLoading}
          >
            <PaperAirplaneIcon className="send-icon" />
          </button>
        </form>
      </div>
    </div>
  );
}; 