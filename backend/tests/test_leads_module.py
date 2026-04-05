"""
Test Leads Module (Phase 3 Strangler Fig)
Tests all lead-related API endpoints from /app/backend/routes/leads.py
Feature flag: USE_NEW_LEADS_ROUTES=true

Endpoints tested:
- GET /api/leads - List leads for authenticated user
- POST /api/leads - Create a new lead
- GET /api/leads/{lead_id} - Get specific lead by ID
- PUT /api/leads/{lead_id} - Update a lead
- DELETE /api/leads/{lead_id} - Delete a lead
- GET /api/leads/phone-stats - Get phone type statistics
- POST /api/leads/preview-examples - Preview leads without credits
- GET /api/leads/export-csv - Export leads to CSV
"""
import pytest
import requests
import os
import uuid

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}
USER_B = {"email": "test_user_b@example.com", "password": "Test456!"}


class TestLeadsModuleSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated session for admin user"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        assert token, "No token returned from login"
        
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def user_b_session(self):
        """Get authenticated session for User B (for multi-tenant tests)"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if response.status_code != 200:
            pytest.skip(f"User B login failed: {response.text}")
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_base_url_configured(self):
        """Verify BASE_URL is configured"""
        assert BASE_URL, "REACT_APP_BACKEND_URL not set"
        print(f"Testing against: {BASE_URL}")
    
    def test_admin_login(self, admin_session):
        """Verify admin user can authenticate"""
        response = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == ADMIN_USER["email"]
        print(f"Admin user authenticated: {data.get('email')}")


class TestLeadsCRUD:
    """Test basic CRUD operations for leads"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated session for admin user"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def created_lead_id(self, admin_session):
        """Create a test lead and return its ID for subsequent tests"""
        lead_data = {
            "business_name": f"TEST_Lead_{uuid.uuid4().hex[:8]}",
            "phone": "+15551234567",
            "contact_name": "Test Contact",
            "email": "testlead@example.com",
            "industry": "Technology",
            "company_size": "10-50",
            "source": "manual",
            "intent_signals": ["test_signal"]
        }
        
        response = admin_session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 200, f"Failed to create lead: {response.text}"
        
        data = response.json()
        lead_id = data.get("id")
        assert lead_id, "No lead ID returned"
        
        yield lead_id
        
        # Cleanup: Delete the test lead
        admin_session.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_create_lead(self, admin_session):
        """Test POST /api/leads - Create a new lead"""
        lead_data = {
            "business_name": f"TEST_CreateLead_{uuid.uuid4().hex[:8]}",
            "phone": "+15559876543",
            "contact_name": "Create Test",
            "email": "create@test.com",
            "industry": "Finance",
            "source": "manual"
        }
        
        response = admin_session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 200, f"Create lead failed: {response.text}"
        
        data = response.json()
        assert data.get("id"), "No ID returned"
        assert data.get("business_name") == lead_data["business_name"]
        assert data.get("phone") == lead_data["phone"]
        assert data.get("contact_name") == lead_data["contact_name"]
        assert data.get("status") == "new"  # Default status
        assert data.get("user_id"), "user_id should be set"
        
        print(f"Created lead: {data.get('id')}")
        
        # Cleanup
        admin_session.delete(f"{BASE_URL}/api/leads/{data.get('id')}")
    
    def test_create_lead_minimal(self, admin_session):
        """Test creating lead with minimal required fields"""
        lead_data = {
            "business_name": f"TEST_MinimalLead_{uuid.uuid4().hex[:8]}",
            "phone": "+15551112222"
        }
        
        response = admin_session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 200, f"Create minimal lead failed: {response.text}"
        
        data = response.json()
        assert data.get("id")
        assert data.get("business_name") == lead_data["business_name"]
        assert data.get("source") == "manual"  # Default source
        
        # Cleanup
        admin_session.delete(f"{BASE_URL}/api/leads/{data.get('id')}")
    
    def test_create_lead_missing_required_fields(self, admin_session):
        """Test creating lead without required fields returns error"""
        # Missing business_name
        response = admin_session.post(f"{BASE_URL}/api/leads", json={"phone": "+15551234567"})
        assert response.status_code == 422, "Should fail without business_name"
        
        # Missing phone
        response = admin_session.post(f"{BASE_URL}/api/leads", json={"business_name": "Test"})
        assert response.status_code == 422, "Should fail without phone"
    
    def test_get_leads_list(self, admin_session, created_lead_id):
        """Test GET /api/leads - List leads for authenticated user"""
        response = admin_session.get(f"{BASE_URL}/api/leads")
        assert response.status_code == 200, f"Get leads failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Find our created lead
        lead_ids = [lead.get("id") for lead in data]
        assert created_lead_id in lead_ids, "Created lead should be in list"
        
        print(f"Found {len(data)} leads")
    
    def test_get_leads_with_status_filter(self, admin_session):
        """Test GET /api/leads with status filter"""
        response = admin_session.get(f"{BASE_URL}/api/leads?status=new")
        assert response.status_code == 200
        
        data = response.json()
        for lead in data:
            assert lead.get("status") == "new", "All leads should have status 'new'"
    
    def test_get_leads_with_pagination(self, admin_session):
        """Test GET /api/leads with limit and skip"""
        response = admin_session.get(f"{BASE_URL}/api/leads?limit=5&skip=0")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 5, "Should return at most 5 leads"
    
    def test_get_lead_by_id(self, admin_session, created_lead_id):
        """Test GET /api/leads/{lead_id} - Get specific lead"""
        response = admin_session.get(f"{BASE_URL}/api/leads/{created_lead_id}")
        assert response.status_code == 200, f"Get lead by ID failed: {response.text}"
        
        data = response.json()
        assert data.get("id") == created_lead_id
        assert data.get("business_name")
        assert data.get("phone")
        
        print(f"Retrieved lead: {data.get('business_name')}")
    
    def test_get_lead_not_found(self, admin_session):
        """Test GET /api/leads/{lead_id} with non-existent ID"""
        fake_id = str(uuid.uuid4())
        response = admin_session.get(f"{BASE_URL}/api/leads/{fake_id}")
        assert response.status_code == 404, "Should return 404 for non-existent lead"
    
    def test_update_lead(self, admin_session, created_lead_id):
        """Test PUT /api/leads/{lead_id} - Update a lead"""
        updates = {
            "contact_name": "Updated Contact Name",
            "status": "contacted",
            "notes": ["First contact made"]
        }
        
        response = admin_session.put(f"{BASE_URL}/api/leads/{created_lead_id}", json=updates)
        assert response.status_code == 200, f"Update lead failed: {response.text}"
        
        data = response.json()
        assert data.get("contact_name") == updates["contact_name"]
        assert data.get("status") == updates["status"]
        
        # Verify persistence with GET
        get_response = admin_session.get(f"{BASE_URL}/api/leads/{created_lead_id}")
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        assert get_data.get("contact_name") == updates["contact_name"]
        assert get_data.get("status") == updates["status"]
        
        print(f"Updated lead status to: {data.get('status')}")
    
    def test_update_lead_not_found(self, admin_session):
        """Test PUT /api/leads/{lead_id} with non-existent ID"""
        fake_id = str(uuid.uuid4())
        response = admin_session.put(f"{BASE_URL}/api/leads/{fake_id}", json={"status": "contacted"})
        assert response.status_code == 404, "Should return 404 for non-existent lead"
    
    def test_delete_lead(self, admin_session):
        """Test DELETE /api/leads/{lead_id} - Delete a lead"""
        # First create a lead to delete
        lead_data = {
            "business_name": f"TEST_DeleteLead_{uuid.uuid4().hex[:8]}",
            "phone": "+15553334444"
        }
        
        create_response = admin_session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert create_response.status_code == 200
        lead_id = create_response.json().get("id")
        
        # Delete the lead
        delete_response = admin_session.delete(f"{BASE_URL}/api/leads/{lead_id}")
        assert delete_response.status_code == 200, f"Delete lead failed: {delete_response.text}"
        
        data = delete_response.json()
        assert data.get("message") == "Lead deleted"
        
        # Verify deletion with GET
        get_response = admin_session.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert get_response.status_code == 404, "Deleted lead should not be found"
        
        print(f"Deleted lead: {lead_id}")
    
    def test_delete_lead_not_found(self, admin_session):
        """Test DELETE /api/leads/{lead_id} with non-existent ID"""
        fake_id = str(uuid.uuid4())
        response = admin_session.delete(f"{BASE_URL}/api/leads/{fake_id}")
        assert response.status_code == 404, "Should return 404 for non-existent lead"


