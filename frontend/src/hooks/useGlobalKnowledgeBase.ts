import { useState, useEffect } from 'react'

interface GlobalKnowledgeBase {
  status: 'not_initialized' | 'error' | 'ready'
  initialized: boolean
  error: string | null
  documents: string[]
  document_count: number
  chunk_count: number
  description: string
}

export const useGlobalKnowledgeBase = () => {
  const [globalKB, setGlobalKB] = useState<GlobalKnowledgeBase | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchGlobalKB = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await fetch('/api/global-knowledge-base')
      if (!response.ok) {
        throw new Error(`Failed to fetch global knowledge base: ${response.status}`)
      }
      
      const data = await response.json()
      setGlobalKB(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      console.error('Error fetching global knowledge base:', errorMessage)
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  // Poll for initialization status
  useEffect(() => {
    fetchGlobalKB()
    
    // Poll every 5 seconds if not ready
    const interval = setInterval(() => {
      if (!globalKB || globalKB.status !== 'ready') {
        fetchGlobalKB()
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [globalKB?.status])

  const isReady = globalKB?.status === 'ready'
  const hasError = globalKB?.status === 'error' || error !== null
  const isInitializing = globalKB?.status === 'not_initialized' || isLoading

  return {
    globalKB,
    isLoading,
    error,
    isReady,
    hasError,
    isInitializing,
    refresh: fetchGlobalKB
  }
} 