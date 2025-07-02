# 🚀 Vercel Deployment Troubleshooting Guide

## 🔧 **Common Issues & Solutions**

### 1. **Python Runtime Issues**
**Problem**: Vercel uses old Python version by default
**Solution**: 
- Created `runtime.txt` with `python-3.11.12`
- Added runtime config in `vercel.json`
- Created `api/vercel.json` for API-specific settings

### 2. **Frontend Build Configuration**
**Problem**: Static build not properly configured
**Solution**:
- Updated `vercel.json` to use `@vercel/static-build`
- Optimized Vite config for production builds
- Disabled sourcemaps to reduce bundle size

### 3. **Serverless Function Limits**
**Problem**: Lambda function too large
**Solution**:
- Increased `maxLambdaSize` to 50mb
- Set `maxDuration` to 30 seconds
- Optimized font chunking strategy

### 4. **Environment Variables Required**
**Problem**: Missing OpenAI API key
**Solution**: Configure in Vercel dashboard:
```bash
OPENAI_API_KEY=your_api_key_here
```

### 5. **Import Path Issues**
**Problem**: Relative imports fail in serverless
**Solution**: Python path configuration in vercel.json

## 🔍 **Debugging Steps**

1. **Check Build Logs**: Look for Python version and dependency issues
2. **Function Logs**: Check serverless function execution logs  
3. **Network Tab**: Verify API endpoints are reachable
4. **Environment**: Ensure all required env vars are set

## 📋 **Pre-deployment Checklist**

- [ ] Frontend builds successfully (`npm run build`)
- [ ] All environment variables configured
- [ ] Python dependencies in requirements.txt
- [ ] Runtime version specified
- [ ] API endpoints returning 200 status
- [ ] CORS configured for Vercel domain

## 🚨 **Emergency Rollback**

If deployment fails completely:
```bash
# Revert to previous working vercel.json
git checkout HEAD~1 vercel.json
git commit -m "Revert vercel config"
git push
``` 