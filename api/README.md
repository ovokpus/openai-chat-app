# OpenAI Chat API Backend

FastAPI-based backend service providing intelligent chat capabilities with advanced document processing and RAG (Retrieval-Augmented Generation) integration.

## Overview

This backend service delivers a comprehensive AI-powered chat experience featuring:
- OpenAI integration with streaming responses
- Multi-format document processing and analysis
- Vector database storage for document retrieval
- Session management for conversation continuity
- RESTful API design with automatic documentation

## Architecture

### Technology Stack
- **Framework**: FastAPI 0.115.12
- **AI Integration**: OpenAI Python SDK 1.77.0
- **Document Processing**: Multiple specialized libraries
- **Data Validation**: Pydantic 2.11.4
- **Server**: Uvicorn ASGI server
- **Vector Operations**: NumPy for embeddings

### Core Components
- **Chat Service**: OpenAI API integration with streaming
- **Document Processor**: Multi-format file handling
- **RAG Pipeline**: Vector search and context augmentation
- **Session Manager**: Conversation state persistence
- **Vector Database**: Embedding storage and retrieval

## Installation and Setup

### Prerequisites
- Python 3.9 or higher
- OpenAI API key with sufficient credits
- Virtual environment (recommended)

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Create `.env` file in the `api` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
PYTHONPATH=.
```

### Running the Server
```bash
# Development mode
python app.py

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Server Access Points:**
- API Base: http://localhost:8000
- Interactive Documentation: http://localhost:8000/docs
- Alternative Documentation: http://localhost:8000/redoc

## API Reference

### Authentication
All endpoints requiring OpenAI integration accept the API key via:
- Request body parameter: `api_key`
- Header: `Authorization: Bearer YOUR_API_KEY`

### Core Endpoints

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "features": [
    "chat",
    "document_upload", 
    "rag",
    "session_management"
  ],
  "version": "2.0.0"
}
```

#### Chat Interface
```http
POST /api/chat
```

**Request Body:**
```json
{
  "developer_message": "string",
  "user_message": "string", 
  "model": "gpt-4o-mini",
  "api_key": "string",
  "session_id": "string (optional)"
}
```

**Response:**
- **Type**: Server-Sent Events (SSE)
- **Content-Type**: `text/plain`
- **Format**: Streaming text chunks

**Example Usage:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "developer_message": "You are a helpful assistant.",
        "user_message": "Explain quantum computing",
        "api_key": "your-api-key-here"
    },
    stream=True
)

for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
    if chunk:
        print(chunk, end='')
```

### Document Management

#### Document Upload
```http
POST /api/documents
```

**Request:**
- **Content-Type**: `multipart/form-data`
- **Body**: File upload with metadata

**Parameters:**
- `file`: Document file (required)
- `session_id`: Session identifier (optional)

**Supported Formats:**
- PDF Documents (`.pdf`)
- Microsoft Word (`.docx`)
- Excel Spreadsheets (`.xlsx`, `.xls`)
- PowerPoint Presentations (`.pptx`)
- Text Files (`.txt`)
- Markdown (`.md`, `.markdown`)
- CSV Data (`.csv`)
- HTML Documents (`.html`, `.htm`)

**File Constraints:**
- Maximum size: 15MB
- File type validation enforced
- Content sanitization applied

**Response:**
```json
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "size": 1024000,
  "status": "processed",
  "chunks_created": 25,
  "processing_time": 3.2,
  "metadata": {
    "pages": 10,
    "text_length": 15000,
    "format": "pdf"
  }
}
```

#### Document Listing
```http
GET /api/documents
```

