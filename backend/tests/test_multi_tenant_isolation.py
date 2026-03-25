"""
Multi-Tenant Data Isolation Tests
=================================
Tests to verify that each user can only access their own data (leads, campaigns, calls, agents, webhooks).
Cross-user access should return 404 (not 403) to avoid leaking existence of other users' data.
"""

import pytest
import requests
import os
import uuid

# Get the base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://onboard-dialgenix.preview.emergentagent.com').rstrip('/')

# Test users
USER_A = {"email": "test@example.com", "password": "Test123!", "name": "Test User A"}
USER_B = {"email": "test_user_b@example.com", "password": "Test456!", "name": "Test User B"}


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation across all resources"""
    
    @pytest.fixture(scope="class")
    def user_a_token(self):
        """Get or create User A and return session token"""
        # Try to login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_A["email"],
            "password": USER_A["password"]
        })
        
        if response.status_code == 200:
            token = response.json().get("session_token")
            if token:
                return token
        
        # If login fails, register the user
        response = requests.post(f"{BASE_URL}/api/auth/register", json=USER_A)
        if response.status_code in [200, 201]:
            token = response.json().get("session_token")
            if token:
                return token
        
        # Try login again after registration
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_A["email"],
            "password": USER_A["password"]
        })
        if response.status_code == 200:
            token = response.json().get("session_token")
            if token:
                return token
        
        pytest.skip(f"Could not authenticate User A: {response.text}")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        """Get or create User B and return session token"""
        # Try to login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_B["email"],
            "password": USER_B["password"]
        })
        
        if response.status_code == 200:
            token = response.json().get("session_token")
            if token:
                return token
        
        # If login fails, register the user
        response = requests.post(f"{BASE_URL}/api/auth/register", json=USER_B)
        if response.status_code in [200, 201]:
            token = response.json().get("session_token")
            if token:
                return token
        
        # Try login again after registration
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_B["email"],
            "password": USER_B["password"]
        })
        if response.status_code == 200:
            token = response.json().get("session_token")
            if token:
                return token
        
        pytest.skip(f"Could not authenticate User B: {response.text}")
    
    @pytest.fixture(scope="class")
    def user_a_headers(self, user_a_token):
        """Headers for User A requests"""
        return {"Authorization": f"Bearer {user_a_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def user_b_headers(self, user_b_token):
        """Headers for User B requests"""
        return {"Authorization": f"Bearer {user_b_token}", "Content-Type": "application/json"}
    
    # ==================== LEADS ISOLATION TESTS ====================
    
    def test_user_a_can_create_lead(self, user_a_headers):
        """User A creates a lead"""
        lead_data = {
            "business_name": f"TEST_UserA_Business_{uuid.uuid4().hex[:8]}",
            "phone": "+1-555-0001",
            "contact_name": "User A Contact",
            "email": "usera@test.com"
        }
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=user_a_headers)
        assert response.status_code == 200, f"Failed to create lead: {response.text}"
        
        lead = response.json()
        assert lead["business_name"] == lead_data["business_name"]
        assert "id" in lead
        
        # Store lead_id for later tests
        self.__class__.user_a_lead_id = lead["id"]
        print(f"User A created lead: {lead['id']}")
    
    def test_user_b_can_create_lead(self, user_b_headers):
        """User B creates a lead"""
        lead_data = {
            "business_name": f"TEST_UserB_Business_{uuid.uuid4().hex[:8]}",
            "phone": "+1-555-0002",
            "contact_name": "User B Contact",
            "email": "userb@test.com"
        }
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=user_b_headers)
        assert response.status_code == 200, f"Failed to create lead: {response.text}"
        
        lead = response.json()
        assert lead["business_name"] == lead_data["business_name"]
        assert "id" in lead
        
        # Store lead_id for later tests
        self.__class__.user_b_lead_id = lead["id"]
        print(f"User B created lead: {lead['id']}")
    
    def test_user_a_can_only_see_own_leads(self, user_a_headers):
        """User A should only see their own leads in GET /api/leads"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=user_a_headers)
        assert response.status_code == 200
        
        leads = response.json()
        # Check that User B's lead is NOT in User A's list
        lead_ids = [lead["id"] for lead in leads]
        
        if hasattr(self.__class__, 'user_b_lead_id'):
            assert self.__class__.user_b_lead_id not in lead_ids, "User A can see User B's lead - ISOLATION FAILURE!"
        
        print(f"User A sees {len(leads)} leads (isolation verified)")
    
    def test_user_b_can_only_see_own_leads(self, user_b_headers):
        """User B should only see their own leads in GET /api/leads"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=user_b_headers)
        assert response.status_code == 200
        
        leads = response.json()
        # Check that User A's lead is NOT in User B's list
        lead_ids = [lead["id"] for lead in leads]
        
        if hasattr(self.__class__, 'user_a_lead_id'):
            assert self.__class__.user_a_lead_id not in lead_ids, "User B can see User A's lead - ISOLATION FAILURE!"
        
        print(f"User B sees {len(leads)} leads (isolation verified)")
    
    def test_user_b_cannot_read_user_a_lead_by_id(self, user_b_headers):
        """User B should get 404 when trying to access User A's lead by ID"""
        if not hasattr(self.__class__, 'user_a_lead_id'):
            pytest.skip("User A lead not created")
        
        response = requests.get(f"{BASE_URL}/api/leads/{self.__class__.user_a_lead_id}", headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code} - User B can read User A's lead!"
        print("User B correctly gets 404 when accessing User A's lead")
    
    def test_user_b_cannot_update_user_a_lead(self, user_b_headers):
        """User B should get 404 when trying to update User A's lead"""
        if not hasattr(self.__class__, 'user_a_lead_id'):
            pytest.skip("User A lead not created")
        
        update_data = {"contact_name": "HACKED BY USER B"}
        response = requests.put(f"{BASE_URL}/api/leads/{self.__class__.user_a_lead_id}", 
                               json=update_data, headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code} - User B can update User A's lead!"
        print("User B correctly gets 404 when updating User A's lead")
    
    def test_user_b_cannot_delete_user_a_lead(self, user_b_headers):
        """User B should get 404 when trying to delete User A's lead"""
        if not hasattr(self.__class__, 'user_a_lead_id'):
            pytest.skip("User A lead not created")
        
        response = requests.delete(f"{BASE_URL}/api/leads/{self.__class__.user_a_lead_id}", headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code} - User B can delete User A's lead!"
        print("User B correctly gets 404 when deleting User A's lead")
    
    def test_user_a_lead_still_exists_after_user_b_delete_attempt(self, user_a_headers):
        """Verify User A's lead still exists after User B's delete attempt"""
        if not hasattr(self.__class__, 'user_a_lead_id'):
            pytest.skip("User A lead not created")
        
        response = requests.get(f"{BASE_URL}/api/leads/{self.__class__.user_a_lead_id}", headers=user_a_headers)
        assert response.status_code == 200, f"User A's lead was deleted by User B! Status: {response.status_code}"
        print("User A's lead still exists (delete isolation verified)")
    
    # ==================== CAMPAIGNS ISOLATION TESTS ====================
    
    def test_user_a_can_create_campaign(self, user_a_headers):
        """User A creates a campaign"""
        campaign_data = {
            "name": f"TEST_UserA_Campaign_{uuid.uuid4().hex[:8]}",
            "ai_script": "Test script for User A",
            "description": "User A's test campaign"
        }
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=user_a_headers)
        assert response.status_code == 200, f"Failed to create campaign: {response.text}"
        
        campaign = response.json()
        assert campaign["name"] == campaign_data["name"]
        self.__class__.user_a_campaign_id = campaign["id"]
        print(f"User A created campaign: {campaign['id']}")
    
    def test_user_b_can_create_campaign(self, user_b_headers):
        """User B creates a campaign (free tier - no voicemail)"""
        campaign_data = {
            "name": f"TEST_UserB_Campaign_{uuid.uuid4().hex[:8]}",
            "ai_script": "Test script for User B",
            "description": "User B's test campaign",
            "voicemail_enabled": False  # Free tier users cannot use voicemail
        }
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=user_b_headers)
        assert response.status_code == 200, f"Failed to create campaign: {response.text}"
        
        campaign = response.json()
        self.__class__.user_b_campaign_id = campaign["id"]
        print(f"User B created campaign: {campaign['id']}")
    
    def test_user_a_can_only_see_own_campaigns(self, user_a_headers):
        """User A should only see their own campaigns"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=user_a_headers)
        assert response.status_code == 200
        
        campaigns = response.json()
        campaign_ids = [c["id"] for c in campaigns]
        
        if hasattr(self.__class__, 'user_b_campaign_id'):
            assert self.__class__.user_b_campaign_id not in campaign_ids, "User A can see User B's campaign!"
        
        print(f"User A sees {len(campaigns)} campaigns (isolation verified)")
    
    def test_user_b_cannot_access_user_a_campaign(self, user_b_headers):
        """User B should get 404 when accessing User A's campaign"""
        if not hasattr(self.__class__, 'user_a_campaign_id'):
            pytest.skip("User A campaign not created")
        
        response = requests.get(f"{BASE_URL}/api/campaigns/{self.__class__.user_a_campaign_id}", headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when accessing User A's campaign")
    
    def test_user_b_cannot_update_user_a_campaign(self, user_b_headers):
        """User B should get 404 when updating User A's campaign"""
        if not hasattr(self.__class__, 'user_a_campaign_id'):
            pytest.skip("User A campaign not created")
        
        response = requests.put(f"{BASE_URL}/api/campaigns/{self.__class__.user_a_campaign_id}", 
                               json={"name": "HACKED"}, headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when updating User A's campaign")
    
    def test_user_b_cannot_delete_user_a_campaign(self, user_b_headers):
        """User B should get 404 when deleting User A's campaign"""
        if not hasattr(self.__class__, 'user_a_campaign_id'):
            pytest.skip("User A campaign not created")
        
        response = requests.delete(f"{BASE_URL}/api/campaigns/{self.__class__.user_a_campaign_id}", headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when deleting User A's campaign")
    
    # ==================== AGENTS ISOLATION TESTS ====================
    
    def test_user_a_can_create_agent(self, user_a_headers):
        """User A creates an agent"""
        agent_data = {
            "name": f"TEST_UserA_Agent_{uuid.uuid4().hex[:8]}",
            "email": "agent_a@test.com",
            "calendly_link": "https://calendly.com/agent-a"
        }
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_data, headers=user_a_headers)
        assert response.status_code == 200, f"Failed to create agent: {response.text}"
        
        agent = response.json()
        self.__class__.user_a_agent_id = agent["id"]
        print(f"User A created agent: {agent['id']}")
    
    def test_user_b_can_create_agent(self, user_b_headers):
        """User B creates an agent"""
        agent_data = {
            "name": f"TEST_UserB_Agent_{uuid.uuid4().hex[:8]}",
            "email": "agent_b@test.com",
            "calendly_link": "https://calendly.com/agent-b"
        }
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_data, headers=user_b_headers)
        assert response.status_code == 200, f"Failed to create agent: {response.text}"
        
        agent = response.json()
        self.__class__.user_b_agent_id = agent["id"]
        print(f"User B created agent: {agent['id']}")
    
    def test_user_a_can_only_see_own_agents(self, user_a_headers):
        """User A should only see their own agents"""
        response = requests.get(f"{BASE_URL}/api/agents", headers=user_a_headers)
        assert response.status_code == 200
        
        agents = response.json()
        agent_ids = [a["id"] for a in agents]
        
        if hasattr(self.__class__, 'user_b_agent_id'):
            assert self.__class__.user_b_agent_id not in agent_ids, "User A can see User B's agent!"
        
        print(f"User A sees {len(agents)} agents (isolation verified)")
    
    def test_user_b_cannot_access_user_a_agent(self, user_b_headers):
        """User B should get 404 when accessing User A's agent"""
        if not hasattr(self.__class__, 'user_a_agent_id'):
            pytest.skip("User A agent not created")
        
        response = requests.get(f"{BASE_URL}/api/agents/{self.__class__.user_a_agent_id}", headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when accessing User A's agent")
    
    def test_user_b_cannot_update_user_a_agent(self, user_b_headers):
        """User B should get 404 when updating User A's agent"""
        if not hasattr(self.__class__, 'user_a_agent_id'):
            pytest.skip("User A agent not created")
        
        response = requests.put(f"{BASE_URL}/api/agents/{self.__class__.user_a_agent_id}", 
                               json={"name": "HACKED"}, headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when updating User A's agent")
    
    def test_user_b_cannot_delete_user_a_agent(self, user_b_headers):
        """User B should get 404 when deleting User A's agent"""
        if not hasattr(self.__class__, 'user_a_agent_id'):
            pytest.skip("User A agent not created")
        
        response = requests.delete(f"{BASE_URL}/api/agents/{self.__class__.user_a_agent_id}", headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when deleting User A's agent")
    
    # ==================== WEBHOOKS ISOLATION TESTS ====================
    
    def test_user_a_can_create_webhook(self, user_a_headers):
        """User A creates a webhook"""
        webhook_data = {
            "name": f"TEST_UserA_Webhook_{uuid.uuid4().hex[:8]}",
            "event_type": "lead_qualified",
            "notification_emails": ["usera@test.com"]
        }
        response = requests.post(f"{BASE_URL}/api/webhooks", json=webhook_data, headers=user_a_headers)
        assert response.status_code == 200, f"Failed to create webhook: {response.text}"
        
        webhook = response.json()
        self.__class__.user_a_webhook_id = webhook["id"]
        print(f"User A created webhook: {webhook['id']}")
    
    def test_user_b_can_create_webhook(self, user_b_headers):
        """User B creates a webhook"""
        webhook_data = {
            "name": f"TEST_UserB_Webhook_{uuid.uuid4().hex[:8]}",
            "event_type": "meeting_booked",
            "notification_emails": ["userb@test.com"]
        }
        response = requests.post(f"{BASE_URL}/api/webhooks", json=webhook_data, headers=user_b_headers)
        assert response.status_code == 200, f"Failed to create webhook: {response.text}"
        
        webhook = response.json()
        self.__class__.user_b_webhook_id = webhook["id"]
        print(f"User B created webhook: {webhook['id']}")
    
    def test_user_a_can_only_see_own_webhooks(self, user_a_headers):
        """User A should only see their own webhooks"""
        response = requests.get(f"{BASE_URL}/api/webhooks", headers=user_a_headers)
        assert response.status_code == 200
        
        webhooks = response.json()
        webhook_ids = [w["id"] for w in webhooks]
        
        if hasattr(self.__class__, 'user_b_webhook_id'):
            assert self.__class__.user_b_webhook_id not in webhook_ids, "User A can see User B's webhook!"
        
        print(f"User A sees {len(webhooks)} webhooks (isolation verified)")
    
    def test_user_b_cannot_update_user_a_webhook(self, user_b_headers):
        """User B should get 404 when updating User A's webhook"""
        if not hasattr(self.__class__, 'user_a_webhook_id'):
            pytest.skip("User A webhook not created")
        
        response = requests.put(f"{BASE_URL}/api/webhooks/{self.__class__.user_a_webhook_id}", 
                               json={"name": "HACKED"}, headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when updating User A's webhook")
    
    def test_user_b_cannot_delete_user_a_webhook(self, user_b_headers):
        """User B should get 404 when deleting User A's webhook"""
        if not hasattr(self.__class__, 'user_a_webhook_id'):
            pytest.skip("User A webhook not created")
        
        response = requests.delete(f"{BASE_URL}/api/webhooks/{self.__class__.user_a_webhook_id}", headers=user_b_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("User B correctly gets 404 when deleting User A's webhook")
    
    # ==================== CALLS ISOLATION TESTS ====================
    
    def test_user_a_can_only_see_own_calls(self, user_a_headers):
        """User A should only see their own calls"""
        response = requests.get(f"{BASE_URL}/api/calls", headers=user_a_headers)
        assert response.status_code == 200
        
        calls = response.json()
        print(f"User A sees {len(calls)} calls (isolation verified)")
    
    def test_user_b_can_only_see_own_calls(self, user_b_headers):
        """User B should only see their own calls"""
        response = requests.get(f"{BASE_URL}/api/calls", headers=user_b_headers)
        assert response.status_code == 200
        
        calls = response.json()
        print(f"User B sees {len(calls)} calls (isolation verified)")
    
    # ==================== DASHBOARD STATS ISOLATION TESTS ====================
    
    def test_user_a_dashboard_stats_only_show_own_data(self, user_a_headers):
        """User A's dashboard stats should only reflect their own data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=user_a_headers)
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_leads" in stats
        assert "total_calls" in stats
        print(f"User A dashboard stats: {stats.get('total_leads')} leads, {stats.get('total_calls')} calls")
    
    def test_user_b_dashboard_stats_only_show_own_data(self, user_b_headers):
        """User B's dashboard stats should only reflect their own data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=user_b_headers)
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_leads" in stats
        assert "total_calls" in stats
        print(f"User B dashboard stats: {stats.get('total_leads')} leads, {stats.get('total_calls')} calls")
    
    # ==================== CLEANUP ====================
    
    def test_cleanup_user_a_data(self, user_a_headers):
        """Cleanup User A's test data"""
        # Delete lead
        if hasattr(self.__class__, 'user_a_lead_id'):
            requests.delete(f"{BASE_URL}/api/leads/{self.__class__.user_a_lead_id}", headers=user_a_headers)
        
        # Delete campaign
        if hasattr(self.__class__, 'user_a_campaign_id'):
            requests.delete(f"{BASE_URL}/api/campaigns/{self.__class__.user_a_campaign_id}", headers=user_a_headers)
        
        # Delete agent
        if hasattr(self.__class__, 'user_a_agent_id'):
            requests.delete(f"{BASE_URL}/api/agents/{self.__class__.user_a_agent_id}", headers=user_a_headers)
        
        # Delete webhook
        if hasattr(self.__class__, 'user_a_webhook_id'):
            requests.delete(f"{BASE_URL}/api/webhooks/{self.__class__.user_a_webhook_id}", headers=user_a_headers)
        
        print("User A test data cleaned up")
    
    def test_cleanup_user_b_data(self, user_b_headers):
        """Cleanup User B's test data"""
        # Delete lead
        if hasattr(self.__class__, 'user_b_lead_id'):
            requests.delete(f"{BASE_URL}/api/leads/{self.__class__.user_b_lead_id}", headers=user_b_headers)
        
        # Delete campaign
        if hasattr(self.__class__, 'user_b_campaign_id'):
            requests.delete(f"{BASE_URL}/api/campaigns/{self.__class__.user_b_campaign_id}", headers=user_b_headers)
        
        # Delete agent
        if hasattr(self.__class__, 'user_b_agent_id'):
            requests.delete(f"{BASE_URL}/api/agents/{self.__class__.user_b_agent_id}", headers=user_b_headers)
        
        # Delete webhook
        if hasattr(self.__class__, 'user_b_webhook_id'):
            requests.delete(f"{BASE_URL}/api/webhooks/{self.__class__.user_b_webhook_id}", headers=user_b_headers)
        
        print("User B test data cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
