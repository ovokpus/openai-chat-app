#!/bin/bash

# Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..

# Install Python dependencies
cd api
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --no-cache-dir 