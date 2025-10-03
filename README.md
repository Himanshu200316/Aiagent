# AI-Powered Social Media Advertising Agent

An intelligent automation system that generates and posts advertisements on Instagram, X (Twitter), and LinkedIn using AI-powered content creation and MCP (Model Context Protocol) for social media integration.

## 🚀 Features

### Core Capabilities
- **AI Content Generation**: Creates engaging ad content with both images and captions
- **Multi-Platform Support**: Posts to Instagram, X (Twitter), and LinkedIn
- **Smart Prompt Management**: Avoids content repetition with intelligent prompt storage
- **Automated Scheduling**: Daily posting at 12:00 AM (customizable)
- **Conversational Interface**: Cerebrus API for natural user interaction
- **Custom Image Support**: Upload your own images or use AI-generated ones

### AI Image Generation
- **Multiple Styles**: Realistic, artistic, cartoon, minimalist, vintage, modern
- **AI Models**: Stable Diffusion and DALL·E integration
- **Smart Processing**: Automatic image optimization for social media

### Advanced Features
- **Instagram Stories Support**: Post to both feed and stories
- **User Management**: Secure credential storage and user preferences
- **Docker Deployment**: Containerized for easy deployment and scaling
- **Comprehensive Logging**: Full activity tracking and error reporting

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cerebrus API  │    │   Core Engine   │    │  Social Media   │
│   (Chat Layer)  │───▶│   Components    │───▶│     APIs        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼───────┐ ┌─────▼──────┐ ┌─────▼──────┐
        │ Prompt Manager│ │Image Gen. │ │Caption Gen.│
        └───────────────┘ └───────────┘ └────────────┘
```

## 🛠️ Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for development)
- API keys for AI services (OpenAI, Stability AI)

### Quick Start

1. **Clone and configure**:
```bash
git clone <repository-url>
cd ai-social-media-agent
cp .env.template .env
# Edit .env with your API keys and credentials
```

2. **Start with Docker Compose**:
```bash
docker-compose up -d
```

3. **Access the API**:
- Main API: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Documentation: http://localhost:8000/docs

### Manual Installation (Development)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment**:
```bash
cp .env.template .env
# Configure your API keys in .env
```

3. **Run the application**:
```bash
python main.py
```

## 📖 Usage Guide

### Conversational Interface

The system uses Cerebrus API for natural conversation. Here are some example interactions:

#### Getting Started
```
User: "Hello, I want to set up automated posting"
Agent: "Hello! I'm your AI Social Media Advertising Agent... What would you like to do today?"
```

#### Setting Up Credentials
```
User: "I want to connect my Instagram account"
Agent: "Perfect! Let's set up your Instagram credentials..."
```

#### Creating an Advertisement
```
User: "Create an ad for my coffee shop, professional tone, for coffee lovers"
Agent: "Great! Let's create an advertisement for you..."
```

### API Endpoints

#### Chat Interface
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create an ad for my new product",
    "user_id": "user123",
    "platform": "instagram"
  }'
```

#### Ad Generation
```bash
curl -X POST "http://localhost:8000/api/v1/generate-ad" \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Premium organic coffee beans",
    "platforms": ["instagram", "twitter", "linkedin"],
    "tone": "professional",
    "target_audience": "coffee_lovers",
    "image_style": "realistic"
  }'
```

#### Upload Credentials
```bash
curl -X POST "http://localhost:8000/api/v1/upload-credentials" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "platform": "instagram",
    "credentials": {
      "username": "your_username",
      "password": "your_password"
    }
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for DALL·E and GPT | Yes |
| `STABILITY_API_KEY` | Stability AI API key for Stable Diffusion | Yes |
| `INSTAGRAM_USERNAME` | Instagram login username | Yes |
| `INSTAGRAM_PASSWORD` | Instagram login password | Yes |
| `TWITTER_API_KEY` | Twitter API key | Yes |
| `TWITTER_API_SECRET` | Twitter API secret | Yes |
| `TWITTER_ACCESS_TOKEN` | Twitter access token | Yes |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter access token secret | Yes |
| `LINKEDIN_EMAIL` | LinkedIn login email | Yes |
| `LINKEDIN_PASSWORD` | LinkedIn login password | Yes |

### Platform-Specific Setup

#### Instagram
- Uses `instagrapi` library for posting
- Supports both feed posts and stories
- Requires valid Instagram credentials

#### Twitter/X
- Uses `tweepy` library for API access
- Supports tweet posting with images
- Requires Twitter Developer API credentials

#### LinkedIn
- Uses `linkedin-api` library for posting
- Supports professional post creation
- Requires LinkedIn account credentials

## 📊 Monitoring & Management

### Health Checks
```bash
curl http://localhost:8000/health
```

### System Status
```bash
curl http://localhost:8000/api/v1/status
```

### Logs
- Application logs: `/app/logs/app.log`
- Access logs: Available via Docker logs
- Error tracking: Comprehensive error reporting

### Data Storage
- User data: `/app/data/users/`
- Prompts: `/app/data/prompts/`
- Images: `/app/data/images/`
- History: `/app/data/scheduler_history.json`

## 🔒 Security Considerations

### Credential Management
- Credentials are encrypted before storage
- API keys are loaded from environment variables
- No sensitive data is logged

### Best Practices
- Use strong, unique passwords for social media accounts
- Regularly rotate API keys
- Monitor account activity
- Use HTTPS in production

## 🚨 Troubleshooting

### Common Issues

**"Image generation failed"**
- Check API keys are correctly configured
- Verify internet connection for external APIs
- Check available disk space for image storage

**"Posting failed"**
- Verify social media credentials are correct
- Check if accounts are in good standing
- Ensure API rate limits aren't exceeded

**"Scheduler not running"**
- Check application logs for errors
- Verify system time is correct
- Restart the application if needed

### Debug Mode
Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for DALL·E and GPT models
- Stability AI for Stable Diffusion
- Instagram, Twitter, and LinkedIn APIs
- FastAPI for the web framework
- Docker for containerization

---

**Need Help?** Check the logs in `/app/logs/` or reach out to the development team for support.