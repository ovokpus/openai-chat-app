# 🚀 Vercel Deployment Troubleshooting Guide

## 🔧 **Why It Works Locally But Not on Vercel**

### 🏠 **Local Development vs 🌐 Vercel Production**

**Locally:**
- Vite dev server serves files directly from `frontend/src/`
- API runs on `localhost:8000`, frontend on `localhost:3000`
- Hot reloading and direct file access

**On Vercel:**
- Frontend must be pre-built into static files
- Static files served from serverless CDN
- API runs as serverless functions
- Different routing and file serving mechanisms

## 🎯 **Specific Issues Found & Fixed**

### 1. **Static File Serving Problem**
**Issue**: Generated HTML references `/assets/index-xyz.js` but Vercel couldn't find the files

**Root Cause**: 
```html
<!-- Generated HTML references: -->
<script src="/assets/index-Dk7ti2jC.js"></script>
<link href="/assets/index-DAvVUihP.css" rel="stylesheet">
```

But Vercel was looking in wrong directory structure.

**Solution**: Updated `vercel.json` routing:
```json
{
  "src": "/assets/(.*)",
  "dest": "/frontend/dist/assets/$1"
},
{
  "src": "/fonts/(.*)", 
  "dest": "/frontend/dist/fonts/$1"
}
```

### 2. **Build Directory Configuration**
**Issue**: `distDir: "frontend/dist"` was incorrect for `@vercel/static-build`

**Solution**: Changed to `distDir: "dist"` - Vercel expects relative path from package.json location

### 3. **SPA Routing Problem**
**Issue**: All routes were trying to serve files instead of serving `index.html` for SPA

**Solution**: Catch-all route now serves `index.html`:
```json
{
  "src": "/(.*)",
  "dest": "/frontend/dist/index.html"
}
```

## 🔍 **How Files Flow in Deployment**

1. **Build Phase**: 
   - `npm run vercel-build` runs in `frontend/` directory
   - Generates `frontend/dist/` with all static assets
   - Creates `index.html`, `/assets/`, `/fonts/` folders

2. **Deploy Phase**:
   - Vercel uploads built files to CDN
   - Routes requests based on `vercel.json` rules
   - API requests → Python serverless functions
   - Static files → CDN with proper paths

3. **Runtime**:
   - Browser requests `/assets/index-xyz.js`
   - Vercel routes to `/frontend/dist/assets/index-xyz.js`
   - Files served with proper MIME types and caching

## 🏗️ **Build Verification Commands**

```bash
# Test frontend build locally
cd frontend && npm run build

# Check generated files
ls -la frontend/dist/
ls -la frontend/dist/assets/
ls -la frontend/dist/fonts/

# Verify HTML references correct paths
cat frontend/dist/index.html
```

## 🚨 **Debug Vercel Issues**

### Check Build Logs:
1. Go to Vercel Dashboard → Your Project → Deployments
2. Click on failed deployment → View Build Logs
3. Look for:
   - `npm run vercel-build` success/failure
   - File size warnings
   - Missing dependency errors

### Check Function Logs:
1. Go to Functions tab in Vercel Dashboard
2. Check `/api/app.py` function logs
3. Look for Python import errors or timeouts

### Test Locally:
```bash
# Build and serve locally to mimic Vercel
cd frontend && npm run build
npx serve dist -s
```

## 📋 **Pre-deployment Checklist**

- [x] Frontend builds without errors (`npm run build`)
- [x] All assets generated in correct directories
- [x] `vercel.json` routes configured for static files
- [x] API routes separate from static routes
- [x] Environment variables set in Vercel dashboard
- [x] Python runtime specified correctly

## 🎉 **What Should Work Now**

- ✅ Frontend assets served from correct paths
- ✅ KaTeX fonts load properly (math rendering)
- ✅ API calls routed to Python backend
- ✅ SPA routing works (React Router)
- ✅ Hot reloading in development unchanged 