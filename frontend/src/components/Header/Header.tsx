import React from 'react';
import { KeyIcon, SparklesIcon } from '@heroicons/react/24/solid';
import './Header.css';

interface HeaderProps {
  showApiKey: boolean;
  setShowApiKey: (show: boolean) => void;
  apiKey: string;
  setApiKey: (key: string) => void;
  hasRAG: boolean;
  ragMode: boolean;
  onToggleRAG: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  showApiKey,
  setShowApiKey,
  apiKey,
  setApiKey,
  hasRAG,
  ragMode,
  onToggleRAG
}) => {
  return (
    <>
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="app-title">OpenAI Chat</h1>
            {hasRAG && (
              <div className="rag-toggle">
                <button
                  onClick={onToggleRAG}
                  className={`rag-toggle-button ${ragMode ? 'active' : ''}`}
                  title={ragMode ? 'Disable RAG mode' : 'Enable RAG mode'}
                >
                  <SparklesIcon className="rag-toggle-icon" />
                  {ragMode ? 'RAG ON' : 'RAG OFF'}
                </button>
              </div>
            )}
          </div>
          <button
            className="api-key-button"
            onClick={() => setShowApiKey(!showApiKey)}
            title={apiKey ? "API Key configured" : "Set API Key"}
          >
            <KeyIcon className={`key-icon ${apiKey ? 'configured' : ''}`} />
          </button>
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
    </>
  );
}; 