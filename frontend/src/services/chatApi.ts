import type { Message } from '../types'

const DEVELOPER_MESSAGE = `You are a helpful AI assistant. When providing responses:

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

Always format mathematical calculations using proper markdown math syntax with $$ delimiters.`

export interface ChatRequest {
  userMessage: string
  apiKey: string
  model?: string
}

export const sendChatMessage = async (
  { userMessage, apiKey, model = "gpt-4o-mini" }: ChatRequest
): Promise<ReadableStreamDefaultReader<Uint8Array> | null> => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_message: userMessage,
      developer_message: DEVELOPER_MESSAGE,
      api_key: apiKey,
      model
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return response.body?.getReader() || null
} 