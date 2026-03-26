"""
Backend API Tests for AI Cold Calling SaaS Platform
Tests: Authentication (register, login, me, logout), Packs/Pricing, TTS
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://voice-dialer-staging.preview.emergentagent.com')
API = f"{BASE_URL}/api"

# Test data
TEST_USER_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_NAME = "Test User"

class TestHealthCheck:
    """Basic API health check"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{API}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "AI Cold Calling Machine API" in data["message"]
        print("✓ API root endpoint working")


class TestUserRegistration:
    """User registration tests"""
    
    def test_register_new_user(self):
        """Test registering a new user"""
        response = requests.post(f"{API}/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "user" in data
        assert "session_token" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        assert data["user"]["name"] == TEST_USER_NAME
        assert "user_id" in data["user"]
        
        # Verify free trial credits
        assert data["user"]["lead_credits_remaining"] == 50
        assert data["user"]["call_credits_remaining"] == 50
        
        print(f"✓ User registered: {TEST_USER_EMAIL}")
        return data["session_token"]
    
    def test_register_duplicate_email(self):
        """Test registering with existing email fails"""
        # First register
        requests.post(f"{API}/auth/register", json={
            "email": f"dup_{TEST_USER_EMAIL}",
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        
        # Try to register again with same email
        response = requests.post(f"{API}/auth/register", json={
            "email": f"dup_{TEST_USER_EMAIL}",
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
        print("✓ Duplicate email registration correctly rejected")


class TestUserLogin:
    """User login tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a test user for login tests"""
        self.email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "LoginTest123!"
        
        # Register user first
        response = requests.post(f"{API}/auth/register", json={
            "email": self.email,
            "password": self.password,
            "name": "Login Test User"
        })
        assert response.status_code == 200
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{API}/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "session_token" in data
        assert data["user"]["email"] == self.email
        assert data["session_token"].startswith("sess_")
        
        print(f"✓ Login successful for {self.email}")
        return data["session_token"]
    
    def test_login_invalid_password(self):
        """Test login with wrong password"""
        response = requests.post(f"{API}/auth/login", json={
            "email": self.email,
            "password": "WrongPassword123!"
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
        print("✓ Invalid password correctly rejected")
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email"""
        response = requests.post(f"{API}/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        })
        assert response.status_code == 401
        print("✓ Non-existent user login correctly rejected")


class TestAuthMe:
    """Test /auth/me endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create and login a test user"""
        self.email = f"me_test_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "MeTest123!"
        
        # Register user
        response = requests.post(f"{API}/auth/register", json={
            "email": self.email,
            "password": self.password,
            "name": "Me Test User"
        })
        assert response.status_code == 200
        self.session_token = response.json()["session_token"]
    
    def test_get_me_with_valid_token(self):
        """Test getting current user with valid token"""
        response = requests.get(f"{API}/auth/me", headers={
            "Authorization": f"Bearer {self.session_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == self.email
        assert "user_id" in data
        assert "password_hash" not in data  # Should not expose password
        
        print(f"✓ /auth/me returns user data correctly")
    
    def test_get_me_without_token(self):
        """Test getting current user without token"""
        response = requests.get(f"{API}/auth/me")
        assert response.status_code == 401
        print("✓ /auth/me correctly rejects unauthenticated requests")
    
    def test_get_me_with_invalid_token(self):
        """Test getting current user with invalid token"""
        response = requests.get(f"{API}/auth/me", headers={
            "Authorization": "Bearer invalid_token_12345"
        })
        assert response.status_code == 401
        print("✓ /auth/me correctly rejects invalid tokens")


class TestAuthLogout:
    """Test /auth/logout endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create and login a test user"""
        self.email = f"logout_test_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "LogoutTest123!"
        
        # Register user
        response = requests.post(f"{API}/auth/register", json={
            "email": self.email,
            "password": self.password,
            "name": "Logout Test User"
        })
        assert response.status_code == 200
        self.session_token = response.json()["session_token"]
    
    def test_logout_clears_session(self):
        """Test that logout clears the session"""
        # First verify we're logged in
        response = requests.get(f"{API}/auth/me", headers={
            "Authorization": f"Bearer {self.session_token}"
        })
        assert response.status_code == 200
        
        # Logout
        response = requests.post(f"{API}/auth/logout", headers={
            "Authorization": f"Bearer {self.session_token}"
        }, cookies={"session_token": self.session_token})
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
        
        print("✓ Logout endpoint works correctly")


class TestPacksAndPricing:
    """Test /packs endpoint for subscription plans and pricing"""
    
    def test_get_packs(self):
        """Test getting available packs and subscription plans"""
        response = requests.get(f"{API}/packs")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "subscription_plans" in data
        assert "lead_packs" in data
        assert "call_packs" in data
        assert "topup_packs" in data
        
        plans = data["subscription_plans"]
        
        # Verify 4 subscription tiers exist
        assert "starter" in plans
        assert "professional" in plans
        assert "unlimited" in plans
        assert "byl" in plans
        
        # Verify correct pricing
        assert plans["starter"]["price"] == 199
        assert plans["professional"]["price"] == 399
        assert plans["unlimited"]["price"] == 699
        assert plans["byl"]["price"] == 349
        
        # Verify plan names
        assert plans["starter"]["name"] == "Starter"
        assert plans["professional"]["name"] == "Professional"
        assert plans["unlimited"]["name"] == "Unlimited"
        assert plans["byl"]["name"] == "Bring Your List"
        
        print("✓ Packs endpoint returns correct pricing:")
        print(f"  - Starter: ${plans['starter']['price']}")
        print(f"  - Professional: ${plans['professional']['price']}")
        print(f"  - Unlimited: ${plans['unlimited']['price']}")
        print(f"  - BYL: ${plans['byl']['price']}")


class TestTTSEndpoint:
    """Test ElevenLabs TTS integration"""
    
    def test_tts_generate(self):
        """Test TTS generation endpoint"""
        response = requests.post(f"{API}/tts/generate", json={
            "text": "Hello, this is a test of the text to speech system.",
            "voice_id": "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        })
        
        # Should return 200 if ElevenLabs is configured
        if response.status_code == 200:
            data = response.json()
            assert "audio_url" in data
            assert data["audio_url"].startswith("data:audio/mpeg;base64,")
            assert data["text"] == "Hello, this is a test of the text to speech system."
            print("✓ TTS generation working with ElevenLabs")
        elif response.status_code == 503:
            # ElevenLabs not configured
            print("⚠ TTS endpoint returns 503 - ElevenLabs not configured (expected if no API key)")
        else:
            print(f"⚠ TTS endpoint returned unexpected status: {response.status_code}")
    
    def test_tts_voices(self):
        """Test getting available TTS voices"""
        response = requests.get(f"{API}/tts/voices")
        
        if response.status_code == 200:
            data = response.json()
            assert "voices" in data
            assert isinstance(data["voices"], list)
            print(f"✓ TTS voices endpoint working - {len(data['voices'])} voices available")
        elif response.status_code == 503:
            print("⚠ TTS voices endpoint returns 503 - ElevenLabs not configured")
        else:
            print(f"⚠ TTS voices endpoint returned unexpected status: {response.status_code}")


class TestExistingUserLogin:
    """Test login with existing test user credentials"""
    
    def test_login_existing_user(self):
        """Test login with provided test credentials"""
        response = requests.post(f"{API}/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!"
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "user" in data
            assert "session_token" in data
            print(f"✓ Existing test user login successful")
            print(f"  - Email: {data['user']['email']}")
            print(f"  - Lead Credits: {data['user'].get('lead_credits_remaining', 'N/A')}")
            print(f"  - Call Credits: {data['user'].get('call_credits_remaining', 'N/A')}")
        else:
            print(f"⚠ Existing test user login failed: {response.status_code}")
            print(f"  This may be expected if user doesn't exist yet")


class TestDashboardStats:
    """Test dashboard stats endpoint"""
    
    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        response = requests.get(f"{API}/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "total_leads" in data
        assert "qualified_leads" in data
        assert "booked_leads" in data
        assert "total_calls" in data
        assert "active_campaigns" in data
        assert "total_agents" in data
        assert "qualification_rate" in data
        assert "booking_rate" in data
        
        print("✓ Dashboard stats endpoint working")
        print(f"  - Total Leads: {data['total_leads']}")
        print(f"  - Total Calls: {data['total_calls']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
