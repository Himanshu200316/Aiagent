#!/bin/bash

# AI Social Media Advertising Agent Setup Script

echo "🚀 Setting up AI Social Media Advertising Agent..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{prompts,images,logs,credentials}
mkdir -p config
mkdir -p tests

# Set up environment file
echo "⚙️ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env file from template. Please update with your API keys."
else
    echo "✅ .env file already exists"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set up database
echo "🗄️ Setting up database..."
python -c "from src.storage.database import init_database; import asyncio; asyncio.run(init_database())"

# Create initial configuration
echo "🔧 Creating initial configuration..."
if [ ! -f config/posting_config.json ]; then
    cp config/posting_config.json config/posting_config.json
fi

# Set permissions
echo "🔐 Setting file permissions..."
chmod +x scripts/*.sh
chmod 600 data/credentials/* 2>/dev/null || true

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Configure social media credentials"
echo "3. Run: docker-compose up"
echo "4. Access the API at http://localhost:8000"
echo ""
echo "For more information, see README.md"