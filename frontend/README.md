# OpenAI Chat Frontend

Modern React application with TypeScript providing an intelligent chat interface featuring document upload, RAG (Retrieval-Augmented Generation) capabilities, and responsive design.

## Overview

This frontend application delivers a comprehensive user experience for AI-powered conversations with document analysis capabilities. Built with modern web technologies, it provides seamless interaction with the OpenAI Chat API backend.

## Features

### Core Functionality
- **Interactive Chat Interface**: Real-time messaging with streaming responses
- **Document Upload**: Drag-and-drop support for multiple file formats
- **RAG Mode**: Toggle between standard chat and document-enhanced conversations
- **Session Management**: Persistent conversation history and document tracking
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices

### Document Processing
- **Multi-Format Support**: PDF, DOCX, XLSX, XLS, PPTX, TXT, MD, CSV, HTML
- **Visual Upload Area**: Intuitive drag-and-drop interface with progress indicators
- **File Management**: View uploaded documents and manage session data
- **Processing Status**: Real-time feedback during document processing

### User Interface
- **Modern Design**: Clean, professional interface with dark theme
- **Component Architecture**: Modular, reusable React components
- **TypeScript Integration**: Full type safety and enhanced development experience
- **Accessibility**: WCAG-compliant design with keyboard navigation support

## Technology Stack

### Core Technologies
- **React**: 18.2.0 - Modern component-based UI framework
- **TypeScript**: 5.2.2 - Type-safe JavaScript development
- **Vite**: 5.1.0 - Fast build tool and development server
- **CSS Modules**: Scoped styling with component isolation

### Key Dependencies
- **@heroicons/react**: 2.1.1 - Professional icon library
- **react-markdown**: 10.1.0 - Markdown rendering support
- **axios**: HTTP client for API communication
- **vite-plugin-compression2**: Asset compression for production

### Development Tools
- **ESLint**: Code quality and consistency enforcement
- **TypeScript ESLint**: TypeScript-specific linting rules
- **PostCSS**: Advanced CSS processing capabilities

## Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── ChatContainer/    # Main chat interface
│   │   ├── DocumentPanel/    # Document management sidebar
│   │   ├── DocumentUpload/   # File upload component
│   │   ├── Header/          # Application header
│   │   ├── LoadingIndicator/ # Loading animations
│   │   ├── MessageBubble/   # Chat message display
│   │   ├── WelcomeSection/  # Initial welcome screen
│   │   └── index.ts         # Component exports
│   ├── hooks/               # Custom React hooks
│   │   ├── useChat.ts       # Chat functionality logic
│   │   └── useRAG.ts        # RAG mode management
│   ├── services/            # API communication layer
│   │   ├── chat/            # Chat API services
│   │   ├── documents/       # Document management
│   │   ├── session/         # Session management
│   │   └── index.ts         # Service exports
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts         # Shared type exports
│   ├── constants/           # Application constants
│   │   └── index.ts         # Configuration values
│   ├── App.tsx              # Main application component
│   ├── App.css              # Global styles
│   ├── main.tsx             # Application entry point
│   └── index.css            # CSS reset and variables
├── public/                  # Static assets
├── dist/                    # Production build output
├── package.json             # Dependencies and scripts
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite build configuration
└── eslint.config.js         # ESLint configuration
```

## Installation and Setup

### Prerequisites
- **Node.js**: 16.0 or higher
- **npm**: 7.0 or higher
- **Git**: Latest version

### Local Development

1. **Clone Repository**
   ```bash
   git clone https://github.com/[your-username]/openai-chat-app.git
   cd openai-chat-app/frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Development Server**
   ```bash
   npm run dev
   ```

4. **Access Application**
   - Local development: http://localhost:3000
   - Network access: Use `--host` flag for external access

### Environment Configuration

