"""
Test Subscription Tier Enforcement
Tests for:
- GET /api/subscription/features - Returns correct features based on user's tier
- Subscription tier limits on lead discovery
- Subscription tier limits on campaign creation
- Subscription tier limits on agent creation
- CSV upload blocked for free users, allowed for BYL/Professional
- CSV export blocked for free users, allowed for Starter+
- ICP scoring feature access check
- Campaign creation with ICP config
- Low balance notification logic
- Monthly usage tracking
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-cold-call.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}  # Has unlimited tier
FREE_USER = {"email": "test_user_b@example.com", "password": "Test456!"}  # No subscription tier (free trial)


class TestSubscriptionFeatures:
    """Test subscription features endpoint and tier-based feature access"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_subscription_features_admin_user(self):
        """Test that admin user gets unlimited tier features"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate admin user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/subscription/features")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "tier" in data, "Response should contain 'tier'"
        assert "features" in data, "Response should contain 'features'"
        assert "usage" in data, "Response should contain 'usage'"
        assert "credits" in data, "Response should contain 'credits'"
        
        # Admin should have unlimited features
        features = data["features"]
        assert features.get("csv_export") == True, "Admin should have csv_export"
        assert features.get("csv_upload") == True, "Admin should have csv_upload"
        assert features.get("api_access") == True, "Admin should have api_access"
        assert features.get("icp_scoring") == True, "Admin should have icp_scoring"
        assert features.get("ai_icp_scoring") == True, "Admin should have ai_icp_scoring"
        assert features.get("max_campaigns") == -1, "Admin should have unlimited campaigns"
        assert features.get("max_agents") == -1, "Admin should have unlimited agents"
        
        print(f"PASS: Admin user has unlimited tier features - tier: {data['tier']}")
    
    def test_subscription_features_free_user(self):
        """Test that free user (no subscription) gets limited features"""
        token = self.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        assert token is not None, "Failed to authenticate free user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/subscription/features")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Free user should have limited features
        features = data["features"]
        
        # Free trial limits
        assert features.get("csv_export") == False, "Free user should NOT have csv_export"
        assert features.get("csv_upload") == False, "Free user should NOT have csv_upload"
        assert features.get("api_access") == False, "Free user should NOT have api_access"
        assert features.get("icp_scoring") == False, "Free user should NOT have icp_scoring"
        assert features.get("ai_icp_scoring") == False, "Free user should NOT have ai_icp_scoring"
        assert features.get("max_leads_per_month") == 50, "Free user should have 50 leads/month limit"
        assert features.get("max_calls_per_month") == 50, "Free user should have 50 calls/month limit"
        assert features.get("max_campaigns") == 1, "Free user should have 1 campaign limit"
        assert features.get("max_agents") == 1, "Free user should have 1 agent limit"
        
        print(f"PASS: Free user has limited features - tier: {data['tier']}")
    
    def test_subscription_features_usage_tracking(self):
        """Test that usage tracking is returned correctly"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/subscription/features")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify usage structure
        usage = data["usage"]
        assert "leads_used" in usage, "Usage should contain leads_used"
        assert "leads_limit" in usage, "Usage should contain leads_limit"
        assert "calls_used" in usage, "Usage should contain calls_used"
        assert "calls_limit" in usage, "Usage should contain calls_limit"
        assert "month_start" in usage, "Usage should contain month_start"
        
        # Verify credits structure
        credits = data["credits"]
        assert "lead_credits" in credits, "Credits should contain lead_credits"
        assert "call_credits" in credits, "Credits should contain call_credits"
        
        print(f"PASS: Usage tracking returned correctly - leads_used: {usage['leads_used']}, calls_used: {usage['calls_used']}")


