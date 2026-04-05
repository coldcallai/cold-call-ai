"""
Test Calls Module (Phase 6 Strangler Fig)
Tests for /app/backend/routes/calls.py - READ operations and analytics only.

Endpoints tested:
- GET /api/calls/twilio-status - Check Twilio configuration
- GET /api/calls - List calls for authenticated user
- GET /api/calls/{call_id} - Get specific call by ID
- GET /api/analytics?range=7d - Get call analytics
- GET /api/calls/{call_id}/amd-status - Get AMD status for a call
- GET /api/calls/{call_id}/recording - Get recording (requires Starter tier)
- GET /api/calls/{call_id}/transcript - Get transcript (requires Professional tier)

Note: Twilio webhooks and call initiation remain in server.py
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}
USER_B = {"email": "test_user_b@example.com", "password": "Test456!"}
STARTER_USER = {"email": "test_starter_1ea49b76@example.com", "password": "Test123!"}


class TestCallsModuleSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin user token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        """Get User B token for isolation tests"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if resp.status_code != 200:
            pytest.skip("User B not available for isolation tests")
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def starter_token(self):
        """Get Starter tier user token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=STARTER_USER)
        if resp.status_code != 200:
            pytest.skip("Starter user not available")
        return resp.json().get("session_token")
    
    def test_admin_login(self, admin_token):
        """Verify admin user can login"""
        assert admin_token is not None
        assert len(admin_token) > 10
        print(f"Admin token obtained: {admin_token[:20]}...")


class TestTwilioStatus:
    """Tests for GET /api/calls/twilio-status"""
    
    def test_twilio_status_returns_configuration(self):
        """Twilio status endpoint should return configuration info"""
        resp = requests.get(f"{BASE_URL}/api/calls/twilio-status")
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify response structure
        assert "configured" in data
        assert "phone_number" in data
        assert isinstance(data["configured"], bool)
        
        # If configured, phone number should be partially masked
        if data["configured"]:
            assert data["phone_number"] is not None
            assert "****" in data["phone_number"]  # Should be masked
        
        print(f"Twilio status: configured={data['configured']}, phone={data['phone_number']}")


class TestCallsList:
    """Tests for GET /api/calls - List calls"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200
        return resp.json().get("session_token")
    
    def test_list_calls_requires_auth(self):
        """GET /api/calls should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/calls")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
    
    def test_list_calls_authenticated(self, admin_token):
        """GET /api/calls should return user's calls"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} calls for admin user")
        
        # Verify call structure if calls exist
        if len(data) > 0:
            call = data[0]
            assert "id" in call
            assert "user_id" in call
            assert "lead_id" in call
            assert "campaign_id" in call
            assert "status" in call
            assert "created_at" in call
    
    def test_list_calls_with_status_filter(self, admin_token):
        """GET /api/calls?status=completed should filter by status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls?status=completed", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        assert isinstance(data, list)
        
        # All returned calls should have completed status
        for call in data:
            assert call.get("status") == "completed", f"Expected completed, got {call.get('status')}"
        
        print(f"Found {len(data)} completed calls")
    
    def test_list_calls_with_limit(self, admin_token):
        """GET /api/calls?limit=5 should limit results"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls?limit=5", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        print(f"Returned {len(data)} calls with limit=5")


