#!/bin/bash

# Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..

# Install Python dependencies
cd api
python -m pip install -r requirements.txt

# Copy wheel file to the correct location
mkdir -p .vercel/wheels
cp wheels/aimakerspace-0.1.0-py3-none-any.whl .vercel/wheels/ 