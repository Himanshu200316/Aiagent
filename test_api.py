#!/usr/bin/env python3
"""
API Test Script for Social Media Advertising Agent
Tests all major endpoints and functionality
"""

import requests
import json
import time
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpassword123"
}

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=TEST_USER
            )
            
            if response.status_code == 200:
                print("✅ User registration passed")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                print("✅ User already exists (expected)")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ User registration error: {e}")
            return False
    
    def test_user_login(self) -> bool:
        """Test user login"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print("✅ User login passed")
                return True
            else:
                print(f"❌ User login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ User login error: {e}")
            return False
    
    def test_get_current_user(self) -> bool:
        """Test get current user info"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["id"]
                print("✅ Get current user passed")
                return True
            else:
                print(f"❌ Get current user failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Get current user error: {e}")
            return False
    
    def test_content_generation(self) -> bool:
        """Test content generation"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "product_description": "Test product for API testing",
                "tone": "professional",
                "target_audience": "developers",
                "platforms": ["instagram"],
                "generate_image": False  # Skip image generation for faster testing
            }
            
            response = requests.post(
                f"{self.base_url}/api/content/generate",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Content generation passed")
                    return True
                else:
                    print(f"❌ Content generation failed: {data.get('error')}")
                    return False
            else:
                print(f"❌ Content generation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Content generation error: {e}")
            return False
    
    def test_schedule_setup(self) -> bool:
        """Test schedule setup"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "post_time": "12:00",
                "frequency": "daily",
                "platforms": ["instagram"],
                "enabled": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/scheduling/setup",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                print("✅ Schedule setup passed")
                return True
            else:
                print(f"❌ Schedule setup failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Schedule setup error: {e}")
            return False
    
    def test_get_schedule(self) -> bool:
        """Test get current schedule"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/scheduling/current", headers=headers)
            
            if response.status_code == 200:
                print("✅ Get schedule passed")
                return True
            else:
                print(f"❌ Get schedule failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Get schedule error: {e}")
            return False
    
    def test_cerebrus_status(self) -> bool:
        """Test Cerebrus status endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/cerebrus/status", headers=headers)
            
            if response.status_code == 200:
                print("✅ Cerebrus status passed")
                return True
            else:
                print(f"❌ Cerebrus status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cerebrus status error: {e}")
            return False
    
    def test_cerebrus_help(self) -> bool:
        """Test Cerebrus help endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/cerebrus/help")
            
            if response.status_code == 200:
                print("✅ Cerebrus help passed")
                return True
            else:
                print(f"❌ Cerebrus help failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cerebrus help error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🧪 Starting API Tests...")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Get Current User", self.test_get_current_user),
            ("Content Generation", self.test_content_generation),
            ("Schedule Setup", self.test_schedule_setup),
            ("Get Schedule", self.test_get_schedule),
            ("Cerebrus Status", self.test_cerebrus_status),
            ("Cerebrus Help", self.test_cerebrus_help),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(1)  # Small delay between tests
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return False

def main():
    """Main test function"""
    print("🤖 Social Media Advertising Agent - API Test Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running. Please start the server first:")
            print("   docker-compose up -d")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Please ensure:")
        print("   1. Server is running: docker-compose up -d")
        print("   2. Server is accessible at http://localhost:8000")
        return False
    
    # Run tests
    tester = APITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 API is ready for use!")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")
    else:
        print("\n❌ API tests failed. Please check the server logs:")
        print("   docker-compose logs")
    
    return success

if __name__ == "__main__":
    main()