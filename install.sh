#!/bin/bash

# Autoscience Installation Script
# This script sets up the development environment

set -e

echo "=================================="
echo "  Autoscience Installation"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Node.js $NODE_VERSION"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is required for sandbox execution"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Warning: Docker Compose is required for deployment"
fi

echo ""
echo "Setting up backend..."

# Backend setup
cd backend

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev,sandbox]"

# Create .env from template
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from template"
fi

cd ..

echo ""
echo "Setting up frontend..."

# Frontend setup
cd frontend

# Install dependencies
npm install

cd ..

echo ""
echo "=================================="
echo "  Installation Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure API keys in backend/.env:"
echo "   - OPENAI_API_KEY (for GPT-4o)"
echo "   - ANTHROPIC_API_KEY (for Claude)"
echo ""
echo "2. Start the development servers:"
echo "   - Backend: cd backend && uvicorn app.main:app --reload"
echo "   - Frontend: cd frontend && npm run dev"
echo ""
echo "3. Or use Docker Compose:"
echo "   - docker-compose -f docker/docker-compose.yml up"
echo ""
echo "4. Open http://localhost:3000"
echo ""
