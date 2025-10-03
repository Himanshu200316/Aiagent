# AI Social Media Advertising Agent - Usage Guide

## Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to the project
cd /workspace

# Run the setup script
./scripts/setup.sh

# Update environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure API Keys

Update the `.env` file with your API keys:

```bash
# OpenAI for content generation
OPENAI_API_KEY=your_openai_api_key_here

# Cerebrus API for conversation
CEREBRUS_API_KEY=your_cerebrus_api_key_here

# Social Media APIs
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token

TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

TWITTER_BEARER_TOKEN=your_twitter_bearer_token

LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
```

### 3. Start the Agent

```bash
# Using Docker (Recommended)
docker-compose up

# Or run directly
python src/main.py
```

### 4. Access the API

The agent will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Using the Agent

### Setting Up Credentials

```bash
curl -X POST "http://localhost:8000/api/v1/credentials" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "credentials": {
      "access_token": "your_access_token",
      "user_id": "your_user_id"
    }
  }'
```

### Generating Ad Content

```bash
curl -X POST "http://localhost:8000/api/v1/generate-ad" \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Amazing AI-powered smartphone",
    "tone": "professional",
    "target_audience": "tech enthusiasts",
    "call_to_action": "Pre-order now!",
    "hashtags": ["smartphone", "AI", "tech"],
    "platforms": ["instagram", "twitter", "linkedin"]
  }'
```

### Posting Content

```bash
curl -X POST "http://localhost:8000/api/v1/post-content" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "caption": "Check out our amazing product! #amazing #product",
      "image_url": "/path/to/image.png",
      "platforms": ["instagram", "twitter"]
    },
    "platforms": ["instagram", "twitter"]
  }'
```

### Uploading Custom Images

```bash
curl -X POST "http://localhost:8000/api/v1/upload-image" \
  -F "file=@/path/to/your/image.jpg"
```

## Cerebrus API Integration

The agent integrates with Cerebrus API for conversational interaction:

### Chat Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "I want to create an ad for my new product",
    "context": {}
  }'
```

### Example Conversation Flow

1. **User**: "I want to create an ad for my new product"
2. **Agent**: "Great! Let's create an ad. Please tell me about your product or service, and I'll help you generate content."
3. **User**: "It's a smartphone with AI features"
4. **Agent**: "Perfect! What tone would you like for the ad? (professional, casual, friendly, authoritative, playful)"
5. **User**: "Professional"
6. **Agent**: "Great! Who is your target audience?"
7. **User**: "Tech enthusiasts and professionals"
8. **Agent**: "Excellent! I'll generate professional content for tech enthusiasts. Would you like me to create an AI-generated image or upload your own?"

## Automated Posting

The agent automatically posts content daily at 12 AM (configurable):

### Configure Schedule

```bash
curl -X PUT "http://localhost:8000/api/v1/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "time": "09:00",
    "timezone": "UTC",
    "platforms": ["instagram", "twitter", "linkedin"]
  }'
```

### Check Schedule Status

```bash
curl -X GET "http://localhost:8000/api/v1/schedule"
```

## Monitoring and Analytics

### View Posting History

```bash
curl -X GET "http://localhost:8000/api/v1/posting-history?limit=50"
```

### Get Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/statistics"
```

## Testing

Run the test suite:

```bash
# Run all tests
python scripts/test_agent.py

# Run specific tests
pytest tests/test_content_generator.py
pytest tests/test_social_media_manager.py
pytest tests/test_prompt_manager.py
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all API keys in `.env` are valid
2. **Credential Issues**: Test social media credentials before posting
3. **Image Generation Fails**: Check OpenAI API quota and key validity
4. **Posting Failures**: Verify social media app permissions

### Logs

Check logs in `./data/logs/`:
- `posting_log.jsonl` - Posting attempts and results
- `daily_posting_log.jsonl` - Automated posting history

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

## Advanced Configuration

### Custom Content Strategies

Modify `config/posting_config.json`:

```json
{
  "content_strategy": {
    "default_tone": "professional",
    "include_hashtags": true,
    "max_hashtags": 5,
    "image_generation": true,
    "content_themes": ["tech", "innovation", "quality"]
  }
}
```

### Platform-Specific Settings

Each platform can have specific configurations:

- **Instagram**: Supports feed posts and stories
- **Twitter**: Optimized for character limits
- **LinkedIn**: Professional tone and business focus

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Encrypt credentials** before storage
4. **Regularly rotate** API keys
5. **Monitor usage** and set up alerts

## Support

For issues and questions:
1. Check the logs in `./data/logs/`
2. Run the test suite: `python scripts/test_agent.py`
3. Review the API documentation at `/docs`
4. Check the health endpoint: `/health`