The frontend automatically connects to the backend API. For custom configurations, create `.env` file:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_DEBUG=false
```

## Component Architecture

### Core Components

#### ChatContainer
Primary chat interface component managing conversation flow.

**Features:**
- Message history display
- Streaming response handling
- Input validation and submission
- Scroll management for long conversations

**Props:**
```typescript
interface ChatContainerProps {
  apiKey: string;
  sessionId?: string;
  ragEnabled: boolean;
  onMessageSent?: (message: string) => void;
}
```

#### DocumentUpload
Drag-and-drop file upload component with validation.

**Features:**
- Multi-format file support
- Visual drag-and-drop area
- File size and type validation
- Upload progress tracking
- Error handling and user feedback

**Supported Formats:**
```typescript
const SUPPORTED_FORMATS = {
  '.pdf': 'PDF Document',
  '.docx': 'Word Document', 
  '.xlsx': 'Excel Spreadsheet',
  '.xls': 'Excel Spreadsheet (Legacy)',
  '.pptx': 'PowerPoint Presentation',
  '.txt': 'Text File',
  '.md': 'Markdown File',
  '.csv': 'CSV File',
  '.html': 'HTML Document'
};
```

#### DocumentPanel
Sidebar component for document and session management.

**Features:**
- Uploaded document listing
- Session information display
- Document deletion functionality
- RAG mode toggle
- Session cleanup options

#### MessageBubble
Individual message display component with role-based styling.

**Features:**
- User/assistant message differentiation
- Markdown content rendering
- Timestamp display
- Loading states for streaming responses

### Custom Hooks

#### useChat
Manages chat functionality and state.

```typescript
interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string) => void;
  clearChat: () => void;
}
```

#### useRAG
Handles RAG mode state and document context.

```typescript
interface UseRAGReturn {
  ragEnabled: boolean;
  hasDocuments: boolean;
  toggleRAG: () => void;
  documentCount: number;
}
```

## API Integration

### Service Layer
Centralized API communication through service modules.

#### Chat Service
```typescript
class ChatService {
  async sendMessage(request: ChatRequest): Promise<Response>;
  async streamResponse(request: ChatRequest): Promise<ReadableStream>;
}
```

#### Document Service  
```typescript
class DocumentService {
  async uploadDocument(file: File, sessionId?: string): Promise<UploadResponse>;
  async getDocuments(sessionId?: string): Promise<Document[]>;
  async deleteDocument(documentId: string): Promise<void>;
}
```

#### Session Service
```typescript
class SessionService {
  async createSession(): Promise<Session>;
  async getSession(sessionId: string): Promise<Session>;
  async deleteSession(sessionId: string): Promise<void>;
}
```

## Development Guidelines

### Code Standards
- **TypeScript**: Strict mode enabled with comprehensive type coverage
- **ESLint**: Extended configuration with React and TypeScript rules
- **Component Design**: Functional components with hooks
- **Styling**: CSS modules with BEM methodology
- **Testing**: Component and integration testing with modern practices

### Performance Optimization
- **Code Splitting**: Automatic route and component-based splitting
- **Bundle Analysis**: Webpack bundle analyzer integration
- **Asset Optimization**: Image and font optimization
- **Caching**: Proper HTTP caching headers for static assets

### Accessibility Standards
- **WCAG 2.1**: AA compliance level
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Readers**: ARIA labels and semantic HTML
- **Color Contrast**: High contrast ratios for readability

## Build and Deployment

### Development Build
```bash
npm run dev
```
**Features:**
- Hot module replacement
- Source maps for debugging
- Development error overlay
- Fast refresh for React components

### Production Build
```bash
npm run build
```
**Output:**
- Optimized bundle sizes (~460KB JS, ~59KB CSS)
- Asset compression and minification
- Source maps for production debugging
- Service worker for caching

### Build Analysis
```bash
npm run build:analyze
```
**Reports:**
- Bundle size breakdown
- Dependency analysis
- Performance metrics
- Optimization suggestions

### Quality Assurance
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format

# Preview production build
npm run preview
```

## Configuration

### Vite Configuration
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
});
```

### TypeScript Configuration
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

## Performance Metrics

### Bundle Analysis
- **Vendor Bundle**: ~140KB (React, React-DOM, utilities)
- **Application Bundle**: ~460KB (application code and components)
- **CSS Bundle**: ~59KB (styles and component CSS)
- **Gzipped Total**: ~135KB (optimized for delivery)

### Runtime Performance
- **First Contentful Paint**: <1.5s
- **Largest Contentful Paint**: <2.5s
- **Cumulative Layout Shift**: <0.1
- **First Input Delay**: <100ms

## Browser Support

### Supported Browsers
- **Chrome**: 90+ (recommended)
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Progressive Enhancement
- **Core Functionality**: Works in all supported browsers
- **Enhanced Features**: Modern browser capabilities when available
- **Graceful Degradation**: Fallbacks for older browsers

## Troubleshooting

### Common Issues

**Development Server Won't Start:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Build Failures:**
```bash
# Check TypeScript errors
npm run type-check

# Clear Vite cache
rm -rf node_modules/.vite
```

**API Connection Issues:**
```bash
# Verify backend is running on port 8000
curl http://localhost:8000/api/health

# Check proxy configuration in vite.config.ts
```

**Styling Issues:**
```bash
# Rebuild CSS
npm run build:css

# Check for CSS module conflicts
```

## Contributing

### Development Workflow
1. Create feature branch from main
2. Implement changes with tests
3. Run quality checks: `npm run lint && npm run type-check`
4. Build and test: `npm run build && npm run preview`
5. Submit pull request with description

### Code Review Checklist
- [ ] TypeScript types properly defined
- [ ] Components properly tested
- [ ] Accessibility standards met
- [ ] Performance impact assessed
- [ ] Documentation updated

---

**Frontend Version**: 2.0.0  
**Last Updated**: July 2025  
**React Version**: 18.2.0  
**Production Status**: Deployed with Vercel
