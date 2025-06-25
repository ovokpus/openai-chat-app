export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatState {
  messages: Message[]
  input: string
  isLoading: boolean
  apiKey: string
  showApiKey: boolean
} 