class TestLeadsAuthentication:
    """Test authentication requirements for leads endpoints"""
    
    def test_get_leads_without_auth(self):
        """Test GET /api/leads without authentication"""
        response = requests.get(f"{BASE_URL}/api/leads")
        assert response.status_code == 401, "Should require authentication"
    
    def test_create_lead_without_auth(self):
        """Test POST /api/leads without authentication"""
        lead_data = {"business_name": "Test", "phone": "+15551234567"}
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 401, "Should require authentication"
    
    def test_get_lead_by_id_without_auth(self):
        """Test GET /api/leads/{id} without authentication"""
        response = requests.get(f"{BASE_URL}/api/leads/{uuid.uuid4()}")
        assert response.status_code == 401, "Should require authentication"
    
    def test_update_lead_without_auth(self):
        """Test PUT /api/leads/{id} without authentication"""
        response = requests.put(f"{BASE_URL}/api/leads/{uuid.uuid4()}", json={"status": "contacted"})
        assert response.status_code == 401, "Should require authentication"
    
    def test_delete_lead_without_auth(self):
        """Test DELETE /api/leads/{id} without authentication"""
        response = requests.delete(f"{BASE_URL}/api/leads/{uuid.uuid4()}")
        assert response.status_code == 401, "Should require authentication"
    
    def test_phone_stats_without_auth(self):
        """Test GET /api/leads/phone-stats without authentication"""
        response = requests.get(f"{BASE_URL}/api/leads/phone-stats")
        assert response.status_code == 401, "Should require authentication"


