"""
Test Phone Verification Feature
Tests for:
- POST /api/leads/{lead_id}/verify-phone - Individual phone verification
- POST /api/leads/verify-phones-bulk - Bulk phone verification
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://voice-clone-preview-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Test123!"


class TestPhoneVerification:
    """Phone verification endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("session_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Authentication failed - skipping phone verification tests")
        
        yield
        
        # Cleanup: Delete test leads created during tests
        self._cleanup_test_leads()
    
    def _cleanup_test_leads(self):
        """Clean up test leads created during tests"""
        try:
            leads_response = self.session.get(f"{BASE_URL}/api/leads")
            if leads_response.status_code == 200:
                leads = leads_response.json()
                for lead in leads:
                    if lead.get("business_name", "").startswith("TEST_PhoneVerify"):
                        self.session.delete(f"{BASE_URL}/api/leads/{lead['id']}")
        except Exception:
            pass
    
    def _create_test_lead(self, phone="+1-555-0199", business_name=None):
        """Helper to create a test lead"""
        if business_name is None:
            business_name = f"TEST_PhoneVerify_{uuid.uuid4().hex[:8]}"
        
        response = self.session.post(f"{BASE_URL}/api/leads", json={
            "business_name": business_name,
            "phone": phone,
            "email": "test@testbusiness.com",
            "contact_name": "Test Contact"
        })
        return response
    
    # ============== Individual Phone Verification Tests ==============
    
    def test_verify_phone_endpoint_exists(self):
        """Test that verify-phone endpoint exists and requires auth"""
        # Create a test lead first
        create_response = self._create_test_lead()
        assert create_response.status_code == 200, f"Failed to create test lead: {create_response.text}"
        lead_id = create_response.json()["id"]
        
        # Test the verify endpoint
        response = self.session.post(f"{BASE_URL}/api/leads/{lead_id}/verify-phone")
        
        # Should return 200 (success) or 400/500 (Twilio error) - not 404
        assert response.status_code != 404, "verify-phone endpoint not found"
        print(f"✓ verify-phone endpoint exists, status: {response.status_code}")
    
    def test_verify_phone_returns_verification_data(self):
        """Test that verify-phone returns proper verification structure"""
        # Create a test lead
        create_response = self._create_test_lead(phone="+1-555-0123")
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Verify the phone
        response = self.session.post(f"{BASE_URL}/api/leads/{lead_id}/verify-phone")
        
        # Should succeed (Twilio may return 'unknown' with test credentials)
        assert response.status_code == 200, f"Verify phone failed: {response.text}"
        
        data = response.json()
        
        # Check response structure
        assert "lead_id" in data, "Response missing lead_id"
        assert "phone" in data, "Response missing phone"
        assert "verification" in data, "Response missing verification object"
        
        verification = data["verification"]
        assert "line_type" in verification, "Verification missing line_type"
        assert "is_mobile" in verification, "Verification missing is_mobile"
        assert "is_landline" in verification, "Verification missing is_landline"
        assert "is_voip" in verification, "Verification missing is_voip"
        assert "is_valid" in verification, "Verification missing is_valid"
        assert "dial_priority" in verification, "Verification missing dial_priority"
        
        print(f"✓ Verification response structure correct")
        print(f"  Line type: {verification['line_type']}")
        print(f"  Carrier: {verification.get('carrier', 'N/A')}")
        print(f"  Is valid: {verification['is_valid']}")
    
    def test_verify_phone_updates_lead(self):
        """Test that verify-phone updates the lead record"""
        # Create a test lead
        create_response = self._create_test_lead(phone="+1-555-0124")
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Verify the phone
        verify_response = self.session.post(f"{BASE_URL}/api/leads/{lead_id}/verify-phone")
        assert verify_response.status_code == 200
        
        # Get the lead and check it was updated
        get_response = self.session.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert get_response.status_code == 200
        
        lead = get_response.json()
        
        # Check lead was updated with verification data
        assert "line_type" in lead, "Lead not updated with line_type"
        assert "phone_verified" in lead, "Lead not updated with phone_verified"
        
        print(f"✓ Lead updated after verification")
        print(f"  phone_verified: {lead.get('phone_verified')}")
        print(f"  line_type: {lead.get('line_type')}")
        print(f"  carrier: {lead.get('carrier', 'N/A')}")
    
    def test_verify_phone_nonexistent_lead(self):
        """Test verify-phone with non-existent lead returns 404"""
        fake_lead_id = "nonexistent-lead-id-12345"
        response = self.session.post(f"{BASE_URL}/api/leads/{fake_lead_id}/verify-phone")
        
        assert response.status_code == 404, f"Expected 404 for non-existent lead, got {response.status_code}"
        print("✓ Returns 404 for non-existent lead")
    
    def test_verify_phone_requires_auth(self):
        """Test that verify-phone requires authentication"""
        # Create a lead first (with auth)
        create_response = self._create_test_lead()
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Try to verify without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.post(f"{BASE_URL}/api/leads/{lead_id}/verify-phone")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Requires authentication")
    
    # ============== Bulk Phone Verification Tests ==============
    
    def test_bulk_verify_endpoint_exists(self):
        """Test that bulk verify endpoint exists"""
        response = self.session.post(f"{BASE_URL}/api/leads/verify-phones-bulk", json={
            "verify_all_unverified": True
        })
        
        # Should not return 404
        assert response.status_code != 404, "verify-phones-bulk endpoint not found"
        print(f"✓ verify-phones-bulk endpoint exists, status: {response.status_code}")
    
    def test_bulk_verify_with_lead_ids(self):
        """Test bulk verify with specific lead IDs"""
        # Create test leads
        lead_ids = []
        for i in range(2):
            create_response = self._create_test_lead(
                phone=f"+1-555-01{50+i}",
                business_name=f"TEST_PhoneVerify_Bulk_{i}_{uuid.uuid4().hex[:6]}"
            )
            assert create_response.status_code == 200
            lead_ids.append(create_response.json()["id"])
        
        # Bulk verify
        response = self.session.post(f"{BASE_URL}/api/leads/verify-phones-bulk", json={
            "lead_ids": lead_ids
        })
        
        assert response.status_code == 200, f"Bulk verify failed: {response.text}"
        
        data = response.json()
        assert "results" in data, "Response missing results"
        
        results = data["results"]
        assert "total" in results, "Results missing total"
        assert "verified" in results, "Results missing verified"
        assert "mobile" in results, "Results missing mobile count"
        assert "landline" in results, "Results missing landline count"
        assert "voip" in results, "Results missing voip count"
        
        print(f"✓ Bulk verify with lead_ids successful")
        print(f"  Total: {results['total']}, Verified: {results['verified']}")
        print(f"  Mobile: {results['mobile']}, Landline: {results['landline']}, VoIP: {results['voip']}")
    
    def test_bulk_verify_all_unverified(self):
        """Test bulk verify with verify_all_unverified flag"""
        # Create a test lead that's unverified
        create_response = self._create_test_lead(
            phone="+1-555-0160",
            business_name=f"TEST_PhoneVerify_AllUnverified_{uuid.uuid4().hex[:6]}"
        )
        assert create_response.status_code == 200
        
        # Bulk verify all unverified
        response = self.session.post(f"{BASE_URL}/api/leads/verify-phones-bulk", json={
            "verify_all_unverified": True
        })
        
        assert response.status_code == 200, f"Bulk verify all unverified failed: {response.text}"
        
        data = response.json()
        assert "results" in data or "message" in data, "Response missing results or message"
        
        print(f"✓ Bulk verify all unverified successful")
        if "results" in data:
            print(f"  Results: {data['results']}")
    
    def test_bulk_verify_requires_params(self):
        """Test that bulk verify requires either lead_ids or verify_all_unverified"""
        response = self.session.post(f"{BASE_URL}/api/leads/verify-phones-bulk", json={})
        
        # Should return 400 or 422 for missing params
        assert response.status_code in [400, 422], f"Expected 400/422 for missing params, got {response.status_code}"
        print("✓ Returns error when no params provided")
    
    def test_bulk_verify_requires_auth(self):
        """Test that bulk verify requires authentication"""
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.post(f"{BASE_URL}/api/leads/verify-phones-bulk", json={
            "verify_all_unverified": True
        })
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Bulk verify requires authentication")