**Query Parameters:**
- `session_id`: Filter by session (optional)
- `limit`: Maximum results (default: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "documents": [
    {
      "document_id": "uuid",
      "filename": "document.pdf",
      "upload_time": "2025-07-03T10:30:00Z",
      "size": 1024000,
      "status": "processed"
    }
  ],
  "total": 1,
  "has_more": false
}
```

#### Document Deletion
```http
DELETE /api/documents/{document_id}
```

**Response:**
```json
{
  "status": "deleted",
  "document_id": "uuid",
  "cleanup_completed": true
}
```

### RAG (Retrieval-Augmented Generation)

#### RAG Chat
```http
POST /api/rag
```

**Request Body:**
```json
{
  "query": "string",
  "api_key": "string",
  "session_id": "string (optional)",
  "document_ids": ["uuid1", "uuid2"],
  "max_context_length": 4000,
  "similarity_threshold": 0.7
}
```

**Response:**
- **Type**: Server-Sent Events (SSE)
- **Content-Type**: `text/plain`
- **Format**: Streaming response with context

**RAG Process:**
1. Query embedding generation
2. Vector similarity search across documents
3. Context chunk retrieval and ranking
4. Prompt augmentation with relevant context
5. OpenAI API request with enhanced context
6. Streaming response generation

### Session Management

#### Session Creation
```http
POST /api/sessions
```

**Request Body:**
```json
{
  "session_name": "string (optional)",
  "metadata": {
    "user_id": "string",
    "purpose": "string"
  }
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "created_at": "2025-07-03T10:30:00Z",
  "status": "active"
}
```

#### Session Information
```http
GET /api/sessions/{session_id}
```

**Response:**
```json
{
  "session_id": "uuid",
  "created_at": "2025-07-03T10:30:00Z",
  "last_activity": "2025-07-03T11:15:00Z",
  "document_count": 3,
  "message_count": 15,
  "status": "active",
  "documents": [
    {
      "document_id": "uuid",
      "filename": "report.pdf",
      "upload_time": "2025-07-03T10:45:00Z"
    }
  ]
}
```

#### Session Cleanup
```http
DELETE /api/sessions/{session_id}
```

**Response:**
```json
{
  "status": "deleted",
  "session_id": "uuid",
  "documents_removed": 3,
  "vectors_cleared": 150
}
```

## Advanced Features

### Batch Document Processing
The system supports optimized batch processing for multiple documents:
- Concurrent processing of document chunks
- Memory-efficient handling of large files
- Progress tracking for long-running operations
- Automatic retry for failed chunks

### Vector Database Operations
- **Storage**: Embeddings with metadata indexing
- **Search**: Cosine similarity with configurable thresholds
- **Optimization**: Automatic index management
- **Persistence**: Session-based vector storage

### Error Handling
Comprehensive error management includes:
- Input validation with detailed error messages
- OpenAI API error propagation
- File processing error recovery
- Resource cleanup on failures

## Performance Specifications

### Processing Capabilities
- **Document Size**: Up to 15MB per file
- **Concurrent Uploads**: 3 simultaneous files
- **Chunk Processing**: 20 chunks per batch
- **Response Time**: Average 2-3 seconds for standard queries

### Resource Usage
- **Memory**: Optimized for 2GB allocation
- **CPU**: Efficient multi-core utilization
- **Storage**: Temporary file management with auto-cleanup

## Security Features

### Input Validation
- File type verification
- Content sanitization
- Size limit enforcement
- Malicious content detection

### API Security
- Request validation via Pydantic models
- Error message sanitization
- Rate limiting consideration
- Secure environment variable handling

## Development and Testing

### Running Tests
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# API endpoint tests
python -m pytest tests/api/
```

### Development Mode
```bash
# With auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# With debug logging
python app.py --debug
```

### API Documentation
Access comprehensive interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deployment Configuration

### Production Environment
```python
# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_WORKERS=4
TIMEOUT=60
MEMORY_LIMIT=2048
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring and Observability

### Health Monitoring
- Endpoint availability checks
- Response time monitoring
- Error rate tracking
- Resource utilization metrics

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking with stack traces
- Performance metrics collection

---

**API Version**: 2.0.0  
**Last Updated**: July 2025  
**FastAPI Version**: 0.115.12  
**Production Status**: Deployed on Vercel 