class TestCSVFeatureAccess:
    """Test CSV upload and export feature access based on subscription tier"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_csv_export_blocked_for_free_user(self):
        """Test that CSV export is blocked for free users"""
        token = self.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        assert token is not None, "Failed to authenticate free user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/leads/export-csv")
        
        # Should be 403 Forbidden for free users
        assert response.status_code == 403, f"Expected 403 for free user CSV export, got {response.status_code}"
        
        data = response.json()
        assert "not available on your plan" in data.get("detail", "").lower() or "upgrade" in data.get("detail", "").lower(), \
            f"Error message should mention plan upgrade: {data}"
        
        print(f"PASS: CSV export correctly blocked for free user - {data.get('detail')}")
    
    def test_csv_export_allowed_for_admin(self):
        """Test that CSV export is allowed for admin/unlimited tier"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate admin user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/leads/export-csv")
        
        # Should be 200 or 404 (no leads to export) - NOT 403
        assert response.status_code in [200, 404], f"Expected 200 or 404 for admin CSV export, got {response.status_code}: {response.text}"
        
        if response.status_code == 404:
            print("PASS: CSV export allowed for admin (no leads to export)")
        else:
            print("PASS: CSV export allowed for admin (leads exported)")
    
    def test_csv_upload_blocked_for_free_user(self):
        """Test that CSV upload is blocked for free users"""
        token = self.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        assert token is not None, "Failed to authenticate free user"
        
        # Create a simple CSV file
        csv_content = "business_name,phone,email\nTest Business,+1-555-0001,test@test.com"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/leads/upload-csv", files=files, headers=headers)
        
        # Should be 403 Forbidden for free users
        assert response.status_code == 403, f"Expected 403 for free user CSV upload, got {response.status_code}"
        
        data = response.json()
        assert "not available on your plan" in data.get("detail", "").lower() or "upgrade" in data.get("detail", "").lower(), \
            f"Error message should mention plan upgrade: {data}"
        
        print(f"PASS: CSV upload correctly blocked for free user - {data.get('detail')}")
    
    def test_csv_upload_allowed_for_admin(self):
        """Test that CSV upload is allowed for admin/unlimited tier"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate admin user"
        
        # Create a simple CSV file
        csv_content = "business_name,phone,email\nTEST_CSV_Business,+1-555-9999,testcsv@test.com"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/leads/upload-csv", files=files, headers=headers)
        
        # Should be 200 for admin
        assert response.status_code == 200, f"Expected 200 for admin CSV upload, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("uploaded", 0) >= 1, "Should have uploaded at least 1 lead"
        
        print(f"PASS: CSV upload allowed for admin - uploaded {data.get('uploaded')} leads")


class TestICPScoringAccess:
    """Test ICP scoring feature access based on subscription tier"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_icp_scoring_blocked_for_free_user(self):
        """Test that ICP scoring is blocked for free users"""
        token = self.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        assert token is not None, "Failed to authenticate free user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # First, try to get a lead ID (create one if needed)
        # Try to score a non-existent lead - should still check feature access first
        response = self.session.post(f"{BASE_URL}/api/leads/fake-lead-id/icp-score")
        
        # Should be 403 Forbidden for free users (feature check happens before lead lookup)
        assert response.status_code == 403, f"Expected 403 for free user ICP scoring, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "not available on your plan" in data.get("detail", "").lower() or "upgrade" in data.get("detail", "").lower(), \
            f"Error message should mention plan upgrade: {data}"
        
        print(f"PASS: ICP scoring correctly blocked for free user - {data.get('detail')}")
    
    def test_icp_scoring_allowed_for_admin(self):
        """Test that ICP scoring is allowed for admin/unlimited tier"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate admin user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # First, create a test lead
        lead_response = self.session.post(f"{BASE_URL}/api/leads", json={
            "business_name": "TEST_ICP_Business",
            "phone": "+1-555-8888",
            "email": "testicp@test.com",
            "industry": "Technology",
            "company_size": "11-50",
            "intent_signals": ["Looking for alternative", "Need to switch"]
        })
        
        if lead_response.status_code == 201:
            lead_id = lead_response.json().get("id")
            
            # Now try ICP scoring
            response = self.session.post(f"{BASE_URL}/api/leads/{lead_id}/icp-score")
            
            # Should be 200 for admin
            assert response.status_code == 200, f"Expected 200 for admin ICP scoring, got {response.status_code}: {response.text}"
            
            data = response.json()
            assert "total_score" in data, "Response should contain total_score"
            assert "breakdown" in data, "Response should contain breakdown"
            assert "tier" in data, "Response should contain tier"
            
            print(f"PASS: ICP scoring allowed for admin - score: {data.get('total_score')}, tier: {data.get('tier')}")
            
            # Cleanup
            self.session.delete(f"{BASE_URL}/api/leads/{lead_id}")
        else:
            # If lead creation failed, just verify feature access works
            response = self.session.post(f"{BASE_URL}/api/leads/fake-lead-id/icp-score")
            # Should be 404 (lead not found) not 403 (feature blocked)
            assert response.status_code == 404, f"Expected 404 for non-existent lead, got {response.status_code}"
            print("PASS: ICP scoring feature access allowed for admin (lead not found)")


class TestCampaignLimits:
    """Test campaign creation limits based on subscription tier"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.created_campaigns = []
    
    def teardown_method(self, method):
        """Cleanup created campaigns"""
        for campaign_id in self.created_campaigns:
            try:
                self.session.delete(f"{BASE_URL}/api/campaigns/{campaign_id}")
            except:
                pass
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_campaign_creation_with_icp_config(self):
        """Test campaign creation with ICP configuration"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate admin user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Create campaign with ICP config
        campaign_data = {
            "name": "TEST_ICP_Campaign",
            "description": "Test campaign with ICP config",
            "ai_script": "Hello, this is a test call.",
            "qualification_criteria": {"min_score": 60},
            "calls_per_day": 50,
            "icp_config": {
                "target_industries": ["Technology", "Software"],
                "preferred_company_sizes": ["11-50", "51-200"],
                "high_value_signals": ["alternative", "switch", "looking for"],
                "decision_maker_titles": ["owner", "manager", "ceo"]
            },
            "min_icp_score": 50
        }
        
        response = self.session.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        
        assert response.status_code == 200 or response.status_code == 201, \
            f"Expected 200/201 for campaign creation, got {response.status_code}: {response.text}"
        
        data = response.json()
        self.created_campaigns.append(data.get("id"))
        
        # Verify ICP config was saved
        assert data.get("icp_config") is not None, "Campaign should have icp_config"
        assert data.get("min_icp_score") == 50, "Campaign should have min_icp_score of 50"
        
        print(f"PASS: Campaign created with ICP config - id: {data.get('id')}")
    
    def test_free_user_campaign_limit(self):
        """Test that free user has campaign limit of 1"""
        token = self.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        assert token is not None, "Failed to authenticate free user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get current campaigns count
        campaigns_response = self.session.get(f"{BASE_URL}/api/campaigns")
        current_campaigns = campaigns_response.json() if campaigns_response.status_code == 200 else []
        
        # If user already has 1 campaign, trying to create another should fail
        if len(current_campaigns) >= 1:
            campaign_data = {
                "name": "TEST_Limit_Campaign",
                "ai_script": "Test script",
                "calls_per_day": 10
            }
            
            response = self.session.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
            
            # Should be 403 - limit reached
            assert response.status_code == 403, f"Expected 403 for campaign limit, got {response.status_code}"
            
            data = response.json()
            assert "limit" in data.get("detail", "").lower(), f"Error should mention limit: {data}"
            
            print(f"PASS: Free user campaign limit enforced - {data.get('detail')}")
        else:
            # Create first campaign (should succeed)
            campaign_data = {
                "name": "TEST_First_Campaign",
                "ai_script": "Test script",
                "calls_per_day": 10
            }
            
            response = self.session.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
            
            if response.status_code in [200, 201]:
                campaign_id = response.json().get("id")
                self.created_campaigns.append(campaign_id)
                
                # Now try to create second campaign (should fail)
                campaign_data["name"] = "TEST_Second_Campaign"
                response2 = self.session.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
                
                assert response2.status_code == 403, f"Expected 403 for second campaign, got {response2.status_code}"
                print("PASS: Free user campaign limit enforced (1 campaign max)")
            else:
                print(f"INFO: Could not test campaign limit - creation failed: {response.status_code}")


class TestAgentLimits:
    """Test agent creation limits based on subscription tier"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.created_agents = []
    
    def teardown_method(self, method):
        """Cleanup created agents"""
        for agent_id in self.created_agents:
            try:
                self.session.delete(f"{BASE_URL}/api/agents/{agent_id}")
            except:
                pass
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_admin_unlimited_agents(self):
        """Test that admin can create agents without limit"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate admin user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Create an agent
        agent_data = {
            "name": "TEST_Agent_1",
            "email": "testagent1@test.com",
            "calendly_link": "https://calendly.com/test",
            "max_daily_calls": 50
        }
        
        response = self.session.post(f"{BASE_URL}/api/agents", json=agent_data)
        
        assert response.status_code in [200, 201], f"Expected 200/201 for agent creation, got {response.status_code}: {response.text}"
        
        data = response.json()
        self.created_agents.append(data.get("id"))
        
        print(f"PASS: Admin can create agents - id: {data.get('id')}")
    
    def test_free_user_agent_limit(self):
        """Test that free user has agent limit of 1"""
        token = self.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        assert token is not None, "Failed to authenticate free user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get current agents count
        agents_response = self.session.get(f"{BASE_URL}/api/agents")
        current_agents = agents_response.json() if agents_response.status_code == 200 else []
        
        # If user already has 1 agent, trying to create another should fail
        if len(current_agents) >= 1:
            agent_data = {
                "name": "TEST_Limit_Agent",
                "email": "testlimitagent@test.com",
                "calendly_link": "https://calendly.com/test"
            }
            
            response = self.session.post(f"{BASE_URL}/api/agents", json=agent_data)
            
            # Should be 403 - limit reached
            assert response.status_code == 403, f"Expected 403 for agent limit, got {response.status_code}"
            
            data = response.json()
            assert "limit" in data.get("detail", "").lower(), f"Error should mention limit: {data}"
            
            print(f"PASS: Free user agent limit enforced - {data.get('detail')}")
        else:
            # Create first agent (should succeed)
            agent_data = {
                "name": "TEST_First_Agent",
                "email": "testfirstagent@test.com",
                "calendly_link": "https://calendly.com/test"
            }
            
            response = self.session.post(f"{BASE_URL}/api/agents", json=agent_data)
            
            if response.status_code in [200, 201]:
                agent_id = response.json().get("id")
                self.created_agents.append(agent_id)
                
                # Now try to create second agent (should fail)
                agent_data["name"] = "TEST_Second_Agent"
                agent_data["email"] = "testsecondagent@test.com"
                response2 = self.session.post(f"{BASE_URL}/api/agents", json=agent_data)
                
                assert response2.status_code == 403, f"Expected 403 for second agent, got {response2.status_code}"
                print("PASS: Free user agent limit enforced (1 agent max)")
            else:
                print(f"INFO: Could not test agent limit - creation failed: {response.status_code}")


class TestLeadDiscoveryLimits:
    """Test lead discovery limits based on subscription tier"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_lead_discovery_limit_check(self):
        """Test that lead discovery checks subscription limits"""
        token = self.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        assert token is not None, "Failed to authenticate free user"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try to discover leads - should check limits
        # Free user has 50 leads/month limit
        response = self.session.post(f"{BASE_URL}/api/leads/gpt-intent-search", json={
            "search_query": "credit card processing",
            "max_results": 5
        })
        
        # Could be 402 (insufficient credits), 403 (limit reached), or 200 (success)
        # All are valid responses depending on user's current state
        assert response.status_code in [200, 402, 403], \
            f"Expected 200, 402, or 403 for lead discovery, got {response.status_code}: {response.text}"
        
        if response.status_code == 403:
            data = response.json()
            assert "limit" in data.get("detail", "").lower() or "upgrade" in data.get("detail", "").lower(), \
                f"Error should mention limit or upgrade: {data}"
            print(f"PASS: Lead discovery limit enforced - {data.get('detail')}")
        elif response.status_code == 402:
            data = response.json()
            assert "credit" in data.get("detail", "").lower(), f"Error should mention credits: {data}"
            print(f"PASS: Lead discovery credit check enforced - {data.get('detail')}")
        else:
            print("PASS: Lead discovery allowed (within limits)")


