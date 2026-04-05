"""
Auth Module Tests - Testing the new modular auth routes
Tests the extracted auth routes from routes/auth.py and services/auth_service.py
Part of Strangler Fig refactoring - Phase 2 (Auth Module)

Endpoints tested:
- POST /api/auth/login - Login with email/password
- GET /api/auth/me - Get current user (requires auth)
- POST /api/auth/logout - Logout and clear session
- POST /api/auth/session - OAuth session exchange
- POST /api/auth/send-verification - Send phone verification SMS
- POST /api/auth/verify-phone - Verify phone code
"""
import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "test@example.com"
ADMIN_PASSWORD = "Test123!"


class TestAuthLogin:
    """Test POST /api/auth/login endpoint"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "user" in data, "Response should contain 'user' field"
        assert "session_token" in data, "Response should contain 'session_token' field"
        
        # Validate user data
        user = data["user"]
        assert user["email"] == ADMIN_EMAIL, f"Expected email {ADMIN_EMAIL}, got {user.get('email')}"
        assert "user_id" in user, "User should have user_id"
        assert "password_hash" not in user, "Password hash should not be returned"
        
        # Validate session token format
        session_token = data["session_token"]
        assert isinstance(session_token, str), "Session token should be a string"
        assert session_token.startswith("sess_"), f"Session token should start with 'sess_', got {session_token[:10]}"
        
        # Check cookies are set
        assert "session_token" in response.cookies, "session_token cookie should be set"
        
        print(f"✓ Login successful for {ADMIN_EMAIL}")
        print(f"  - User ID: {user.get('user_id')}")
        print(f"  - Session token: {session_token[:20]}...")
    
    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpass"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"✓ Invalid email correctly rejected with 401")
    
    def test_login_invalid_password(self):
        """Test login with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "WrongPassword123!"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"✓ Invalid password correctly rejected with 401")
    
    def test_login_missing_fields(self):
        """Test login with missing required fields"""
        # Missing password
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL}
        )
        assert response.status_code == 422, f"Expected 422 for missing password, got {response.status_code}"
        
        # Missing email
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"password": "Test123!"}
        )
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}"
        
        print(f"✓ Missing fields correctly rejected with 422")


class TestAuthMe:
    """Test GET /api/auth/me endpoint"""
    
    @pytest.fixture
    def auth_session(self):
        """Get authenticated session"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data["session_token"], response.cookies
    
    def test_get_me_with_bearer_token(self, auth_session):
        """Test GET /api/auth/me with Authorization header"""
        session_token, _ = auth_session
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["email"] == ADMIN_EMAIL, f"Expected email {ADMIN_EMAIL}, got {data.get('email')}"
        assert "user_id" in data, "Response should contain user_id"
        assert "password_hash" not in data, "Password hash should not be returned"
        
        # Check trial status is included
        assert "trial_status" in data, "Response should include trial_status"
        
        print(f"✓ GET /api/auth/me with Bearer token successful")
        print(f"  - User: {data.get('name', data.get('email'))}")
        print(f"  - Role: {data.get('role')}")
    
    def test_get_me_with_cookie(self, auth_session):
        """Test GET /api/auth/me with session cookie"""
        _, cookies = auth_session
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            cookies=cookies
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ GET /api/auth/me with cookie successful")
    
    def test_get_me_no_auth(self):
        """Test GET /api/auth/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ GET /api/auth/me without auth correctly rejected with 401")
    
    def test_get_me_invalid_token(self):
        """Test GET /api/auth/me with invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ GET /api/auth/me with invalid token correctly rejected with 401")


class TestAuthLogout:
    """Test POST /api/auth/logout endpoint"""
    
    def test_logout_success(self):
        """Test successful logout"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200
        session_token = login_response.json()["session_token"]
        cookies = login_response.cookies
        
        # Verify session works before logout
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        assert me_response.status_code == 200, "Session should be valid before logout"
        
        # Logout
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            cookies=cookies
        )
        
        assert logout_response.status_code == 200, f"Expected 200, got {logout_response.status_code}"
        data = logout_response.json()
        assert "message" in data, "Logout response should have message"
        
        print(f"✓ Logout successful")
        
        # Verify session is invalidated after logout
        me_after_logout = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        assert me_after_logout.status_code == 401, "Session should be invalid after logout"
        print(f"✓ Session correctly invalidated after logout")
    
    def test_logout_without_session(self):
        """Test logout without active session (should still succeed)"""
        response = requests.post(f"{BASE_URL}/api/auth/logout")
        
        # Logout should succeed even without session
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Logout without session returns 200")


