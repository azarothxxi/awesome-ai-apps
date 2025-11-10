#!/bin/bash

# Quick start script for CX Monitoring Platform - Engine 1

echo "========================================"
echo "CX Monitoring Platform - Engine 1"
echo "SLA Library and Rules Platform"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -e . --quiet

# Start the API server in background
echo ""
echo "Starting API server..."
uvicorn main:app --reload &
SERVER_PID=$!

echo "API server starting (PID: $SERVER_PID)..."
echo "Waiting for server to be ready..."
sleep 5

# Load example data
echo ""
echo "Loading example SLAs and actions..."
python examples/load_examples.py

echo ""
echo "========================================"
echo "Platform is ready!"
echo "========================================"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "API Base URL: http://localhost:8000/api/v1"
echo ""
echo "To stop the server: kill $SERVER_PID"
echo ""