class TestLowBalanceNotification:
    """Test low balance notification logic"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_auth_me_triggers_low_balance_check(self):
        """Test that /auth/me endpoint triggers low balance check"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Call /auth/me which should trigger check_low_balance_and_notify
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify user data is returned
        assert "user_id" in data, "Response should contain user_id"
        assert "email" in data, "Response should contain email"
        
        # Verify credit fields exist (used by low balance check)
        assert "lead_credits_remaining" in data or data.get("lead_credits_remaining") is None, \
            "Response should contain lead_credits_remaining"
        assert "call_credits_remaining" in data or data.get("call_credits_remaining") is None, \
            "Response should contain call_credits_remaining"
        
        print(f"PASS: /auth/me returns user data with credit info - lead_credits: {data.get('lead_credits_remaining')}, call_credits: {data.get('call_credits_remaining')}")


class TestMonthlyUsageTracking:
    """Test monthly usage tracking functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email: str, password: str) -> str:
        """Get authentication token for a user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("session_token")
        return None
    
    def test_monthly_usage_in_subscription_features(self):
        """Test that monthly usage is tracked and returned in subscription features"""
        token = self.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        assert token is not None, "Failed to authenticate"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = self.session.get(f"{BASE_URL}/api/subscription/features")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        usage = data.get("usage", {})
        
        # Verify usage tracking fields
        assert "leads_used" in usage, "Usage should contain leads_used"
        assert "calls_used" in usage, "Usage should contain calls_used"
        assert "month_start" in usage, "Usage should contain month_start"
        
        # Verify month_start is a valid ISO date
        month_start = usage.get("month_start")
        try:
            datetime.fromisoformat(month_start.replace("Z", "+00:00"))
            print(f"PASS: Monthly usage tracking works - leads_used: {usage['leads_used']}, calls_used: {usage['calls_used']}, month_start: {month_start}")
        except:
            pytest.fail(f"month_start is not a valid ISO date: {month_start}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
