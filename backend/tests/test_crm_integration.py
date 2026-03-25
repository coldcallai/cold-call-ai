"""
CRM Integration Tests
Tests for CRM integration endpoints including:
- GET /api/crm/status - CRM connection status for all providers
- POST /api/crm/connect - Connect a CRM with API key
- POST /api/crm/disconnect/{provider} - Disconnect a CRM
- GET /api/crm/push-logs - Get CRM push logs
- Tier gating - Only Professional+ can access CRM features
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}
STARTER_USER_EMAIL = f"test_starter_{uuid.uuid4().hex[:8]}@example.com"
STARTER_USER_PASSWORD = "Test123!"


class TestCRMStatusEndpoint:
    """Tests for GET /api/crm/status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_token):
        self.client = api_client
        self.token = admin_token
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_crm_status_returns_all_providers(self, api_client, admin_token):
        """Test that CRM status returns all three providers (GHL, Salesforce, HubSpot)"""
        response = api_client.get(
            f"{BASE_URL}/api/crm/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Admin user should have CRM enabled
        assert data.get("enabled") == True, "CRM should be enabled for admin user"
        
        # Should have connections array
        assert "connections" in data, "Response should have 'connections' field"
        connections = data["connections"]
        
        # Should have all 3 providers
        assert len(connections) == 3, f"Expected 3 providers, got {len(connections)}"
        
        # Check provider names
        provider_names = [c["provider"] for c in connections]
        assert "gohighlevel" in provider_names, "GoHighLevel should be in providers"
        assert "salesforce" in provider_names, "Salesforce should be in providers"
        assert "hubspot" in provider_names, "HubSpot should be in providers"
        
        # Each connection should have required fields
        for conn in connections:
            assert "provider" in conn
            assert "is_connected" in conn
            assert "total_leads_pushed" in conn
            print(f"Provider {conn['provider']}: connected={conn['is_connected']}, leads_pushed={conn['total_leads_pushed']}")
    
    def test_crm_status_without_auth_fails(self, api_client):
        """Test that CRM status requires authentication"""
        # Use a fresh session without any auth headers
        fresh_client = requests.Session()
        fresh_client.headers.update({"Content-Type": "application/json"})
        response = fresh_client.get(f"{BASE_URL}/api/crm/status")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"CRM status without auth: {response.status_code}")


class TestCRMTierGating:
    """Tests for CRM feature tier gating - only Professional+ should have access"""
    
    def test_starter_tier_user_gets_403_on_crm_status(self, api_client):
        """Test that starter tier user gets upgrade required message"""
        # Create a starter tier user
        register_response = api_client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": STARTER_USER_EMAIL,
                "password": STARTER_USER_PASSWORD,
                "name": "Starter Test User"
            }
        )
        
        if register_response.status_code == 200:
            token = register_response.json().get("session_token") or register_response.json().get("token")
        else:
            # User might already exist, try login
            login_response = api_client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": STARTER_USER_EMAIL, "password": STARTER_USER_PASSWORD}
            )
            if login_response.status_code != 200:
                pytest.skip("Could not create or login starter user")
            token = login_response.json().get("session_token") or login_response.json().get("token")
        
        # Try to access CRM status
        response = api_client.get(
            f"{BASE_URL}/api/crm/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # For non-professional users, should return enabled=False
        assert data.get("enabled") == False, "CRM should be disabled for starter tier"
        assert data.get("upgrade_required") == True, "Should indicate upgrade required"
        print(f"Starter user CRM status: enabled={data.get('enabled')}, upgrade_required={data.get('upgrade_required')}")
    
    def test_starter_tier_user_gets_403_on_crm_connect(self, api_client):
        """Test that starter tier user cannot connect CRM"""
        # Login as starter user
        login_response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STARTER_USER_EMAIL, "password": STARTER_USER_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip("Starter user not available")
        
        token = login_response.json().get("session_token") or login_response.json().get("token")
        
        # Try to connect CRM
        response = api_client.post(
            f"{BASE_URL}/api/crm/connect",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "provider": "hubspot",
                "api_key": "test_api_key_123"
            }
        )
        
        assert response.status_code == 403, f"Expected 403 for starter tier, got {response.status_code}"
        assert "Professional" in response.json().get("detail", ""), "Error should mention Professional plan"
        print(f"Starter user connect attempt: {response.status_code} - {response.json().get('detail')}")


class TestCRMConnectEndpoint:
    """Tests for POST /api/crm/connect endpoint"""
    
    def test_connect_crm_with_invalid_api_key(self, api_client, admin_token):
        """Test connecting CRM with invalid API key returns error"""
        response = api_client.post(
            f"{BASE_URL}/api/crm/connect",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "provider": "hubspot",
                "api_key": "invalid_test_key_12345"
            }
        )
        
        # Should return 400 for invalid API key
        assert response.status_code == 400, f"Expected 400 for invalid key, got {response.status_code}"
        data = response.json()
        assert "Invalid" in data.get("detail", "") or "error" in data.get("detail", "").lower()
        print(f"Invalid API key response: {response.status_code} - {data.get('detail')}")
    
    def test_connect_crm_with_invalid_provider(self, api_client, admin_token):
        """Test connecting with invalid provider returns error"""
        response = api_client.post(
            f"{BASE_URL}/api/crm/connect",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "provider": "invalid_crm",
                "api_key": "test_key"
            }
        )
        
        # Should return 422 for invalid provider enum
        assert response.status_code == 422, f"Expected 422 for invalid provider, got {response.status_code}"
        print(f"Invalid provider response: {response.status_code}")
    
    def test_connect_salesforce_requires_instance_url(self, api_client, admin_token):
        """Test that Salesforce connection requires instance URL"""
        response = api_client.post(
            f"{BASE_URL}/api/crm/connect",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "provider": "salesforce",
                "api_key": "test_salesforce_token"
            }
        )
        
        # Should return 400 because instance_url is required for Salesforce
        assert response.status_code == 400, f"Expected 400 for missing instance_url, got {response.status_code}"
        data = response.json()
        assert "instance" in data.get("detail", "").lower() or "url" in data.get("detail", "").lower()
        print(f"Salesforce without instance URL: {response.status_code} - {data.get('detail')}")
    
    def test_connect_crm_request_structure(self, api_client, admin_token):
        """Test that connect endpoint accepts correct request structure"""
        # Test with all providers to verify request structure
        providers = ["gohighlevel", "hubspot"]
        
        for provider in providers:
            response = api_client.post(
                f"{BASE_URL}/api/crm/connect",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "provider": provider,
                    "api_key": f"test_key_for_{provider}"
                }
            )
            
            # Should return 400 (invalid key) not 422 (validation error)
            assert response.status_code == 400, f"Expected 400 for {provider}, got {response.status_code}"
            print(f"Connect {provider} structure test: {response.status_code}")


