# OpenAI Chat Application - Deployment Guide

Professional deployment documentation for the OpenAI Chat Application with RAG capabilities.

## Overview

This guide provides comprehensive deployment instructions for a production-ready OpenAI chat application featuring FastAPI backend, React frontend, and advanced document processing capabilities with multi-format support.

## Prerequisites

### System Requirements
- **Python**: 3.9 or higher
- **Node.js**: 16 or higher  
- **npm**: 7 or higher
- **Git**: Latest version
- **OpenAI API Key**: Valid API key with sufficient credits

### Required Accounts
- **Vercel Account**: For production deployment
- **GitHub Account**: For version control and CI/CD

## Local Development Setup

### Environment Preparation

1. **Repository Setup**
   ```bash
   git clone https://github.com/[your-username]/openai-chat-app.git
   cd openai-chat-app
   ```

2. **Python Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Backend Dependencies**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

4. **Frontend Dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

### Environment Configuration

Create `.env` file in the `api` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
PYTHONPATH=.
```

### Development Servers

**Terminal 1 - Backend (Port 8000):**
```bash
cd api
python app.py
```

**Terminal 2 - Frontend (Port 3000):**
```bash
cd frontend
npm run dev
```

**Access Points:**
- Frontend Application: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Pre-Deployment Validation

### Backend Verification

1. **Dependency Check**
   ```bash
   cd api
   python -c "
   import fastapi, openai, pydantic, uvicorn, pandas, tabulate
   print('✅ All backend dependencies available')
   "
   ```

2. **API Endpoints Test**
   ```bash
   # Health check
   curl http://localhost:8000/api/health
   
   # Expected response:
   # {"status": "healthy", "features": ["chat", "document_upload", "rag", "session_management"]}
   ```

3. **Document Processing Test**
   ```bash
   # Test file upload (replace with actual file)
   curl -X POST "http://localhost:8000/api/documents" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -F "file=@sample.pdf"
   ```

### Frontend Verification

1. **Production Build**
   ```bash
   cd frontend
   npm run build
   ```

   **Expected Output:**
   - Build completes without errors
   - CSS bundle ~59KB (gzipped ~13KB)
   - JS bundle ~460KB (gzipped ~135KB)
   - All assets properly generated

2. **Build Artifacts Check**
   ```bash
   ls -la frontend/dist/
   # Verify presence of:
   # - index.html
   # - assets/index-[hash].css
   # - assets/index-[hash].js
   # - assets/vendor-[hash].js
   ```

3. **TypeScript Compilation**
   ```bash
   cd frontend
   npx tsc --noEmit
   # Should complete without errors
   ```

## Production Deployment (Vercel)

### Vercel Configuration

The application includes production-optimized `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/app.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/package.json", 
      "use": "@vercel/static-build",
      "config": { "distDir": "dist" }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/app.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/dist/$1"
    }
  ],
  "functions": {
    "api/app.py": {
      "maxDuration": 60,
      "memory": 2048
    }
  }
}
```

### Deployment Process

1. **Vercel CLI Installation**
   ```bash
   npm install -g vercel
   ```

2. **Authentication**
   ```bash
   vercel login
   ```

3. **Environment Variables Setup**
   
   Configure in Vercel Dashboard → Project → Settings → Environment Variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PYTHONPATH`: Set to `.`

4. **Production Deployment**
   ```bash
   vercel --prod
   ```

   **Expected Process:**
   - Build phase: ~90-120 seconds
   - Function optimization: Enabled
   - Static assets: Optimized and served via CDN
   - Deployment URL: Generated automatically

### Production Configuration

**Performance Optimizations:**
- **Function Timeout**: 60 seconds (for large document processing)
- **Memory Allocation**: 2GB (optimal for document operations)
- **Concurrent Processing**: Max 3 batches for document chunks
- **File Size Limit**: 15MB maximum upload size

**Supported Document Formats:**
- PDF documents (.pdf)
- Microsoft Office (.docx, .xlsx, .xls, .pptx)
- Text formats (.txt, .md, .markdown)
- Data files (.csv)
- Web documents (.html, .htm)

## Post-Deployment Verification

### Functional Testing Checklist

1. **Application Access**
   - [ ] Production URL loads successfully
   - [ ] UI renders correctly across devices
   - [ ] No console errors in browser dev tools

2. **Core Functionality**
   - [ ] Document upload works for all supported formats
   - [ ] RAG mode toggle functions properly
   - [ ] Chat responses generate successfully
   - [ ] Session management persists conversations

3. **Document Processing**
   - [ ] PDF files process without errors
   - [ ] Excel files with multiple sheets handled correctly
   - [ ] Large files (up to 15MB) upload successfully
   - [ ] Processing progress indicators display properly

4. **Performance Validation**
   - [ ] Average response time < 3 seconds
   - [ ] Document upload completes within timeout
   - [ ] UI remains responsive during processing
   - [ ] Memory usage within allocated limits

### Production Monitoring

**Key Metrics to Monitor:**
- Function execution time
- Memory usage patterns
- Error rates and types
- Document processing success rate
- User session duration
- API response times

**Vercel Analytics:**
- Performance insights enabled
- Real User Monitoring active
- Error tracking configured
- Usage analytics available

## Troubleshooting

### Common Deployment Issues

**Build Failures:**
```bash
# Solution: Check dependency versions
npm list --depth=0
pip freeze | grep -E "(fastapi|openai|pandas|tabulate)"
```

**Environment Variable Issues:**
```bash
# Verify in Vercel dashboard:
# Settings → Environment Variables
# Ensure OPENAI_API_KEY is set
```

**Function Timeout Errors:**
```json
// Verify vercel.json configuration:
"functions": {
  "api/app.py": {
    "maxDuration": 60,
    "memory": 2048
  }
}
```

**Document Upload Failures:**
- Check file size (max 15MB)
- Verify supported format
- Confirm API key permissions
- Review function logs in Vercel dashboard

### Performance Optimization

**Frontend Optimizations:**
- Code splitting enabled via Vite
- Asset compression active
- Cache headers configured
- Bundle size monitoring

**Backend Optimizations:**
- Batch processing for document chunks
- Concurrent request handling
- Memory-efficient text processing
- Error handling and recovery

## Security Considerations

**API Security:**
- Environment variables encrypted
- No API keys in source code
- Request validation implemented
- CORS configuration secure

**File Upload Security:**
- File type validation active
- Size limits enforced
- Content scanning for malicious files
- Temporary file cleanup

## Maintenance

**Regular Tasks:**
- Monitor Vercel function usage
- Review error logs weekly
- Update dependencies monthly
- Performance optimization quarterly

**Backup Strategy:**
- Source code: GitHub repository
- Configuration: Vercel dashboard
- User sessions: Temporary (cleared periodically)

---

**Production URL**: https://openai-chat-q21hnuxii-ovo-okpubulukus-projects.vercel.app  
**Last Updated**: July 2025  
**Version**: Multi-file support with performance optimization 