class TestLeadsUserIsolation:
    """Test that users can only access their own leads (multi-tenant isolation)"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated session for admin user"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def user_b_session(self):
        """Get authenticated session for User B"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=USER_B)
        if response.status_code != 200:
            pytest.skip(f"User B login failed - skipping isolation tests")
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_user_cannot_access_other_users_lead(self, admin_session, user_b_session):
        """Test that User B cannot access Admin's lead"""
        # Admin creates a lead
        lead_data = {
            "business_name": f"TEST_AdminLead_{uuid.uuid4().hex[:8]}",
            "phone": "+15557778888"
        }
        
        create_response = admin_session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert create_response.status_code == 200
        admin_lead_id = create_response.json().get("id")
        
        try:
            # User B tries to access Admin's lead
            get_response = user_b_session.get(f"{BASE_URL}/api/leads/{admin_lead_id}")
            assert get_response.status_code == 404, "User B should not see Admin's lead"
            
            # User B tries to update Admin's lead
            update_response = user_b_session.put(
                f"{BASE_URL}/api/leads/{admin_lead_id}", 
                json={"status": "contacted"}
            )
            assert update_response.status_code == 404, "User B should not update Admin's lead"
            
            # User B tries to delete Admin's lead
            delete_response = user_b_session.delete(f"{BASE_URL}/api/leads/{admin_lead_id}")
            assert delete_response.status_code == 404, "User B should not delete Admin's lead"
            
            print("User isolation verified - User B cannot access Admin's leads")
            
        finally:
            # Cleanup: Admin deletes the lead
            admin_session.delete(f"{BASE_URL}/api/leads/{admin_lead_id}")
    
    def test_users_see_only_their_leads(self, admin_session, user_b_session):
        """Test that each user only sees their own leads in list"""
        # Admin creates a lead
        admin_lead_data = {
            "business_name": f"TEST_AdminOnly_{uuid.uuid4().hex[:8]}",
            "phone": "+15551111111"
        }
        admin_create = admin_session.post(f"{BASE_URL}/api/leads", json=admin_lead_data)
        assert admin_create.status_code == 200
        admin_lead_id = admin_create.json().get("id")
        
        # User B creates a lead
        user_b_lead_data = {
            "business_name": f"TEST_UserBOnly_{uuid.uuid4().hex[:8]}",
            "phone": "+15552222222"
        }
        user_b_create = user_b_session.post(f"{BASE_URL}/api/leads", json=user_b_lead_data)
        assert user_b_create.status_code == 200
        user_b_lead_id = user_b_create.json().get("id")
        
        try:
            # Admin's list should contain admin_lead_id but not user_b_lead_id
            admin_list = admin_session.get(f"{BASE_URL}/api/leads").json()
            admin_lead_ids = [lead.get("id") for lead in admin_list]
            assert admin_lead_id in admin_lead_ids, "Admin should see their own lead"
            assert user_b_lead_id not in admin_lead_ids, "Admin should not see User B's lead"
            
            # User B's list should contain user_b_lead_id but not admin_lead_id
            user_b_list = user_b_session.get(f"{BASE_URL}/api/leads").json()
            user_b_lead_ids = [lead.get("id") for lead in user_b_list]
            assert user_b_lead_id in user_b_lead_ids, "User B should see their own lead"
            assert admin_lead_id not in user_b_lead_ids, "User B should not see Admin's lead"
            
            print("User isolation verified - each user sees only their own leads")
            
        finally:
            # Cleanup
            admin_session.delete(f"{BASE_URL}/api/leads/{admin_lead_id}")
            user_b_session.delete(f"{BASE_URL}/api/leads/{user_b_lead_id}")