class TestGetSingleCall:
    """Tests for GET /api/calls/{call_id}"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if resp.status_code != 200:
            pytest.skip("User B not available")
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def existing_call_id(self, admin_token):
        """Get an existing call ID from admin user's calls"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls?limit=1", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            return resp.json()[0]["id"]
        pytest.skip("No existing calls found for testing")
    
    def test_get_call_requires_auth(self, existing_call_id):
        """GET /api/calls/{call_id} should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}")
        assert resp.status_code in [401, 403]
    
    def test_get_call_authenticated(self, admin_token, existing_call_id):
        """GET /api/calls/{call_id} should return call details"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}", headers=headers)
        assert resp.status_code == 200
        
        call = resp.json()
        assert call["id"] == existing_call_id
        assert "user_id" in call
        assert "lead_id" in call
        assert "campaign_id" in call
        assert "status" in call
        print(f"Retrieved call {existing_call_id} with status {call['status']}")
    
    def test_get_call_not_found(self, admin_token):
        """GET /api/calls/{non_existent_id} should return 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = str(uuid.uuid4())
        resp = requests.get(f"{BASE_URL}/api/calls/{fake_id}", headers=headers)
        assert resp.status_code == 404
    
    def test_get_call_user_isolation(self, user_b_token, existing_call_id):
        """User B should not be able to access admin's calls"""
        headers = {"Authorization": f"Bearer {user_b_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}", headers=headers)
        # Should return 404 (not found for this user) - user isolation
        assert resp.status_code == 404, f"Expected 404 for user isolation, got {resp.status_code}"
        print("User isolation verified - User B cannot access admin's call")


class TestAnalytics:
    """Tests for GET /api/analytics"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200
        return resp.json().get("session_token")
    
    def test_analytics_requires_auth(self):
        """GET /api/analytics should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/analytics")
        assert resp.status_code in [401, 403]
    
    def test_analytics_default_range(self, admin_token):
        """GET /api/analytics should return 7d analytics by default"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/analytics", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        # Verify analytics structure
        assert "total_calls" in data
        assert "answered_calls" in data
        assert "answer_rate" in data
        assert "qualified_leads" in data
        assert "qualification_rate" in data
        assert "bookings" in data
        assert "booking_rate" in data
        assert "avg_call_duration" in data
        assert "calls_by_day" in data
        assert "calls_by_outcome" in data
        
        print(f"Analytics: total_calls={data['total_calls']}, answer_rate={data['answer_rate']}%")
    
    def test_analytics_7d_range(self, admin_token):
        """GET /api/analytics?range=7d should return 7-day analytics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/analytics?range=7d", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        assert "calls_by_day" in data
        assert len(data["calls_by_day"]) == 7  # 7 days
    
    def test_analytics_30d_range(self, admin_token):
        """GET /api/analytics?range=30d should return 30-day analytics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/analytics?range=30d", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        assert isinstance(data["total_calls"], int)
    
    def test_analytics_90d_range(self, admin_token):
        """GET /api/analytics?range=90d should return 90-day analytics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/analytics?range=90d", headers=headers)
        assert resp.status_code == 200
    
    def test_analytics_all_range(self, admin_token):
        """GET /api/analytics?range=all should return all-time analytics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/analytics?range=all", headers=headers)
        assert resp.status_code == 200
    
    def test_analytics_invalid_range(self, admin_token):
        """GET /api/analytics?range=invalid should return 422"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/analytics?range=invalid", headers=headers)
        assert resp.status_code == 422  # Validation error


class TestAMDStatus:
    """Tests for GET /api/calls/{call_id}/amd-status"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def existing_call_id(self, admin_token):
        """Get an existing call ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls?limit=1", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            return resp.json()[0]["id"]
        pytest.skip("No existing calls found")
    
    def test_amd_status_requires_auth(self, existing_call_id):
        """GET /api/calls/{call_id}/amd-status should require auth"""
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}/amd-status")
        assert resp.status_code in [401, 403]
    
    def test_amd_status_authenticated(self, admin_token, existing_call_id):
        """GET /api/calls/{call_id}/amd-status should return AMD info"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}/amd-status", headers=headers)
        assert resp.status_code == 200
        
        data = resp.json()
        assert "call_id" in data
        assert data["call_id"] == existing_call_id
        assert "answered_by" in data
        assert "voicemail_dropped" in data
        assert "amd_status" in data
        assert "amd_duration_ms" in data
        
        print(f"AMD status: answered_by={data['answered_by']}, voicemail_dropped={data['voicemail_dropped']}")
    
    def test_amd_status_not_found(self, admin_token):
        """GET /api/calls/{non_existent}/amd-status should return 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = str(uuid.uuid4())
        resp = requests.get(f"{BASE_URL}/api/calls/{fake_id}/amd-status", headers=headers)
        assert resp.status_code == 404


