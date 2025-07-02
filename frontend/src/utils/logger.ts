const isDevelopment = import.meta.env.DEV

export const logger = {
  debug: (message: string, ...args: unknown[]) => {
    if (isDevelopment) {
      console.log(`[DEBUG] ${message}`, ...args)
    }
  },
  
  info: (message: string, ...args: unknown[]) => {
    if (isDevelopment) {
      console.info(`[INFO] ${message}`, ...args)
    }
  },
  
  warn: (message: string, ...args: unknown[]) => {
    console.warn(`[WARN] ${message}`, ...args)
  },
  
  error: (message: string, ...args: unknown[]) => {
    console.error(`[ERROR] ${message}`, ...args)
  }
}

// Helper for logging API requests in development
export const logApiRequest = (endpoint: string, request: Record<string, unknown>) => {
  if (isDevelopment) {
    console.group(`🌐 API Request: ${endpoint}`)
    console.log('Request:', request)
    console.groupEnd()
  }
}

// Helper for logging API responses in development  
export const logApiResponse = (endpoint: string, response: Record<string, unknown>) => {
  if (isDevelopment) {
    console.group(`✅ API Response: ${endpoint}`)
    console.log('Response:', response)
    console.groupEnd()
  }
} 