class TestLeadsPhoneStats:
    """Test phone statistics endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated session for admin user"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_phone_stats(self, admin_session):
        """Test GET /api/leads/phone-stats"""
        response = admin_session.get(f"{BASE_URL}/api/leads/phone-stats")
        assert response.status_code == 200, f"Get phone stats failed: {response.text}"
        
        data = response.json()
        assert "stats" in data, "Response should contain stats"
        assert "percentages" in data, "Response should contain percentages"
        assert "export_urls" in data, "Response should contain export_urls"
        
        stats = data["stats"]
        assert "mobile" in stats
        assert "landline" in stats
        assert "voip" in stats
        assert "unknown" in stats
        assert "total" in stats
        
        print(f"Phone stats: {stats}")


class TestLeadsPreviewExamples:
    """Test preview examples endpoint (no credits used)"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated session for admin user"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_preview_examples(self, admin_session):
        """Test POST /api/leads/preview-examples"""
        request_data = {
            "search_query": "restaurants",
            "location": "New York",
            "industry": "Food & Beverage"
        }
        
        response = admin_session.post(f"{BASE_URL}/api/leads/preview-examples", json=request_data)
        assert response.status_code == 200, f"Preview examples failed: {response.text}"
        
        data = response.json()
        assert data.get("preview") == True, "Should indicate this is a preview"
        assert "count" in data
        assert "message" in data
        assert "example_leads" in data
        
        print(f"Preview returned {data.get('count')} example leads")
    
    def test_preview_examples_with_keywords(self, admin_session):
        """Test preview examples with custom keywords"""
        request_data = {
            "search_query": "credit card processing",
            "custom_keywords": ["merchant services", "payment processing"]
        }
        
        response = admin_session.post(f"{BASE_URL}/api/leads/preview-examples", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "keywords_used" in data


class TestLeadsExportCSV:
    """Test CSV export endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated session for admin user"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_export_csv(self, admin_session):
        """Test GET /api/leads/export-csv"""
        # First ensure there's at least one lead
        lead_data = {
            "business_name": f"TEST_ExportLead_{uuid.uuid4().hex[:8]}",
            "phone": "+15559998888"
        }
        create_response = admin_session.post(f"{BASE_URL}/api/leads", json=lead_data)
        lead_id = None
        if create_response.status_code == 200:
            lead_id = create_response.json().get("id")
        
        try:
            response = admin_session.get(f"{BASE_URL}/api/leads/export-csv")
            
            # Could be 200 (success) or 403 (tier restriction) or 404 (no leads)
            if response.status_code == 200:
                assert "text/csv" in response.headers.get("Content-Type", "")
                assert "Content-Disposition" in response.headers
                print("CSV export successful")
            elif response.status_code == 403:
                print("CSV export not available on current tier (expected for some tiers)")
            elif response.status_code == 404:
                print("No leads found for export")
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")
                
        finally:
            if lead_id:
                admin_session.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_export_csv_with_filters(self, admin_session):
        """Test CSV export with status and line_type filters"""
        response = admin_session.get(f"{BASE_URL}/api/leads/export-csv?status=new&line_type=mobile")
        
        # Accept 200, 403 (tier), or 404 (no matching leads)
        assert response.status_code in [200, 403, 404], f"Unexpected status: {response.status_code}"


class TestLeadsStatusTransitions:
    """Test lead status transitions"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get authenticated session for admin user"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200
        
        data = response.json()
        token = data.get("session_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_status_transitions(self, admin_session):
        """Test valid status transitions"""
        # Create a lead
        lead_data = {
            "business_name": f"TEST_StatusLead_{uuid.uuid4().hex[:8]}",
            "phone": "+15556667777"
        }
        
        create_response = admin_session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert create_response.status_code == 200
        lead_id = create_response.json().get("id")
        
        try:
            # Test all valid statuses
            valid_statuses = ["new", "contacted", "qualified", "not_qualified", "booked"]
            
            for status in valid_statuses:
                update_response = admin_session.put(
                    f"{BASE_URL}/api/leads/{lead_id}",
                    json={"status": status}
                )
                assert update_response.status_code == 200, f"Failed to set status to {status}"
                assert update_response.json().get("status") == status
                print(f"Status transition to '{status}' successful")
                
        finally:
            admin_session.delete(f"{BASE_URL}/api/leads/{lead_id}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
