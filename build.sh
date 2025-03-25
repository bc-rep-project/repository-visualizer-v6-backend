#!/bin/bash

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Explicitly install requests to ensure it's available
pip install requests

echo "Building application..."
mkdir -p repos

echo "Build completed successfully!"


