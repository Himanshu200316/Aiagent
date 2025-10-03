# AI-Powered Social Media Advertising Agent

An intelligent agent that automatically generates and posts advertisements on Instagram, X (Twitter), and LinkedIn using MCP Dockerbase.

## Features

- 🤖 AI-generated ad content (images + captions)
- 📸 Support for custom image uploads
- 🔄 Automated daily posting at 12 AM
- 📱 Multi-platform support (Instagram, X, LinkedIn)
- 📝 Conversational interface via Cerebrus API
- 🗄️ File-based storage with duplicate prevention
- 🐳 Docker deployment ready

## Architecture

- **MCP Modules**: Instagram, X, LinkedIn posting capabilities
- **Cerebrus API**: User interaction and conversation management
- **AI Generation**: Stable Diffusion/DALL·E for image generation
- **Storage**: File-based system for prompts and history
- **Scheduler**: Automated posting system

## Quick Start

1. Clone the repository
2. Set up environment variables
3. Run with Docker: `docker-compose up`
4. Access the Cerebrus API interface
5. Configure your social media credentials
6. Start generating and posting ads!

## Project Structure

```
├── src/
│   ├── mcp/           # MCP modules for social platforms
│   ├── api/           # Cerebrus API integration
│   ├── ai/            # AI content generation
│   ├── storage/       # File-based storage system
│   └── scheduler/     # Automated posting scheduler
├── docker/            # Docker configuration
├── config/            # Configuration files
└── tests/             # Test suites
```