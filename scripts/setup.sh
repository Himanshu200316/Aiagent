#!/bin/bash

# Setup script for AI Social Media Ad Agent

set -e

echo "🚀 Setting up AI Social Media Ad Agent..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{prompts,images,history,uploads,credentials}
mkdir -p logs
mkdir -p config

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and credentials"
else
    echo "✅ .env file already exists"
fi

# Set permissions
echo "🔒 Setting permissions..."
chmod -R 755 data/
chmod -R 755 logs/
chmod +x scripts/*.sh

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "📍 Access points:"
    echo "   • API: http://localhost:8000"
    echo "   • Health check: http://localhost:8000/health"
    echo "   • API docs: http://localhost:8000/docs"
    echo "   • PostgreSQL: localhost:5432"
    echo "   • Redis: localhost:6379"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Edit .env file with your API keys"
    echo "   2. Restart services: docker-compose restart"
    echo "   3. Test the API: curl http://localhost:8000/health"
    echo "   4. Start a conversation: POST /api/chat/start"
else
    echo "❌ Some services failed to start. Check logs:"
    echo "   docker-compose logs"
fi