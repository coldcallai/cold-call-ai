"""
Test Campaigns Module (Phase 5 Strangler Fig)
Tests all campaign-related endpoints from /app/backend/routes/campaigns.py
Feature flag: USE_NEW_CAMPAIGNS_ROUTES=true

Endpoints tested:
- GET /api/campaigns - List campaigns for authenticated user
- POST /api/campaigns - Create a new campaign
- GET /api/campaigns/{campaign_id} - Get specific campaign by ID
- PUT /api/campaigns/{campaign_id} - Update a campaign
- DELETE /api/campaigns/{campaign_id} - Delete a campaign
- POST /api/campaigns/{campaign_id}/start - Start a campaign
- POST /api/campaigns/{campaign_id}/pause - Pause a campaign
- GET /api/campaigns/{campaign_id}/followup-settings - Get followup settings
- PUT /api/campaigns/{campaign_id}/followup-settings - Update followup settings
"""

import pytest
import requests
import os
import uuid

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}
USER_B = {"email": "test_user_b@example.com", "password": "Test456!"}


class TestCampaignsModuleSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        """Get auth token for user B (multi-tenant testing)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"User B login failed: {response.status_code} - {response.text}")
    
    def test_health_check(self):
        """Verify backend is running"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("Backend health check passed")
    
    def test_admin_login(self, admin_token):
        """Verify admin can login"""
        assert admin_token is not None
        print(f"Admin login successful, token: {admin_token[:20]}...")


