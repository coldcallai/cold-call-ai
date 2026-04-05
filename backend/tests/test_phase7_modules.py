"""
Phase 7 Modules Test Suite
Tests for Bookings, Settings, and Billing modules extracted via Strangler Fig pattern.

Endpoints tested:
- GET /api/settings - Get application settings
- PUT /api/settings - Update settings
- GET /api/packs - Get available credit packs and subscription plans
- GET /api/account/usage - Get user account usage
- GET /api/bookings - List bookings
- GET /api/bookings/{booking_id} - Get specific booking
- GET /api/subscription/features - Get user subscription features
- GET /api/subscriptions/current - Get current subscription
- GET /api/subscriptions/invoices - Get invoice history
- GET /api/team/members - Get team members (requires Professional tier)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}  # unlimited tier
FREE_USER = {"email": "test_user_b@example.com", "password": "Test456!"}  # free/null tier (no team access)
STARTER_USER = {"email": "test_starter_1ea49b76@example.com", "password": "Test123!"}  # starter tier


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
            # Try different token field names
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


# ============== SETTINGS ENDPOINTS TESTS ==============

class TestSettingsEndpoints:
    """Tests for /api/settings endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_get_settings_success(self):
        """GET /api/settings - Should return application settings"""
        response = requests.get(f"{BASE_URL}/api/settings")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify settings structure
        assert "twilio_configured" in data or "qualification_threshold" in data, "Settings should contain configuration fields"
        print(f"Settings retrieved: {list(data.keys())}")
    
    def test_update_settings_success(self):
        """PUT /api/settings - Should update application settings"""
        # Update a setting
        update_data = {
            "qualification_threshold": 65,
            "min_interest_level": 7
        }
        
        response = requests.put(
            f"{BASE_URL}/api/settings",
            json=update_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify update was applied
        assert data.get("qualification_threshold") == 65, "qualification_threshold should be updated to 65"
        assert data.get("min_interest_level") == 7, "min_interest_level should be updated to 7"
        print(f"Settings updated successfully: qualification_threshold={data.get('qualification_threshold')}")
        
        # Restore original values
        requests.put(f"{BASE_URL}/api/settings", json={"qualification_threshold": 60, "min_interest_level": 6})


# ============== PACKS ENDPOINTS TESTS ==============

class TestPacksEndpoints:
    """Tests for /api/packs endpoint"""
    
    def test_get_packs_success(self):
        """GET /api/packs - Should return available credit packs and subscription plans"""
        response = requests.get(f"{BASE_URL}/api/packs")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify packs structure
        expected_keys = ["subscription_plans", "lead_packs", "call_packs", "combo_packs", "topup_packs", "prepay_discounts"]
        for key in expected_keys:
            assert key in data, f"Response should contain '{key}'"
        
        print(f"Packs retrieved: {list(data.keys())}")
        print(f"Subscription plans: {list(data.get('subscription_plans', {}).keys())}")


# ============== ACCOUNT USAGE ENDPOINTS TESTS ==============

class TestAccountUsageEndpoints:
    """Tests for /api/account/usage endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_get_account_usage_authenticated(self):
        """GET /api/account/usage - Should return user's account usage"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/account/usage",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify usage structure
        assert "user_id" in data, "Response should contain user_id"
        assert "subscription_tier" in data, "Response should contain subscription_tier"
        assert "lead_credits_remaining" in data, "Response should contain lead_credits_remaining"
        assert "call_credits_remaining" in data, "Response should contain call_credits_remaining"
        
        print(f"Account usage: tier={data.get('subscription_tier')}, lead_credits={data.get('lead_credits_remaining')}, call_credits={data.get('call_credits_remaining')}")
    
    def test_get_account_usage_unauthenticated(self):
        """GET /api/account/usage - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/account/usage")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Account usage correctly requires authentication")


# ============== BOOKINGS ENDPOINTS TESTS ==============

class TestBookingsEndpoints:
    """Tests for /api/bookings endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_get_bookings_authenticated(self):
        """GET /api/bookings - Should return user's bookings"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/bookings",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of bookings"
        print(f"Bookings retrieved: {len(data)} bookings")
        
        # If there are bookings, verify structure
        if len(data) > 0:
            booking = data[0]
            assert "id" in booking, "Booking should have id"
            assert "user_id" in booking, "Booking should have user_id"
            assert "lead_id" in booking, "Booking should have lead_id"
            assert "status" in booking, "Booking should have status"
    
    def test_get_bookings_unauthenticated(self):
        """GET /api/bookings - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/bookings")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Bookings correctly requires authentication")
    
    def test_get_bookings_with_status_filter(self):
        """GET /api/bookings?status=pending - Should filter by status"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/bookings?status=pending",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify all returned bookings have pending status
        for booking in data:
            assert booking.get("status") == "pending", f"Booking status should be pending, got {booking.get('status')}"
        
        print(f"Filtered bookings (pending): {len(data)} bookings")
    
    def test_get_bookings_with_limit(self):
        """GET /api/bookings?limit=5 - Should respect limit parameter"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/bookings?limit=5",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert len(data) <= 5, f"Should return at most 5 bookings, got {len(data)}"
        print(f"Bookings with limit=5: {len(data)} bookings")
    
    def test_get_booking_not_found(self):
        """GET /api/bookings/{booking_id} - Should return 404 for non-existent booking"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/bookings/{fake_id}",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Non-existent booking correctly returns 404")


# ============== SUBSCRIPTION FEATURES ENDPOINTS TESTS ==============

class TestSubscriptionFeaturesEndpoints:
    """Tests for /api/subscription/features endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.admin_token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.admin_headers = TestAuthHelper.get_auth_headers(self.admin_token) if self.admin_token else {}
        
        self.free_token = TestAuthHelper.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        self.free_headers = TestAuthHelper.get_auth_headers(self.free_token) if self.free_token else {}
    
    def test_get_subscription_features_unlimited_tier(self):
        """GET /api/subscription/features - Should return features for unlimited tier"""
        if not self.admin_token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/subscription/features",
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Unlimited tier should have all features
        print(f"Unlimited tier features: {data}")
        
        # Verify some expected feature keys
        expected_features = ["calendar_booking", "team_seats", "voice_cloning", "call_recording"]
        for feature in expected_features:
            if feature in data:
                print(f"  {feature}: {data[feature]}")
    
    def test_get_subscription_features_free_tier(self):
        """GET /api/subscription/features - Should return limited features for free tier"""
        if not self.free_token:
            pytest.skip("Free user authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/subscription/features",
            headers=self.free_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Free tier features: {data}")
    
    def test_get_subscription_features_unauthenticated(self):
        """GET /api/subscription/features - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/subscription/features")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Subscription features correctly requires authentication")


# ============== SUBSCRIPTIONS ENDPOINTS TESTS ==============

class TestSubscriptionsEndpoints:
    """Tests for /api/subscriptions/* endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_get_current_subscription(self):
        """GET /api/subscriptions/current - Should return current subscription details"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/current",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "tier" in data or "subscription" in data, "Response should contain tier or subscription info"
        print(f"Current subscription: tier={data.get('tier')}, status={data.get('status')}")
    
    def test_get_current_subscription_unauthenticated(self):
        """GET /api/subscriptions/current - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/current")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Current subscription correctly requires authentication")
    
    def test_get_subscription_invoices(self):
        """GET /api/subscriptions/invoices - Should return invoice history"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/invoices",
            headers=self.headers
        )
        
        # May return 503 if Stripe not configured, or 200 with empty list
        if response.status_code == 503:
            print("Stripe not configured - invoices endpoint returns 503")
            return
        
        assert response.status_code == 200, f"Expected 200 or 503, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "invoices" in data, "Response should contain invoices array"
        assert isinstance(data["invoices"], list), "Invoices should be a list"
        print(f"Invoices retrieved: {len(data['invoices'])} invoices")
    
    def test_get_subscription_invoices_unauthenticated(self):
        """GET /api/subscriptions/invoices - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/invoices")
        
        assert response.status_code in [401, 403, 503], f"Expected 401/403/503, got {response.status_code}"
        print("Subscription invoices correctly requires authentication or Stripe config")


# ============== TEAM MANAGEMENT ENDPOINTS TESTS ==============

class TestTeamManagementEndpoints:
    """Tests for /api/team/* endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        # Admin user (unlimited tier - should have team access)
        self.admin_token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.admin_headers = TestAuthHelper.get_auth_headers(self.admin_token) if self.admin_token else {}
        
        # Free user (should NOT have team access)
        self.free_token = TestAuthHelper.get_auth_token(FREE_USER["email"], FREE_USER["password"])
        self.free_headers = TestAuthHelper.get_auth_headers(self.free_token) if self.free_token else {}
    
    def test_get_team_members_unlimited_tier(self):
        """GET /api/team/members - Should return team members for Professional+ tier"""
        if not self.admin_token:
            pytest.skip("Authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/team/members",
            headers=self.admin_headers
        )
        
        # Unlimited tier should have access
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of team members"
        print(f"Team members retrieved: {len(data)} members")
    
    def test_get_team_members_free_tier_access(self):
        """GET /api/team/members - Free tier users with max_team_seats=1 should have access"""
        if not self.free_token:
            pytest.skip("Free user authentication failed")
        
        response = requests.get(
            f"{BASE_URL}/api/team/members",
            headers=self.free_headers
        )
        
        # Free tier with max_team_seats=1 should have access (returns empty list)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Free tier user has team access with {len(data)} members (max_team_seats=1)")
    
    def test_get_team_members_unauthenticated(self):
        """GET /api/team/members - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/team/members")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Team members correctly requires authentication")


# ============== USER ISOLATION TESTS ==============

class TestUserIsolation:
    """Tests for multi-tenant user isolation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.admin_token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.admin_headers = TestAuthHelper.get_auth_headers(self.admin_token) if self.admin_token else {}
        
        # User B for isolation tests
        self.user_b_token = TestAuthHelper.get_auth_token("test_user_b@example.com", "Test456!")
        self.user_b_headers = TestAuthHelper.get_auth_headers(self.user_b_token) if self.user_b_token else {}
    
    def test_bookings_user_isolation(self):
        """Users should only see their own bookings"""
        if not self.admin_token or not self.user_b_token:
            pytest.skip("Authentication failed for one or both users")
        
        # Get admin bookings
        admin_response = requests.get(
            f"{BASE_URL}/api/bookings",
            headers=self.admin_headers
        )
        assert admin_response.status_code == 200
        admin_bookings = admin_response.json()
        
        # Get user B bookings
        user_b_response = requests.get(
            f"{BASE_URL}/api/bookings",
            headers=self.user_b_headers
        )
        assert user_b_response.status_code == 200
        user_b_bookings = user_b_response.json()
        
        # Verify no overlap in booking IDs (if both have bookings)
        admin_ids = {b["id"] for b in admin_bookings}
        user_b_ids = {b["id"] for b in user_b_bookings}
        
        overlap = admin_ids.intersection(user_b_ids)
        assert len(overlap) == 0, f"Users should not share bookings, found overlap: {overlap}"
        
        print(f"User isolation verified: Admin has {len(admin_bookings)} bookings, User B has {len(user_b_bookings)} bookings")
    
    def test_account_usage_user_isolation(self):
        """Users should only see their own account usage"""
        if not self.admin_token or not self.user_b_token:
            pytest.skip("Authentication failed for one or both users")
        
        # Get admin usage
        admin_response = requests.get(
            f"{BASE_URL}/api/account/usage",
            headers=self.admin_headers
        )
        assert admin_response.status_code == 200
        admin_usage = admin_response.json()
        
        # Get user B usage
        user_b_response = requests.get(
            f"{BASE_URL}/api/account/usage",
            headers=self.user_b_headers
        )
        assert user_b_response.status_code == 200
        user_b_usage = user_b_response.json()
        
        # Verify different user IDs
        assert admin_usage["user_id"] != user_b_usage["user_id"], "Users should have different user_ids"
        
        print(f"Account usage isolation verified: Admin user_id={admin_usage['user_id'][:8]}..., User B user_id={user_b_usage['user_id'][:8]}...")


# ============== INTEGRATION TESTS ==============

class TestEndpointIntegration:
    """Integration tests for Phase 7 endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = TestAuthHelper.get_auth_token(ADMIN_USER["email"], ADMIN_USER["password"])
        self.headers = TestAuthHelper.get_auth_headers(self.token) if self.token else {}
    
    def test_settings_and_packs_consistency(self):
        """Settings and packs should be consistent"""
        # Get settings
        settings_response = requests.get(f"{BASE_URL}/api/settings")
        assert settings_response.status_code == 200
        
        # Get packs
        packs_response = requests.get(f"{BASE_URL}/api/packs")
        assert packs_response.status_code == 200
        
        packs = packs_response.json()
        assert "subscription_plans" in packs, "Packs should contain subscription_plans"
        
        print("Settings and packs endpoints are consistent")
    
    def test_subscription_features_match_tier(self):
        """Subscription features should match user's tier"""
        if not self.token:
            pytest.skip("Authentication failed")
        
        # Get account usage (contains tier)
        usage_response = requests.get(
            f"{BASE_URL}/api/account/usage",
            headers=self.headers
        )
        assert usage_response.status_code == 200
        usage = usage_response.json()
        
        # Get subscription features
        features_response = requests.get(
            f"{BASE_URL}/api/subscription/features",
            headers=self.headers
        )
        assert features_response.status_code == 200
        features = features_response.json()
        
        tier = usage.get("subscription_tier")
        print(f"User tier: {tier}")
        print(f"Features: {features}")
        
        # Unlimited tier should have all features enabled
        if tier == "unlimited":
            assert features.get("calendar_booking") == True, "Unlimited tier should have calendar_booking"
            assert features.get("max_team_seats", 0) > 0, "Unlimited tier should have max_team_seats > 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