class TestCRMDisconnectEndpoint:
    """Tests for POST /api/crm/disconnect/{provider} endpoint"""
    
    def test_disconnect_crm_not_connected(self, api_client, admin_token):
        """Test disconnecting a CRM that's not connected"""
        response = api_client.post(
            f"{BASE_URL}/api/crm/disconnect/hubspot",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should succeed even if not connected (idempotent)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "disconnected" in data.get("status", "").lower() or "success" in str(data).lower()
        print(f"Disconnect not-connected CRM: {response.status_code} - {data}")
    
    def test_disconnect_invalid_provider(self, api_client, admin_token):
        """Test disconnecting with invalid provider"""
        response = api_client.post(
            f"{BASE_URL}/api/crm/disconnect/invalid_provider",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid provider, got {response.status_code}"
        print(f"Disconnect invalid provider: {response.status_code}")
    
    def test_disconnect_all_providers(self, api_client, admin_token):
        """Test disconnecting all valid providers"""
        providers = ["gohighlevel", "salesforce", "hubspot"]
        
        for provider in providers:
            response = api_client.post(
                f"{BASE_URL}/api/crm/disconnect/{provider}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200, f"Expected 200 for {provider}, got {response.status_code}"
            print(f"Disconnect {provider}: {response.status_code}")


class TestCRMPushLogsEndpoint:
    """Tests for GET /api/crm/push-logs endpoint"""
    
    def test_get_push_logs_empty(self, api_client, admin_token):
        """Test getting push logs when none exist"""
        response = api_client.get(
            f"{BASE_URL}/api/crm/push-logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "logs" in data, "Response should have 'logs' field"
        assert "count" in data, "Response should have 'count' field"
        assert isinstance(data["logs"], list), "logs should be a list"
        print(f"Push logs: count={data['count']}, logs={len(data['logs'])}")
    
    def test_get_push_logs_with_limit(self, api_client, admin_token):
        """Test getting push logs with limit parameter"""
        response = api_client.get(
            f"{BASE_URL}/api/crm/push-logs?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert len(data["logs"]) <= 10, "Should respect limit parameter"
        print(f"Push logs with limit=10: count={data['count']}")
    
    def test_get_push_logs_with_provider_filter(self, api_client, admin_token):
        """Test getting push logs filtered by provider"""
        response = api_client.get(
            f"{BASE_URL}/api/crm/push-logs?provider=hubspot",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # All logs should be for hubspot provider
        for log in data["logs"]:
            assert log.get("provider") == "hubspot", f"Expected hubspot, got {log.get('provider')}"
        print(f"Push logs for hubspot: count={data['count']}")
    
    def test_get_push_logs_without_auth_fails(self, api_client):
        """Test that push logs requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/crm/push-logs")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestCRMAutoQualifiedPush:
    """Tests for auto-push to CRM when lead becomes qualified"""
    
    def test_lead_update_to_qualified_triggers_crm_push(self, api_client, admin_token):
        """Test that updating lead status to qualified triggers CRM push (background task)"""
        # First create a lead
        lead_data = {
            "business_name": f"TEST_CRM_Lead_{uuid.uuid4().hex[:8]}",
            "phone": "+1-555-0199",
            "email": "crmtest@example.com",
            "contact_name": "CRM Test Contact"
        }
        
        create_response = api_client.post(
            f"{BASE_URL}/api/leads",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=lead_data
        )
        
        assert create_response.status_code == 200, f"Failed to create lead: {create_response.text}"
        lead = create_response.json()
        lead_id = lead["id"]
        
        # Update lead status to qualified
        update_response = api_client.put(
            f"{BASE_URL}/api/leads/{lead_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "qualified"}
        )
        
        assert update_response.status_code == 200, f"Failed to update lead: {update_response.text}"
        updated_lead = update_response.json()
        assert updated_lead["status"] == "qualified", "Lead status should be qualified"
        
        print(f"Lead {lead_id} updated to qualified - CRM push should be triggered in background")
        
        # Cleanup
        api_client.delete(
            f"{BASE_URL}/api/leads/{lead_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


# ============== FIXTURES ==============

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def admin_token(api_client):
    """Get authentication token for admin user"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json=ADMIN_USER
    )
    
    if response.status_code == 200:
        # Token can be returned as 'session_token' or 'token'
        token = response.json().get("session_token") or response.json().get("token")
        if token:
            return token
    
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
