#!/bin/bash

# Test script for AI Social Media Ad Agent API

set -e

BASE_URL="http://localhost:8000"
USER_ID="test_user_$(date +%s)"

echo "🧪 Testing AI Social Media Ad Agent API..."
echo "Base URL: $BASE_URL"
echo "Test User ID: $USER_ID"
echo ""

# Test health check
echo "1. Testing health check..."
curl -s "$BASE_URL/health" | jq '.' || echo "❌ Health check failed"
echo ""

# Test user registration
echo "2. Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USER_ID\", \"email\": \"$USER_ID@test.com\", \"password\": \"testpass123\"}")

ACCESS_TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.access_token')
echo "Access token obtained: ${ACCESS_TOKEN:0:20}..."
echo ""

# Test starting a conversation
echo "3. Testing conversation start..."
CONVERSATION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat/start" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"conversation_type\": \"ad_setup\"}")

CONVERSATION_ID=$(echo $CONVERSATION_RESPONSE | jq -r '.conversation_id')
echo "Conversation started: $CONVERSATION_ID"
echo ""

# Test sending a message
echo "4. Testing conversation message..."
curl -s -X POST "$BASE_URL/api/chat/message" \
  -H "Content-Type: application/json" \
  -d "{\"conversation_id\": \"$CONVERSATION_ID\", \"user_id\": \"$USER_ID\", \"message\": \"Yes, I want to start setting up my ad campaign\"}" | jq '.'
echo ""

# Test content generation (requires auth)
echo "5. Testing content generation..."
curl -s -X POST "$BASE_URL/api/content/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "product_service_description": "Revolutionary fitness app that helps people achieve their health goals",
    "target_audience": "Health-conscious millennials aged 25-35",
    "tone": "energetic",
    "platforms": ["instagram", "twitter"],
    "content_type": "feed_post"
  }' | jq '.' || echo "❌ Content generation failed (expected if AI services not configured)"
echo ""

# Test campaign creation
echo "6. Testing campaign creation..."
curl -s -X POST "$BASE_URL/api/posting/campaigns" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Test Fitness Campaign",
    "description": "Testing campaign creation",
    "product_service_description": "Revolutionary fitness app",
    "target_audience": "Health-conscious millennials",
    "tone": "energetic",
    "platforms": ["instagram", "twitter"]
  }' | jq '.' || echo "❌ Campaign creation failed"
echo ""

# Test getting campaigns
echo "7. Testing campaign retrieval..."
curl -s -X GET "$BASE_URL/api/posting/campaigns" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' || echo "❌ Campaign retrieval failed"
echo ""

# Test scheduler health
echo "8. Testing scheduler health..."
curl -s "$BASE_URL/api/posting/health" | jq '.' || echo "❌ Scheduler health check failed"
echo ""

echo "✅ API testing complete!"
echo ""
echo "📝 Notes:"
echo "   • Some tests may fail if AI services are not configured"
echo "   • Social media posting requires valid credentials"
echo "   • Check logs for detailed error information"