class TestLineTypeFilter:
    """Test line type filter functionality via leads endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("session_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_leads_endpoint_returns_line_type(self):
        """Test that leads endpoint returns line_type field"""
        response = self.session.get(f"{BASE_URL}/api/leads")
        assert response.status_code == 200
        
        leads = response.json()
        if len(leads) > 0:
            # Check that leads have line_type field (may be null for unverified)
            lead = leads[0]
            assert "line_type" in lead or lead.get("phone_verified") == False, \
                "Lead should have line_type field or be unverified"
            print(f"✓ Leads endpoint returns line_type field")
            print(f"  Sample lead line_type: {lead.get('line_type', 'not set')}")
        else:
            print("✓ Leads endpoint works (no leads to check)")
    
    def test_leads_have_phone_verified_field(self):
        """Test that leads have phone_verified field"""
        response = self.session.get(f"{BASE_URL}/api/leads")
        assert response.status_code == 200
        
        leads = response.json()
        if len(leads) > 0:
            lead = leads[0]
            # phone_verified should exist (may be False for unverified)
            assert "phone_verified" in lead, "Lead missing phone_verified field"
            print(f"✓ Leads have phone_verified field")
            print(f"  Sample lead phone_verified: {lead.get('phone_verified')}")
        else:
            print("✓ Leads endpoint works (no leads to check)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