class TestRecording:
    """Tests for GET /api/calls/{call_id}/recording - Requires Starter tier"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Admin has unlimited tier - should have access"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def existing_call_id(self, admin_token):
        """Get an existing call ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls?limit=1", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            return resp.json()[0]["id"]
        pytest.skip("No existing calls found")
    
    def test_recording_requires_auth(self, existing_call_id):
        """GET /api/calls/{call_id}/recording should require auth"""
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}/recording")
        assert resp.status_code in [401, 403]
    
    def test_recording_with_unlimited_tier(self, admin_token, existing_call_id):
        """Admin (unlimited tier) should have access to recording endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}/recording", headers=headers)
        
        # Should be 200 (with recording) or 404 (no recording available)
        # Should NOT be 403 (tier restriction) for unlimited user
        assert resp.status_code in [200, 404], f"Expected 200/404, got {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "call_id" in data
            assert "recording_url" in data
            print(f"Recording available: {data.get('recording_url', 'N/A')}")
        else:
            print("No recording available for this call (404)")
    
    def test_recording_not_found(self, admin_token):
        """GET /api/calls/{non_existent}/recording should return 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = str(uuid.uuid4())
        resp = requests.get(f"{BASE_URL}/api/calls/{fake_id}/recording", headers=headers)
        assert resp.status_code == 404


class TestTranscript:
    """Tests for GET /api/calls/{call_id}/transcript - Requires Professional tier"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Admin has unlimited tier - should have access"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def existing_call_id(self, admin_token):
        """Get an existing call ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls?limit=1", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            return resp.json()[0]["id"]
        pytest.skip("No existing calls found")
    
    def test_transcript_requires_auth(self, existing_call_id):
        """GET /api/calls/{call_id}/transcript should require auth"""
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}/transcript")
        assert resp.status_code in [401, 403]
    
    def test_transcript_with_unlimited_tier(self, admin_token, existing_call_id):
        """Admin (unlimited tier) should have access to transcript endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{existing_call_id}/transcript", headers=headers)
        
        # Should be 200 (with transcript) or 404 (no transcript available)
        # Should NOT be 403 (tier restriction) for unlimited user
        assert resp.status_code in [200, 404], f"Expected 200/404, got {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "call_id" in data
            # Could have full_transcript or status=processing
            if data.get("status") == "processing":
                print("Transcript is being processed")
            else:
                assert "full_transcript" in data or "status" in data
                print(f"Transcript status: {data.get('status', 'available')}")
        else:
            print("No transcript available for this call (404)")
    
    def test_transcript_not_found(self, admin_token):
        """GET /api/calls/{non_existent}/transcript should return 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = str(uuid.uuid4())
        resp = requests.get(f"{BASE_URL}/api/calls/{fake_id}/transcript", headers=headers)
        assert resp.status_code == 404


