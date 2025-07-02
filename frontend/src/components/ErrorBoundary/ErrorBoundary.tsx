import React, { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import './ErrorBoundary.css'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('🚨 Error Boundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // Call optional error handler
    this.props.onError?.(error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="error-boundary">
          <div className="error-container">
            <div className="error-icon-container">
              <ExclamationTriangleIcon className="error-icon" />
            </div>
            
            <div className="error-content">
              <h1 className="error-title">Oops! Something went wrong</h1>
              <p className="error-description">
                We encountered an unexpected error. This usually happens when something goes 
                wrong with the application state or network connection.
              </p>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="error-details">
                  <summary className="error-summary">
                    Technical Details (Development Mode)
                  </summary>
                  <div className="error-stack">
                    <strong>Error:</strong> {this.state.error.message}
                    {this.state.error.stack && (
                      <pre className="stack-trace">{this.state.error.stack}</pre>
                    )}
                    {this.state.errorInfo && (
                      <>
                        <strong>Component Stack:</strong>
                        <pre className="stack-trace">{this.state.errorInfo.componentStack}</pre>
                      </>
                    )}
                  </div>
                </details>
              )}
              
              <div className="error-actions">
                <button 
                  onClick={this.handleReset}
                  className="error-button primary"
                  aria-label="Try again"
                >
                  <ArrowPathIcon className="button-icon" />
                  Try Again
                </button>
                
                <button 
                  onClick={this.handleReload}
                  className="error-button secondary"
                  aria-label="Reload page"
                >
                  Reload Page
                </button>
              </div>
              
              <div className="error-help">
                <p className="help-text">
                  If this problem persists:
                </p>
                <ul className="help-list">
                  <li>Check your internet connection</li>
                  <li>Clear your browser cache and cookies</li>
                  <li>Try refreshing the page</li>
                  <li>Contact support if the issue continues</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
} 