class TestSessionPersistence:
    """Test session token works across multiple requests"""
    
    def test_session_persists_across_requests(self):
        """Test that session token works for multiple requests"""
        # Login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200
        session_token = login_response.json()["session_token"]
        
        # Make multiple requests with same token
        for i in range(3):
            response = requests.get(
                f"{BASE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {session_token}"}
            )
            assert response.status_code == 200, f"Request {i+1} failed: {response.text}"
        
        print(f"✓ Session token persists across multiple requests")


class TestPhoneVerification:
    """Test phone verification endpoints"""
    
    def test_send_verification_existing_email(self):
        """Test send-verification with already registered email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/send-verification",
            json={
                "phone_number": "+15551234567",
                "email": ADMIN_EMAIL  # Already registered
            }
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "already registered" in data.get("detail", "").lower(), f"Expected 'already registered' error, got: {data}"
        print(f"✓ send-verification correctly rejects registered email")
    
    def test_send_verification_new_email(self):
        """Test send-verification with new email
        Note: In production with Twilio configured, this may fail with 500 if phone is invalid.
        We test that the endpoint is reachable and validates input correctly.
        """
        import uuid
        test_email = f"test_verify_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/send-verification",
            json={
                "phone_number": "+15559876543",  # 555 numbers are fictional
                "email": test_email
            }
        )
        
        # With Twilio configured, 555 numbers will fail SMS delivery (500)
        # Without Twilio, it would succeed (200) with code logged
        # Both are valid behaviors depending on environment
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data, "Response should have message"
            assert "phone_number" in data, "Response should have phone_number"
            print(f"✓ send-verification works for new email (dev mode - no Twilio)")
        else:
            # 500 means Twilio is configured but phone number is invalid
            data = response.json()
            assert "detail" in data, "Error response should have detail"
            print(f"✓ send-verification endpoint reachable (Twilio configured, invalid test phone)")
    
    def test_verify_phone_invalid_code(self):
        """Test verify-phone with invalid code"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-phone",
            json={
                "phone_number": "+15551234567",
                "code": "000000"  # Invalid code
            }
        )
        
        # Should fail with 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ verify-phone correctly rejects invalid code")


class TestOAuthSession:
    """Test OAuth session exchange endpoint"""
    
    def test_session_exchange_missing_session_id(self):
        """Test session exchange without session_id"""
        response = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "session_id required" in data.get("detail", "").lower() or "session_id" in data.get("detail", "").lower()
        print(f"✓ session exchange correctly requires session_id")
    
    def test_session_exchange_invalid_session_id(self):
        """Test session exchange with invalid session_id"""
        response = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={"session_id": "invalid_session_id_12345"}
        )
        
        # Should fail with 401 (invalid session) or 500 (auth service error)
        assert response.status_code in [401, 500], f"Expected 401 or 500, got {response.status_code}"
        print(f"✓ session exchange correctly rejects invalid session_id")


class TestCookieSettings:
    """Test that cookies are set correctly"""
    
    def test_login_sets_cookie_correctly(self):
        """Test that login sets session_token cookie with correct attributes"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        assert response.status_code == 200
        
        # Check cookie is set
        assert "session_token" in response.cookies, "session_token cookie should be set"
        
        # Get cookie details from Set-Cookie header
        set_cookie = response.headers.get("set-cookie", "")
        
        # Verify cookie attributes (case-insensitive check)
        set_cookie_lower = set_cookie.lower()
        assert "httponly" in set_cookie_lower, "Cookie should be httpOnly"
        assert "path=/" in set_cookie_lower, "Cookie should have path=/"
        
        print(f"✓ Login sets cookie with correct attributes")
        print(f"  - Set-Cookie header: {set_cookie[:100]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