class TestUserIsolation:
    """Tests for user isolation - users can only access their own calls"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert resp.status_code == 200
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if resp.status_code != 200:
            pytest.skip("User B not available")
        return resp.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def admin_call_id(self, admin_token):
        """Get admin's call ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls?limit=1", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            return resp.json()[0]["id"]
        pytest.skip("No admin calls found")
    
    def test_user_b_cannot_access_admin_call(self, user_b_token, admin_call_id):
        """User B should not be able to access admin's call"""
        headers = {"Authorization": f"Bearer {user_b_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{admin_call_id}", headers=headers)
        assert resp.status_code == 404, "User isolation failed - User B accessed admin's call"
    
    def test_user_b_cannot_access_admin_amd_status(self, user_b_token, admin_call_id):
        """User B should not be able to access admin's call AMD status"""
        headers = {"Authorization": f"Bearer {user_b_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{admin_call_id}/amd-status", headers=headers)
        assert resp.status_code == 404, "User isolation failed - User B accessed admin's AMD status"
    
    def test_user_b_cannot_access_admin_recording(self, user_b_token, admin_call_id):
        """User B should not be able to access admin's call recording"""
        headers = {"Authorization": f"Bearer {user_b_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{admin_call_id}/recording", headers=headers)
        # Could be 404 (not found) or 403 (tier restriction) - both are acceptable
        assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"
    
    def test_user_b_cannot_access_admin_transcript(self, user_b_token, admin_call_id):
        """User B should not be able to access admin's call transcript"""
        headers = {"Authorization": f"Bearer {user_b_token}"}
        resp = requests.get(f"{BASE_URL}/api/calls/{admin_call_id}/transcript", headers=headers)
        # Could be 404 (not found) or 403 (tier restriction) - both are acceptable
        assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"
    
    def test_users_see_only_their_own_calls(self, admin_token, user_b_token):
        """Each user should only see their own calls in the list"""
        # Get admin's calls
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        admin_resp = requests.get(f"{BASE_URL}/api/calls", headers=admin_headers)
        assert admin_resp.status_code == 200
        admin_calls = admin_resp.json()
        
        # Get User B's calls
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
        user_b_resp = requests.get(f"{BASE_URL}/api/calls", headers=user_b_headers)
        assert user_b_resp.status_code == 200
        user_b_calls = user_b_resp.json()
        
        # Verify no overlap in call IDs
        admin_call_ids = {c["id"] for c in admin_calls}
        user_b_call_ids = {c["id"] for c in user_b_calls}
        
        overlap = admin_call_ids.intersection(user_b_call_ids)
        assert len(overlap) == 0, f"Found overlapping calls: {overlap}"
        
        print(f"Admin has {len(admin_calls)} calls, User B has {len(user_b_calls)} calls - no overlap")


class TestTierRestrictions:
    """Tests for tier-based access restrictions"""
    
    @pytest.fixture(scope="class")
    def free_user_token(self):
        """Get free tier user token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "freetrial@test.com",
            "password": "Test123!"
        })
        if resp.status_code != 200:
            pytest.skip("Free trial user not available")
        return resp.json().get("session_token")
    
    def test_free_user_recording_access(self, free_user_token):
        """Free tier user should get 403 for recording endpoint"""
        headers = {"Authorization": f"Bearer {free_user_token}"}
        
        # First get a call ID (if any)
        calls_resp = requests.get(f"{BASE_URL}/api/calls?limit=1", headers=headers)
        if calls_resp.status_code != 200 or len(calls_resp.json()) == 0:
            pytest.skip("No calls available for free user")
        
        call_id = calls_resp.json()[0]["id"]
        
        # Try to access recording
        resp = requests.get(f"{BASE_URL}/api/calls/{call_id}/recording", headers=headers)
        # Should be 403 (tier restriction) or 404 (no recording)
        assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"
        
        if resp.status_code == 403:
            assert "Starter" in resp.json().get("detail", "")
            print("Free user correctly denied recording access (403)")
    
    def test_free_user_transcript_access(self, free_user_token):
        """Free tier user should get 403 for transcript endpoint"""
        headers = {"Authorization": f"Bearer {free_user_token}"}
        
        # First get a call ID (if any)
        calls_resp = requests.get(f"{BASE_URL}/api/calls?limit=1", headers=headers)
        if calls_resp.status_code != 200 or len(calls_resp.json()) == 0:
            pytest.skip("No calls available for free user")
        
        call_id = calls_resp.json()[0]["id"]
        
        # Try to access transcript
        resp = requests.get(f"{BASE_URL}/api/calls/{call_id}/transcript", headers=headers)
        # Should be 403 (tier restriction) or 404 (no transcript)
        assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"
        
        if resp.status_code == 403:
            assert "Professional" in resp.json().get("detail", "")
            print("Free user correctly denied transcript access (403)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