class TestCampaignsCRUD:
    """Test Campaign CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        """Get auth token for user B"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"User B login failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Auth headers for admin user"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture
    def user_b_headers(self, user_b_token):
        """Auth headers for user B"""
        return {"Authorization": f"Bearer {user_b_token}"}
    
    # ============== LIST CAMPAIGNS ==============
    
    def test_list_campaigns_requires_auth(self):
        """GET /api/campaigns requires authentication"""
        response = requests.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("List campaigns correctly requires authentication")
    
    def test_list_campaigns_success(self, auth_headers):
        """GET /api/campaigns returns list of user's campaigns"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        assert response.status_code == 200, f"List campaigns failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"List campaigns returned {len(data)} campaigns")
    
    # ============== CREATE CAMPAIGN ==============
    
    def test_create_campaign_requires_auth(self):
        """POST /api/campaigns requires authentication"""
        campaign_data = {
            "name": "TEST_Unauthorized Campaign",
            "ai_script": "Hello, this is a test script."
        }
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Create campaign correctly requires authentication")
    
    def test_create_campaign_success(self, auth_headers):
        """POST /api/campaigns creates a new campaign"""
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_Campaign_{unique_id}",
            "description": "Test campaign for Phase 5 testing",
            "ai_script": "Hello, this is a test AI script for cold calling.",
            "qualification_criteria": {"budget": "10000+", "decision_maker": True},
            "calls_per_day": 50,
            "voicemail_enabled": False,
            "response_wait_seconds": 5,
            "company_name": "Test Company Inc",
            "min_icp_score": 60
        }
        
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=auth_headers)
        assert response.status_code == 200, f"Create campaign failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain campaign id"
        assert data["name"] == campaign_data["name"], "Name should match"
        assert data["ai_script"] == campaign_data["ai_script"], "AI script should match"
        assert data["status"] == "draft", "New campaign should be in draft status"
        assert data["calls_per_day"] == 50, "Calls per day should match"
        assert data["voicemail_enabled"] == False, "Voicemail enabled should match"
        assert data["min_icp_score"] == 60, "Min ICP score should match"
        
        print(f"Created campaign: {data['id']}")
        
        # Cleanup - delete the test campaign
        delete_response = requests.delete(f"{BASE_URL}/api/campaigns/{data['id']}", headers=auth_headers)
        assert delete_response.status_code == 200, f"Cleanup failed: {delete_response.text}"
    
    def test_create_campaign_minimal_fields(self, auth_headers):
        """POST /api/campaigns with minimal required fields"""
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_Minimal_{unique_id}",
            "ai_script": "Minimal test script"
        }
        
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=auth_headers)
        assert response.status_code == 200, f"Create minimal campaign failed: {response.text}"
        
        data = response.json()
        assert data["name"] == campaign_data["name"]
        assert data["status"] == "draft"
        assert data["calls_per_day"] == 100  # Default value
        assert data["voicemail_enabled"] == True  # Default value
        
        print(f"Created minimal campaign: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{data['id']}", headers=auth_headers)
    
    # ============== GET CAMPAIGN BY ID ==============
    
    def test_get_campaign_by_id(self, auth_headers):
        """GET /api/campaigns/{campaign_id} returns specific campaign"""
        # First create a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_GetById_{unique_id}",
            "ai_script": "Test script for get by ID"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=auth_headers)
        assert create_response.status_code == 200
        created = create_response.json()
        campaign_id = created["id"]
        
        # Get the campaign by ID
        response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert response.status_code == 200, f"Get campaign failed: {response.text}"
        
        data = response.json()
        assert data["id"] == campaign_id
        assert data["name"] == campaign_data["name"]
        
        print(f"Successfully retrieved campaign: {campaign_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
    
    def test_get_campaign_not_found(self, auth_headers):
        """GET /api/campaigns/{campaign_id} returns 404 for non-existent campaign"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/campaigns/{fake_id}", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Get non-existent campaign correctly returns 404")
    
    # ============== UPDATE CAMPAIGN ==============
    
    def test_update_campaign(self, auth_headers):
        """PUT /api/campaigns/{campaign_id} updates campaign"""
        # Create a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_Update_{unique_id}",
            "ai_script": "Original script"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=auth_headers)
        assert create_response.status_code == 200
        created = create_response.json()
        campaign_id = created["id"]
        
        # Update the campaign
        updates = {
            "name": f"TEST_Updated_{unique_id}",
            "ai_script": "Updated script content",
            "calls_per_day": 75,
            "description": "Updated description"
        }
        response = requests.put(f"{BASE_URL}/api/campaigns/{campaign_id}", json=updates, headers=auth_headers)
        assert response.status_code == 200, f"Update campaign failed: {response.text}"
        
        data = response.json()
        assert data["name"] == updates["name"], "Name should be updated"
        assert data["ai_script"] == updates["ai_script"], "AI script should be updated"
        assert data["calls_per_day"] == 75, "Calls per day should be updated"
        assert data["description"] == "Updated description", "Description should be updated"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == updates["name"], "Update should persist"
        
        print(f"Successfully updated campaign: {campaign_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
    
    def test_update_campaign_not_found(self, auth_headers):
        """PUT /api/campaigns/{campaign_id} returns 404 for non-existent campaign"""
        fake_id = str(uuid.uuid4())
        updates = {"name": "Updated Name"}
        response = requests.put(f"{BASE_URL}/api/campaigns/{fake_id}", json=updates, headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Update non-existent campaign correctly returns 404")
    
    # ============== DELETE CAMPAIGN ==============
    
    def test_delete_campaign(self, auth_headers):
        """DELETE /api/campaigns/{campaign_id} deletes campaign"""
        # Create a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_Delete_{unique_id}",
            "ai_script": "Script to delete"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=auth_headers)
        assert create_response.status_code == 200
        created = create_response.json()
        campaign_id = created["id"]
        
        # Delete the campaign
        response = requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert response.status_code == 200, f"Delete campaign failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()
        
        # Verify deletion with GET
        get_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert get_response.status_code == 404, "Deleted campaign should return 404"
        
        print(f"Successfully deleted campaign: {campaign_id}")
    
    def test_delete_campaign_not_found(self, auth_headers):
        """DELETE /api/campaigns/{campaign_id} returns 404 for non-existent campaign"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/campaigns/{fake_id}", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Delete non-existent campaign correctly returns 404")


class TestCampaignStatusTransitions:
    """Test campaign start/pause status transitions"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Auth headers for admin user"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture
    def test_campaign(self, auth_headers):
        """Create a test campaign for status tests"""
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_Status_{unique_id}",
            "ai_script": "Status test script"
        }
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=auth_headers)
        assert response.status_code == 200
        campaign = response.json()
        yield campaign
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{campaign['id']}", headers=auth_headers)
    
    def test_start_campaign(self, auth_headers, test_campaign):
        """POST /api/campaigns/{campaign_id}/start changes status to active"""
        campaign_id = test_campaign["id"]
        
        # Verify initial status is draft
        assert test_campaign["status"] == "draft"
        
        # Start the campaign
        response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/start", headers=auth_headers)
        assert response.status_code == 200, f"Start campaign failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "active", "Status should be active"
        assert "message" in data
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["status"] == "active", "Status should persist as active"
        
        print(f"Successfully started campaign: {campaign_id}")
    
    def test_pause_campaign(self, auth_headers, test_campaign):
        """POST /api/campaigns/{campaign_id}/pause changes status to paused"""
        campaign_id = test_campaign["id"]
        
        # First start the campaign
        start_response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/start", headers=auth_headers)
        assert start_response.status_code == 200
        
        # Pause the campaign
        response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/pause", headers=auth_headers)
        assert response.status_code == 200, f"Pause campaign failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "paused", "Status should be paused"
        assert "message" in data
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["status"] == "paused", "Status should persist as paused"
        
        print(f"Successfully paused campaign: {campaign_id}")
    
    def test_start_campaign_not_found(self, auth_headers):
        """POST /api/campaigns/{campaign_id}/start returns 404 for non-existent campaign"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/campaigns/{fake_id}/start", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Start non-existent campaign correctly returns 404")
    
    def test_pause_campaign_not_found(self, auth_headers):
        """POST /api/campaigns/{campaign_id}/pause returns 404 for non-existent campaign"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/campaigns/{fake_id}/pause", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Pause non-existent campaign correctly returns 404")


