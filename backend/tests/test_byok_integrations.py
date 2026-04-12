"""
BYOK (Bring Your Own Key) Integration Tests
Tests for Twilio and ElevenLabs credential verification, storage, and balance checking.

Endpoints tested:
- POST /api/settings/verify-twilio - Verify Twilio credentials and get balance
- POST /api/settings/verify-elevenlabs - Verify ElevenLabs API key and get credits
- POST /api/settings/integrations - Save encrypted BYOK credentials
- GET /api/settings/integrations/status - Check if user has configured BYOK credentials
- GET /api/settings/integrations/balances - Get real-time balances for stored credentials
"""

import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}

# Real Twilio credentials from backend/.env (loaded from environment)
REAL_TWILIO_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'AC_test_placeholder')
REAL_TWILIO_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'test_token_placeholder')

# Real ElevenLabs key from backend/.env (loaded from environment)
REAL_ELEVENLABS_KEY = os.environ.get('ELEVENLABS_API_KEY', 'sk_test_placeholder')


class TestAuthHelper:
    """Helper class for authentication"""
    
    @staticmethod
    def get_auth_token(email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token") or data.get("token") or data.get("access_token")
        print(f"Login failed for {email}: {response.status_code} - {response.text[:200]}")
        return None
    
    @staticmethod
    def get_auth_headers(token: str) -> dict:
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


# ============== VERIFY TWILIO ENDPOINT TESTS ==============

class TestVerifyTwilioEndpoint:
    """Tests for POST /api/settings/verify-twilio"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_verify_twilio_valid_credentials(self):
        """POST /api/settings/verify-twilio - Should return valid=true and balance for valid credentials"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-twilio",
            json={
                "account_sid": REAL_TWILIO_SID,
                "auth_token": REAL_TWILIO_TOKEN
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("valid") == True, f"Expected valid=true, got {data}"
        assert "balance" in data, "Response should contain balance"
        assert isinstance(data["balance"], (int, float)), "Balance should be a number"
        assert "currency" in data, "Response should contain currency"
        
        print(f"Twilio verification SUCCESS: balance=${data['balance']:.2f} {data['currency']}")
    
    def test_verify_twilio_invalid_credentials(self):
        """POST /api/settings/verify-twilio - Should return valid=false for invalid credentials"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-twilio",
            json={
                "account_sid": "ACinvalid123456789012345678901234",
                "auth_token": "invalid_token_12345678901234567890"
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("valid") == False, f"Expected valid=false for invalid credentials, got {data}"
        assert "message" in data, "Response should contain error message"
        
        print(f"Twilio invalid credentials correctly rejected: {data.get('message')}")
    
    def test_verify_twilio_unauthenticated(self):
        """POST /api/settings/verify-twilio - Should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-twilio",
            json={
                "account_sid": REAL_TWILIO_SID,
                "auth_token": REAL_TWILIO_TOKEN
            }
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Twilio verification correctly requires authentication")
    
    def test_verify_twilio_missing_fields(self):
        """POST /api/settings/verify-twilio - Should validate required fields"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        # Missing auth_token
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-twilio",
            json={"account_sid": REAL_TWILIO_SID},
            headers=self.headers
        )
        
        assert response.status_code == 422, f"Expected 422 for missing field, got {response.status_code}"
        print("Twilio verification correctly validates required fields")


# ============== VERIFY ELEVENLABS ENDPOINT TESTS ==============

class TestVerifyElevenLabsEndpoint:
    """Tests for POST /api/settings/verify-elevenlabs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_verify_elevenlabs_valid_key(self):
        """POST /api/settings/verify-elevenlabs - Should return valid=true for valid API key"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-elevenlabs",
            json={"api_key": REAL_ELEVENLABS_KEY},
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("valid") == True, f"Expected valid=true, got {data}"
        # Note: This key lacks user_read permission, so credits may be None
        # but the key should still be verified via /v1/voices fallback
        
        print(f"ElevenLabs verification SUCCESS: {data.get('message')}")
        if data.get("credits"):
            print(f"  Credits: {data['credits']}")
    
    def test_verify_elevenlabs_invalid_key(self):
        """POST /api/settings/verify-elevenlabs - Should return valid=false for invalid API key"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-elevenlabs",
            json={"api_key": "sk_invalid_key_12345678901234567890"},
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("valid") == False, f"Expected valid=false for invalid key, got {data}"
        assert "message" in data, "Response should contain error message"
        
        print(f"ElevenLabs invalid key correctly rejected: {data.get('message')}")
    
    def test_verify_elevenlabs_unauthenticated(self):
        """POST /api/settings/verify-elevenlabs - Should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-elevenlabs",
            json={"api_key": REAL_ELEVENLABS_KEY}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("ElevenLabs verification correctly requires authentication")
    
    def test_verify_elevenlabs_missing_key(self):
        """POST /api/settings/verify-elevenlabs - Should validate required api_key field"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/verify-elevenlabs",
            json={},
            headers=self.headers
        )
        
        assert response.status_code == 422, f"Expected 422 for missing field, got {response.status_code}"
        print("ElevenLabs verification correctly validates required fields")


# ============== SAVE INTEGRATIONS ENDPOINT TESTS ==============

class TestSaveIntegrationsEndpoint:
    """Tests for POST /api/settings/integrations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_save_twilio_credentials(self):
        """POST /api/settings/integrations - Should save encrypted Twilio credentials"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/integrations",
            json={
                "twilio": {
                    "account_sid": REAL_TWILIO_SID,
                    "auth_token": REAL_TWILIO_TOKEN,
                    "phone_number": "+14044676189"
                }
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "saved_at" in data, "Response should contain saved_at timestamp"
        
        print(f"Twilio credentials saved: {data.get('message')} at {data.get('saved_at')}")
    
    def test_save_elevenlabs_credentials(self):
        """POST /api/settings/integrations - Should save encrypted ElevenLabs credentials"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/integrations",
            json={
                "elevenlabs": {
                    "api_key": REAL_ELEVENLABS_KEY
                }
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "saved_at" in data, "Response should contain saved_at timestamp"
        
        print(f"ElevenLabs credentials saved: {data.get('message')} at {data.get('saved_at')}")
    
    def test_save_both_integrations(self):
        """POST /api/settings/integrations - Should save both Twilio and ElevenLabs credentials"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.post(
            f"{BASE_URL}/api/settings/integrations",
            json={
                "twilio": {
                    "account_sid": REAL_TWILIO_SID,
                    "auth_token": REAL_TWILIO_TOKEN,
                    "phone_number": "+14044676189"
                },
                "elevenlabs": {
                    "api_key": REAL_ELEVENLABS_KEY
                }
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        
        print(f"Both integrations saved: {data.get('message')}")
    
    def test_save_integrations_unauthenticated(self):
        """POST /api/settings/integrations - Should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/settings/integrations",
            json={
                "twilio": {
                    "account_sid": REAL_TWILIO_SID,
                    "auth_token": REAL_TWILIO_TOKEN
                }
            }
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Save integrations correctly requires authentication")


# ============== INTEGRATION STATUS ENDPOINT TESTS ==============

class TestIntegrationStatusEndpoint:
    """Tests for GET /api/settings/integrations/status"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_get_integration_status(self):
        """GET /api/settings/integrations/status - Should return connection status for both integrations"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/settings/integrations/status",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "twilio_connected" in data, "Response should contain twilio_connected"
        assert "elevenlabs_connected" in data, "Response should contain elevenlabs_connected"
        assert isinstance(data["twilio_connected"], bool), "twilio_connected should be boolean"
        assert isinstance(data["elevenlabs_connected"], bool), "elevenlabs_connected should be boolean"
        
        print(f"Integration status: Twilio={data['twilio_connected']}, ElevenLabs={data['elevenlabs_connected']}")
        if data.get("twilio_phone_number"):
            print(f"  Twilio phone: {data['twilio_phone_number']}")
        if data.get("byok_updated_at"):
            print(f"  Last updated: {data['byok_updated_at']}")
    
    def test_get_integration_status_unauthenticated(self):
        """GET /api/settings/integrations/status - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/settings/integrations/status")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Integration status correctly requires authentication")


# ============== INTEGRATION BALANCES ENDPOINT TESTS ==============

class TestIntegrationBalancesEndpoint:
    """Tests for GET /api/settings/integrations/balances"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_get_integration_balances(self):
        """GET /api/settings/integrations/balances - Should return real-time balances"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        # First ensure credentials are saved
        requests.post(
            f"{BASE_URL}/api/settings/integrations",
            json={
                "twilio": {
                    "account_sid": REAL_TWILIO_SID,
                    "auth_token": REAL_TWILIO_TOKEN
                },
                "elevenlabs": {
                    "api_key": REAL_ELEVENLABS_KEY
                }
            },
            headers=self.headers
        )
        
        response = requests.get(
            f"{BASE_URL}/api/settings/integrations/balances",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "twilio" in data, "Response should contain twilio balance info"
        assert "elevenlabs" in data, "Response should contain elevenlabs balance info"
        
        # Check Twilio balance structure
        if data["twilio"]:
            if "error" not in data["twilio"]:
                assert "balance" in data["twilio"], "Twilio should have balance"
                assert "currency" in data["twilio"], "Twilio should have currency"
                assert "low" in data["twilio"], "Twilio should have low indicator"
                print(f"Twilio balance: ${data['twilio']['balance']:.2f} {data['twilio']['currency']}, low={data['twilio']['low']}")
            else:
                print(f"Twilio balance error: {data['twilio']['error']}")
        
        # Check ElevenLabs balance structure
        if data["elevenlabs"]:
            if "error" not in data["elevenlabs"]:
                assert "remaining_percent" in data["elevenlabs"], "ElevenLabs should have remaining_percent"
                assert "low" in data["elevenlabs"], "ElevenLabs should have low indicator"
                print(f"ElevenLabs credits: {data['elevenlabs']['remaining_percent']}% remaining, low={data['elevenlabs']['low']}")
            else:
                # Expected for key without user_read permission
                print(f"ElevenLabs balance error (expected for limited key): {data['elevenlabs']['error']}")
    
    def test_get_integration_balances_unauthenticated(self):
        """GET /api/settings/integrations/balances - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/settings/integrations/balances")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Integration balances correctly requires authentication")


# ============== END-TO-END FLOW TESTS ==============

class TestBYOKEndToEndFlow:
    """End-to-end tests for the complete BYOK setup flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_complete_byok_setup_flow(self):
        """Test complete BYOK setup: verify -> save -> check status -> get balances"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        # Step 1: Verify Twilio credentials
        print("\n=== Step 1: Verify Twilio credentials ===")
        twilio_verify = requests.post(
            f"{BASE_URL}/api/settings/verify-twilio",
            json={
                "account_sid": REAL_TWILIO_SID,
                "auth_token": REAL_TWILIO_TOKEN
            },
            headers=self.headers
        )
        assert twilio_verify.status_code == 200
        assert twilio_verify.json().get("valid") == True
        print(f"Twilio verified: balance=${twilio_verify.json().get('balance', 0):.2f}")
        
        # Step 2: Verify ElevenLabs credentials
        print("\n=== Step 2: Verify ElevenLabs credentials ===")
        elevenlabs_verify = requests.post(
            f"{BASE_URL}/api/settings/verify-elevenlabs",
            json={"api_key": REAL_ELEVENLABS_KEY},
            headers=self.headers
        )
        assert elevenlabs_verify.status_code == 200
        assert elevenlabs_verify.json().get("valid") == True
        print(f"ElevenLabs verified: {elevenlabs_verify.json().get('message')}")
        
        # Step 3: Save both integrations
        print("\n=== Step 3: Save integrations ===")
        save_response = requests.post(
            f"{BASE_URL}/api/settings/integrations",
            json={
                "twilio": {
                    "account_sid": REAL_TWILIO_SID,
                    "auth_token": REAL_TWILIO_TOKEN,
                    "phone_number": "+14044676189"
                },
                "elevenlabs": {
                    "api_key": REAL_ELEVENLABS_KEY
                }
            },
            headers=self.headers
        )
        assert save_response.status_code == 200
        print(f"Integrations saved at: {save_response.json().get('saved_at')}")
        
        # Step 4: Check integration status
        print("\n=== Step 4: Check integration status ===")
        status_response = requests.get(
            f"{BASE_URL}/api/settings/integrations/status",
            headers=self.headers
        )
        assert status_response.status_code == 200
        status = status_response.json()
        assert status.get("twilio_connected") == True, "Twilio should be connected"
        assert status.get("elevenlabs_connected") == True, "ElevenLabs should be connected"
        print(f"Status: Twilio={status['twilio_connected']}, ElevenLabs={status['elevenlabs_connected']}")
        
        # Step 5: Get real-time balances
        print("\n=== Step 5: Get real-time balances ===")
        balances_response = requests.get(
            f"{BASE_URL}/api/settings/integrations/balances",
            headers=self.headers
        )
        assert balances_response.status_code == 200
        balances = balances_response.json()
        
        if balances.get("twilio") and "balance" in balances["twilio"]:
            print(f"Twilio balance: ${balances['twilio']['balance']:.2f}, low={balances['twilio']['low']}")
        
        if balances.get("elevenlabs"):
            if "error" in balances["elevenlabs"]:
                print(f"ElevenLabs: {balances['elevenlabs']['error']}")
            else:
                print(f"ElevenLabs: {balances['elevenlabs']['remaining_percent']}% remaining")
        
        print("\n=== BYOK Setup Flow Complete ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
