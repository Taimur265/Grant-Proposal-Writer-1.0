#!/bin/bash

# Grant Proposal Writer - Setup Script
# This script helps set up the development environment

set -e

echo "========================================"
echo "Grant Proposal Writer - Setup Script"
echo "========================================"
echo ""

# Check for required tools
check_requirements() {
    echo "Checking requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "ERROR: Docker is not installed. Please install Docker first."
        exit 1
    fi
    echo "  ✓ Docker found"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "ERROR: Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    echo "  ✓ Docker Compose found"

    echo ""
}

# Setup environment files
setup_env() {
    echo "Setting up environment files..."

    # Backend .env
    if [ ! -f "backend/.env" ]; then
        cp backend/.env.example backend/.env
        echo "  ✓ Created backend/.env from template"
        echo ""
        echo "  IMPORTANT: Edit backend/.env and add your API keys:"
        echo "    - OPENAI_API_KEY=your-openai-key"
        echo "    - ANTHROPIC_API_KEY=your-anthropic-key"
        echo ""
    else
        echo "  ✓ backend/.env already exists"
    fi

    # Frontend .env.local
    if [ ! -f "frontend/.env.local" ]; then
        cp frontend/.env.local.example frontend/.env.local 2>/dev/null || echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > frontend/.env.local
        echo "  ✓ Created frontend/.env.local"
    else
        echo "  ✓ frontend/.env.local already exists"
    fi

    echo ""
}

# Create required directories
create_directories() {
    echo "Creating required directories..."
    mkdir -p backend/uploads
    mkdir -p backend/alembic/versions
    echo "  ✓ Created directories"
    echo ""
}

# Start services
start_services() {
    echo "Starting services with Docker Compose..."
    echo ""

    docker-compose up -d

    echo ""
    echo "Waiting for services to start..."
    sleep 10

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        echo ""
        echo "========================================"
        echo "Setup Complete!"
        echo "========================================"
        echo ""
        echo "Services are running:"
        echo "  - Frontend: http://localhost:3000"
        echo "  - Backend API: http://localhost:8000"
        echo "  - API Documentation: http://localhost:8000/api/docs"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
        echo ""
    else
        echo ""
        echo "WARNING: Some services may not have started correctly."
        echo "Check logs with: docker-compose logs"
    fi
}

# Development setup (without Docker)
dev_setup() {
    echo "Setting up for local development..."
    echo ""

    # Backend
    echo "Setting up backend..."
    cd backend

    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "  ✓ Created Python virtual environment"
    fi

    source venv/bin/activate
    pip install -r requirements.txt
    echo "  ✓ Installed Python dependencies"

    cd ..

    # Frontend
    echo ""
    echo "Setting up frontend..."
    cd frontend

    if [ ! -d "node_modules" ]; then
        npm install
        echo "  ✓ Installed Node.js dependencies"
    fi

    cd ..

    echo ""
    echo "========================================"
    echo "Local Development Setup Complete!"
    echo "========================================"
    echo ""
    echo "To start the backend:"
    echo "  cd backend && source venv/bin/activate"
    echo "  uvicorn app.main:app --reload"
    echo ""
    echo "To start the frontend (in another terminal):"
    echo "  cd frontend && npm run dev"
    echo ""
    echo "Make sure PostgreSQL is running on localhost:5432"
    echo ""
}

# Main menu
main() {
    check_requirements
    setup_env
    create_directories

    echo "How would you like to run the application?"
    echo ""
    echo "  1) Docker (recommended) - Start all services with Docker Compose"
    echo "  2) Local Development - Set up for local development without Docker"
    echo "  3) Exit"
    echo ""
    read -p "Enter choice [1-3]: " choice

    case $choice in
        1)
            start_services
            ;;
        2)
            dev_setup
            ;;
        3)
            echo "Setup cancelled."
            exit 0
            ;;
        *)
            echo "Invalid choice. Running Docker setup..."
            start_services
            ;;
    esac
}

# Run main function
main