class TestCampaignFollowupSettings:
    """Test campaign followup settings endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Auth headers for admin user"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture(scope="class")
    def test_campaign(self, auth_headers):
        """Create a test campaign for followup settings tests"""
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_Followup_{unique_id}",
            "ai_script": "Followup test script"
        }
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create test campaign: {response.text}"
        campaign = response.json()
        yield campaign
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{campaign['id']}", headers=auth_headers)
    
    def test_get_followup_settings_default(self, auth_headers, test_campaign):
        """GET /api/campaigns/{campaign_id}/followup-settings returns default settings"""
        campaign_id = test_campaign["id"]
        
        response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/followup-settings", headers=auth_headers)
        assert response.status_code == 200, f"Get followup settings failed: {response.text}"
        
        data = response.json()
        assert "campaign_id" in data
        assert data["campaign_id"] == campaign_id
        assert "settings" in data
        
        settings = data["settings"]
        assert settings is not None, "Followup settings should not be None - should return defaults"
        
        # Check default values
        assert settings["enabled"] == True
        assert settings["no_answer_retry_enabled"] == True
        assert settings["no_answer_retry_count"] == 3
        assert settings["no_answer_retry_delay_hours"] == 24
        assert settings["voicemail_followup_enabled"] == True
        assert settings["voicemail_followup_delay_hours"] == 48
        
        print(f"Got default followup settings for campaign: {campaign_id}")
    
    def test_update_followup_settings(self, auth_headers, test_campaign):
        """PUT /api/campaigns/{campaign_id}/followup-settings updates settings"""
        campaign_id = test_campaign["id"]
        
        # Update followup settings using form data
        form_data = {
            "enabled": "true",
            "no_answer_retry_enabled": "false",
            "no_answer_retry_count": "5",
            "no_answer_retry_delay_hours": "12",
            "voicemail_followup_enabled": "true",
            "voicemail_followup_delay_hours": "72"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/campaigns/{campaign_id}/followup-settings",
            data=form_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Update followup settings failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "settings" in data
        
        settings = data["settings"]
        assert settings["enabled"] == True
        assert settings["no_answer_retry_enabled"] == False
        assert settings["no_answer_retry_count"] == 5
        assert settings["no_answer_retry_delay_hours"] == 12
        assert settings["voicemail_followup_enabled"] == True
        assert settings["voicemail_followup_delay_hours"] == 72
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/followup-settings", headers=auth_headers)
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["settings"]["no_answer_retry_count"] == 5
        assert fetched["settings"]["no_answer_retry_delay_hours"] == 12
        
        print(f"Successfully updated followup settings for campaign: {campaign_id}")
    
    def test_get_followup_settings_not_found(self, auth_headers):
        """GET /api/campaigns/{campaign_id}/followup-settings returns 404 for non-existent campaign"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/campaigns/{fake_id}/followup-settings", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Get followup settings for non-existent campaign correctly returns 404")
    
    def test_update_followup_settings_not_found(self, auth_headers):
        """PUT /api/campaigns/{campaign_id}/followup-settings returns 404 for non-existent campaign"""
        fake_id = str(uuid.uuid4())
        form_data = {"enabled": "true"}
        response = requests.put(f"{BASE_URL}/api/campaigns/{fake_id}/followup-settings", data=form_data, headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Update followup settings for non-existent campaign correctly returns 404")


class TestCampaignMultiTenantIsolation:
    """Test that users can only access their own campaigns"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        """Get auth token for user B"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if response.status_code == 200:
            data = response.json()
            return data.get("session_token")
        pytest.skip(f"User B login failed: {response.status_code}")
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        """Auth headers for admin user"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture
    def user_b_headers(self, user_b_token):
        """Auth headers for user B"""
        return {"Authorization": f"Bearer {user_b_token}"}
    
    def test_user_cannot_access_other_users_campaign(self, admin_headers, user_b_headers):
        """User B cannot access admin's campaign"""
        # Admin creates a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_Isolation_{unique_id}",
            "ai_script": "Admin's private campaign"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=admin_headers)
        assert create_response.status_code == 200
        admin_campaign = create_response.json()
        campaign_id = admin_campaign["id"]
        
        try:
            # User B tries to access admin's campaign
            response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=user_b_headers)
            assert response.status_code == 404, f"User B should not access admin's campaign, got {response.status_code}"
            print("User B correctly cannot access admin's campaign")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=admin_headers)
    
    def test_user_cannot_update_other_users_campaign(self, admin_headers, user_b_headers):
        """User B cannot update admin's campaign"""
        # Admin creates a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_IsolationUpdate_{unique_id}",
            "ai_script": "Admin's campaign for update test"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=admin_headers)
        assert create_response.status_code == 200
        admin_campaign = create_response.json()
        campaign_id = admin_campaign["id"]
        
        try:
            # User B tries to update admin's campaign
            updates = {"name": "Hacked by User B"}
            response = requests.put(f"{BASE_URL}/api/campaigns/{campaign_id}", json=updates, headers=user_b_headers)
            assert response.status_code == 404, f"User B should not update admin's campaign, got {response.status_code}"
            print("User B correctly cannot update admin's campaign")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=admin_headers)
    
    def test_user_cannot_delete_other_users_campaign(self, admin_headers, user_b_headers):
        """User B cannot delete admin's campaign"""
        # Admin creates a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_IsolationDelete_{unique_id}",
            "ai_script": "Admin's campaign for delete test"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=admin_headers)
        assert create_response.status_code == 200
        admin_campaign = create_response.json()
        campaign_id = admin_campaign["id"]
        
        try:
            # User B tries to delete admin's campaign
            response = requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=user_b_headers)
            assert response.status_code == 404, f"User B should not delete admin's campaign, got {response.status_code}"
            
            # Verify campaign still exists for admin
            get_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=admin_headers)
            assert get_response.status_code == 200, "Admin's campaign should still exist"
            print("User B correctly cannot delete admin's campaign")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=admin_headers)
    
    def test_user_cannot_start_other_users_campaign(self, admin_headers, user_b_headers):
        """User B cannot start admin's campaign"""
        # Admin creates a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_IsolationStart_{unique_id}",
            "ai_script": "Admin's campaign for start test"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=admin_headers)
        assert create_response.status_code == 200
        admin_campaign = create_response.json()
        campaign_id = admin_campaign["id"]
        
        try:
            # User B tries to start admin's campaign
            response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/start", headers=user_b_headers)
            assert response.status_code == 404, f"User B should not start admin's campaign, got {response.status_code}"
            print("User B correctly cannot start admin's campaign")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=admin_headers)
    
    def test_user_cannot_access_other_users_followup_settings(self, admin_headers, user_b_headers):
        """User B cannot access admin's campaign followup settings"""
        # Admin creates a campaign
        unique_id = str(uuid.uuid4())[:8]
        campaign_data = {
            "name": f"TEST_IsolationFollowup_{unique_id}",
            "ai_script": "Admin's campaign for followup test"
        }
        create_response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=admin_headers)
        assert create_response.status_code == 200
        admin_campaign = create_response.json()
        campaign_id = admin_campaign["id"]
        
        try:
            # User B tries to get admin's campaign followup settings
            response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/followup-settings", headers=user_b_headers)
            assert response.status_code == 404, f"User B should not access admin's followup settings, got {response.status_code}"
            print("User B correctly cannot access admin's followup settings")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=admin_headers)
    
    def test_users_see_only_their_own_campaigns(self, admin_headers, user_b_headers):
        """Each user only sees their own campaigns in list"""
        # Admin creates a campaign
        unique_id = str(uuid.uuid4())[:8]
        admin_campaign_data = {
            "name": f"TEST_AdminCampaign_{unique_id}",
            "ai_script": "Admin's campaign"
        }
        admin_create = requests.post(f"{BASE_URL}/api/campaigns", json=admin_campaign_data, headers=admin_headers)
        assert admin_create.status_code == 200
        admin_campaign = admin_create.json()
        
        try:
            # Admin lists campaigns - should see admin's campaign
            admin_list = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers)
            assert admin_list.status_code == 200
            admin_campaigns = admin_list.json()
            admin_campaign_ids = [c["id"] for c in admin_campaigns]
            assert admin_campaign["id"] in admin_campaign_ids, "Admin should see their own campaign"
            
            # User B lists campaigns - should NOT see admin's campaign
            user_b_list = requests.get(f"{BASE_URL}/api/campaigns", headers=user_b_headers)
            assert user_b_list.status_code == 200
            user_b_campaigns = user_b_list.json()
            user_b_campaign_ids = [c["id"] for c in user_b_campaigns]
            assert admin_campaign["id"] not in user_b_campaign_ids, "User B should not see admin's campaign"
            
            print("Users correctly see only their own campaigns (isolation verified)")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/campaigns/{admin_campaign['id']}", headers=admin_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
