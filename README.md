# Social Media Advertising Agent

An AI-powered agent that automatically generates and posts advertisements on Instagram, X (Twitter), and LinkedIn using MCP Dockerbase.

## 🚀 Features

### Core Functionality
- **AI Content Generation**: Generate both images and captions using AI models
- **Multi-Platform Posting**: Support for Instagram, X (Twitter), and LinkedIn
- **Automated Scheduling**: Daily posting at 12 AM (customizable)
- **Content Types**: Both feed posts and Instagram stories
- **Duplicate Prevention**: Smart prompt storage to avoid repeated content

### AI Capabilities
- **Image Generation**: Using Stable Diffusion models
- **Caption Generation**: Platform-specific, tone-aware captions
- **Image Analysis**: Analyze uploaded images for caption suggestions
- **Content Optimization**: Tailored for target audience and platform

### User Interface
- **Cerebrus API Integration**: Conversational interface for easy interaction
- **Secure Credential Management**: Encrypted storage of social media credentials
- **File-based Storage**: Reliable prompt and history tracking
- **RESTful API**: Complete API for all functionality

## 🏗️ Architecture

### MCP Modules
- **MCPInstagram**: Instagram Basic Display API integration
- **MCPTwitter**: Twitter API v2 integration  
- **MCPLinkedIn**: LinkedIn API integration

### Services
- **AIContentGenerator**: OpenAI GPT-4 and Stable Diffusion integration
- **CerebrusIntegration**: Conversational AI interface
- **PostingScheduler**: Automated daily posting system
- **CredentialManager**: Secure credential encryption and storage
- **StorageManager**: File-based data persistence

### Security
- **JWT Authentication**: Secure user authentication
- **Credential Encryption**: Fernet encryption for sensitive data
- **Input Validation**: Comprehensive data validation
- **Error Handling**: Robust error management

## 🐳 Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key
- Social media API credentials (Instagram, Twitter, LinkedIn)
- Cerebrus API key (optional)

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd social-media-agent
   cp .env.example .env
   ```

2. **Configure Environment**
   Edit `.env` file with your API keys:
   ```bash
   # OpenAI API Key
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Social Media API Keys
   INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
   INSTAGRAM_APP_ID=your_instagram_app_id
   INSTAGRAM_APP_SECRET=your_instagram_app_secret
   
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
   
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
   LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
   
   # Cerebrus API (optional)
   CEREBRUS_API_KEY=your_cerebrus_api_key
   CEREBRUS_API_URL=https://api.cerebrus.com
   
   # Security
   SECRET_KEY=your_secret_key_for_jwt_tokens
   ```

3. **Build and Run**
   ```bash
   docker-compose up --build
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📚 API Usage

### Authentication
```bash
# Register user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "user@example.com", "password": "password"}'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### Social Media Setup
```bash
# Set Instagram credentials
curl -X POST "http://localhost:8000/api/social-media/credentials" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "credentials": {
      "access_token": "your_token",
      "app_id": "your_app_id", 
      "app_secret": "your_secret"
    }
  }'
```

### Content Generation
```bash
# Generate complete content
curl -X POST "http://localhost:8000/api/content/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Amazing new product",
    "tone": "professional",
    "target_audience": "business professionals",
    "platforms": ["instagram", "twitter"],
    "generate_image": true
  }'
```

### Scheduling
```bash
# Setup daily posting
curl -X POST "http://localhost:8000/api/scheduling/setup" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "post_time": "12:00",
    "frequency": "daily",
    "platforms": ["instagram", "twitter"],
    "enabled": true
  }'
```

## 🤖 Cerebrus Integration

The agent includes a conversational interface via Cerebrus API:

### Example Conversations
```
User: "Set up Instagram credentials"
Agent: "I'll help you set up Instagram credentials. Please provide: 1. Instagram Access Token 2. App ID 3. App Secret..."

User: "Create ad for my new coffee shop"
Agent: "Perfect! I'll create ad content for 'my new coffee shop' with a professional tone. Should I also generate an AI image?"

User: "Upload an image"
Agent: "I can help you upload an image! Please provide the image file. I'll analyze it and suggest captions..."
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for content generation
- `INSTAGRAM_*`: Instagram Basic Display API credentials
- `TWITTER_*`: Twitter API v2 credentials
- `LINKEDIN_*`: LinkedIn API credentials
- `CEREBRUS_API_KEY`: Cerebrus API key for conversational interface
- `SECRET_KEY`: JWT secret key for authentication
- `DEFAULT_POST_TIME`: Default posting time (format: HH:MM)
- `STABLE_DIFFUSION_MODEL`: Stable Diffusion model to use

### File Structure
```
/workspace/
├── app/
│   ├── api/routes/          # API endpoints
│   ├── core/                # Core configuration
│   ├── services/            # Business logic services
│   ├── models/              # Data models
│   └── schemas/             # Pydantic schemas
├── data/                    # Database files
├── images/                  # Generated/uploaded images
├── logs/                    # Application logs
├── prompts/                 # Stored prompts and history
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
└── docker-compose.yml      # Docker Compose setup
```

## 🔒 Security Features

- **Credential Encryption**: All social media credentials are encrypted using Fernet
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive validation of all inputs
- **Error Handling**: Secure error messages without sensitive data exposure
- **File Permissions**: Restricted file permissions for sensitive data

## 📊 Monitoring and Logging

- **Structured Logging**: Comprehensive logging with different levels
- **Activity Tracking**: All posting activities are logged
- **Error Monitoring**: Detailed error logging for debugging
- **Performance Metrics**: API response times and success rates

## 🚀 Production Deployment

### Scaling Considerations
- Use Redis for session management in production
- Implement database connection pooling
- Use external storage for images (AWS S3, etc.)
- Set up proper monitoring and alerting

### Security Best Practices
- Use environment-specific configuration
- Implement rate limiting
- Set up proper CORS policies
- Use HTTPS in production
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the logs in the `logs/` directory

## 🔄 Updates and Maintenance

- Regular dependency updates
- Security patches
- Feature enhancements
- Performance optimizations

---

**Built with ❤️ using FastAPI, Docker, and AI technologies**