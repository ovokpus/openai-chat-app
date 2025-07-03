#!/bin/bash

# Empty knowledge base directory as per workspace rules
rm -rf api/services/knowledge_base/regulatory_docs
rm -rf api/services/knowledge_base/uploaded_docs

# Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..

# Install Python dependencies from root requirements.txt
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --no-cache-dir 