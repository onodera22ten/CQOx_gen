#!/bin/bash

# CQOx Setup Script

set -e

echo "======================================"
echo "CQOx Setup"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.11+ required (found: $python_version)"
    exit 1
fi

echo "✓ Python $python_version"

# Check Node version
echo "Checking Node.js version..."
node_version=$(node --version 2>&1 | sed 's/v//')
required_node="18.0.0"

if [ "$(printf '%s\n' "$required_node" "$node_version" | sort -V | head -n1)" != "$required_node" ]; then
    echo "Error: Node.js 18+ required (found: $node_version)"
    exit 1
fi

echo "✓ Node.js $node_version"

# Backend setup
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Backend setup complete"

# Frontend setup
echo ""
echo "Setting up frontend..."
cd ../frontend

echo "Installing Node dependencies..."
npm install

echo "✓ Frontend setup complete"

# Create necessary directories
echo ""
echo "Creating necessary directories..."
cd ..
mkdir -p data/{sample,exports}
mkdir -p models
mkdir -p artifacts
mkdir -p config/column_mappings
mkdir -p wolfram/outputs
mkdir -p policies/examples

echo "✓ Directories created"

# Set permissions for Wolfram scripts
echo ""
echo "Setting permissions for Wolfram scripts..."
chmod +x wolfram/visualizations/*.wl

echo "✓ Permissions set"

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m cqox.api.main"
echo ""
echo "To start the frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "API will be at: http://localhost:8000"
echo "UI will be at: http://localhost:3000"
echo ""
