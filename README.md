# AI-Powered Social Media Ad Agent

An intelligent, automated social media advertising system that generates and posts engaging content across Instagram, X (Twitter), and LinkedIn using AI-powered image and caption generation.

## 🚀 Features

### Core Functionality
- **AI Content Generation**: Automated image and caption creation using DALL-E, Stable Diffusion, and GPT/Claude
- **Multi-Platform Posting**: Supports Instagram (feed + stories), X (Twitter), and LinkedIn
- **Conversational Setup**: User-friendly chat interface powered by Cerebrus API
- **Automated Scheduling**: Daily posting at customizable times (default: 12 AM)
- **Content Deduplication**: Ensures unique content with prompt hash tracking
- **Secure Credential Management**: Encrypted storage of social media credentials

### Advanced Features
- **MCP Integration**: Modular Content Protocol for extensible platform support
- **Docker Deployment**: Containerized for easy scaling and deployment
- **Real-time Analytics**: Track posting success rates and engagement
- **Campaign Management**: Organize content by campaigns with different settings
- **Image Upload Support**: Use your own images or AI-generated content
- **Platform Optimization**: Automatic resizing and formatting for each platform

## 🏗️ Architecture

```
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # REST API routes
│   │   ├── chat_routes.py      # Conversational interface
│   │   ├── auth_routes.py      # Authentication & credentials
│   │   ├── content_routes.py   # Content generation
│   │   └── posting_routes.py   # Campaign & posting management
│   ├── ai_generation/          # AI content generation
│   │   ├── content_generator.py
│   │   ├── image_generator.py
│   │   └── caption_generator.py
│   ├── mcp_modules/           # Platform-specific posting modules
│   │   ├── instagram_module.py
│   │   ├── twitter_module.py
│   │   └── linkedin_module.py
│   ├── scheduler/             # Automated posting scheduler
│   ├── storage/               # Data management & persistence
│   └── auth/                  # Security & authentication
├── config/                    # Configuration files
├── data/                      # Data storage (images, prompts, history)
└── docker/                    # Docker configuration
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- API keys for:
  - OpenAI (for DALL-E and GPT)
  - Anthropic (for Claude, optional)
  - Cerebrus API (for conversational interface)
  - Social media platform credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd social-media-ad-agent
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

### Manual Setup (Development)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**
   ```bash
   export PYTHONPATH=$PWD/src
   ```

3. **Run the application**
   ```bash
   python src/main.py
   ```

## 🔧 Configuration

### Environment Variables

```bash
# Core Application
ENVIRONMENT=production
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/social_media_agent

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Cerebrus API
CEREBRUS_API_KEY=your_cerebrus_key
CEREBRUS_BASE_URL=https://api.cerebrus.ai/v1

# Social Media Credentials
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
# ... (see .env.example for complete list)
```

### Platform Setup

#### Instagram
- Username and password (or App Password for 2FA accounts)
- Consider using a business account for better API access

#### X (Twitter)
- Create a Twitter Developer account
- Generate API keys and access tokens
- Ensure your app has read/write permissions

#### LinkedIn
- Create a LinkedIn Developer application
- Generate access tokens with appropriate scopes
- Requires company page admin access for posting

## 💬 Usage

### 1. Start a Conversation
```bash
curl -X POST "http://localhost:8000/api/chat/start" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "conversation_type": "ad_setup"}'
```

### 2. Interactive Setup
The system will guide you through:
- Social media credential setup
- Product/service description
- Target audience definition
- Tone and style preferences
- Platform selection
- Image preferences
- Posting schedule

### 3. Automated Operation
Once configured, the system will:
- Generate unique content daily
- Post to selected platforms automatically
- Track posting success and errors
- Maintain content history

### 4. API Management
Use the REST API for:
- Campaign management
- Content generation
- Posting history
- Analytics and reporting

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/credentials` - Store social media credentials

### Chat Interface
- `POST /api/chat/start` - Start conversation
- `POST /api/chat/message` - Send message
- `POST /api/chat/upload` - Upload images

### Content Generation
- `POST /api/content/generate` - Generate content
- `POST /api/content/generate-with-image` - Generate with uploaded image
- `GET /api/content/templates` - Get content templates

### Campaign Management
- `POST /api/posting/campaigns` - Create campaign
- `GET /api/posting/campaigns` - List campaigns
- `PUT /api/posting/campaigns/{id}/schedule` - Update schedule
- `POST /api/posting/campaigns/{id}/post-now` - Trigger immediate post

## 🔒 Security

- **Credential Encryption**: All social media credentials are encrypted using Fernet
- **JWT Authentication**: Secure API access with JSON Web Tokens
- **Input Validation**: Comprehensive validation of all user inputs
- **Rate Limiting**: Built-in rate limiting for social media APIs
- **Secure Storage**: Encrypted database storage for sensitive data

## 📊 Monitoring & Analytics

### Health Checks
- Application health: `GET /health`
- Component health: Individual module health checks
- Database connectivity monitoring

### Analytics
- Posting success rates
- Content generation metrics
- Platform-specific performance
- Campaign effectiveness tracking

## 🔧 Development

### Adding New Platforms
1. Create new module in `src/mcp_modules/`
2. Extend `BaseSocialMediaModule`
3. Implement platform-specific posting logic
4. Update MCP configuration
5. Add credential validation

### Extending AI Generation
1. Add new models to `ImageGenerator` or `CaptionGenerator`
2. Update prompt templates
3. Add platform-specific optimizations
4. Test with various content types

### Custom Scheduling
1. Extend `PostScheduler` with new triggers
2. Add custom scheduling logic
3. Update API endpoints
4. Test scheduling accuracy

## 🐛 Troubleshooting

### Common Issues

**Authentication Failures**
- Verify API keys are correct
- Check social media account permissions
- Ensure 2FA is properly configured

**Posting Failures**
- Check platform rate limits
- Verify content meets platform requirements
- Review error logs for specific issues

**Content Generation Issues**
- Verify AI service API keys
- Check content length limits
- Review prompt formatting

### Logs
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Posting logs: `logs/posting.log`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API documentation at `/docs`

## 🚀 Roadmap

- [ ] Video content generation
- [ ] TikTok integration
- [ ] Advanced analytics dashboard
- [ ] A/B testing capabilities
- [ ] Multi-language support
- [ ] Advanced scheduling options
- [ ] Integration with more AI models
- [ ] Mobile app interface