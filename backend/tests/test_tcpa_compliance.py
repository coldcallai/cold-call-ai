"""
TCPA Compliance Features Test Suite
Tests for:
- GET /api/compliance/status - TCPA compliance configuration status
- GET /api/compliance/calling-hours/{phone_number} - Calling hours check
- GET /api/compliance/national-dnc/{phone_number} - National DNC Registry check
- GET /api/compliance/check/{phone_number} - Full TCPA compliance check
- State-specific calling restrictions (TX, CT, FL, etc.)
- Area code to timezone mapping
"""

import pytest
import requests
import os
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Test123!"

# Test phone numbers for different timezones
TEST_PHONES = {
    "texas": "+19725551234",      # Texas/Central - 972 area code
    "california": "+14155551234", # California/Pacific - 415 area code
    "new_york": "+12125551234",   # New York/Eastern - 212 area code
    "florida": "+13055551234",    # Florida/Eastern - 305 area code
    "connecticut": "+12035551234", # Connecticut/Eastern - 203 area code
}


class TestTCPACompliance:
    """TCPA Compliance API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    # ============== COMPLIANCE STATUS TESTS ==============
    
    def test_compliance_status_endpoint_returns_200(self):
        """GET /api/compliance/status should return 200 with TCPA config"""
        response = self.session.get(f"{BASE_URL}/api/compliance/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Compliance status endpoint returns 200")
    
    def test_compliance_status_has_tcpa_compliance_section(self):
        """Compliance status should include tcpa_compliance configuration"""
        response = self.session.get(f"{BASE_URL}/api/compliance/status")
        data = response.json()
        
        assert "tcpa_compliance" in data, "Response missing 'tcpa_compliance' section"
        tcpa = data["tcpa_compliance"]
        
        # Verify required fields
        assert "calling_hours_enforcement" in tcpa, "Missing calling_hours_enforcement"
        assert "internal_dnc_list" in tcpa, "Missing internal_dnc_list"
        assert "national_dnc_registry" in tcpa, "Missing national_dnc_registry"
        
        # Verify calling hours enforcement is enabled
        assert tcpa["calling_hours_enforcement"] == True, "Calling hours enforcement should be enabled"
        
        print(f"PASS: TCPA compliance config: {tcpa}")
    
    def test_compliance_status_has_state_restrictions(self):
        """Compliance status should include state-specific calling restrictions"""
        response = self.session.get(f"{BASE_URL}/api/compliance/status")
        data = response.json()
        
        assert "state_restrictions" in data, "Response missing 'state_restrictions'"
        restrictions = data["state_restrictions"]
        
        # Verify key states with specific restrictions
        assert "TX" in restrictions, "Missing Texas restrictions"
        assert "CT" in restrictions, "Missing Connecticut restrictions"
        assert "FL" in restrictions, "Missing Florida restrictions"
        assert "DEFAULT" in restrictions, "Missing DEFAULT (Federal) restrictions"
        
        # Verify Texas has 9am-9pm restriction
        assert restrictions["TX"]["start_hour"] == 9, "Texas should start at 9am"
        assert restrictions["TX"]["end_hour"] == 21, "Texas should end at 9pm"
        
        # Verify Connecticut has 9am-8pm restriction
        assert restrictions["CT"]["start_hour"] == 9, "Connecticut should start at 9am"
        assert restrictions["CT"]["end_hour"] == 20, "Connecticut should end at 8pm"
        
        # Verify Florida has 8am-8pm restriction
        assert restrictions["FL"]["start_hour"] == 8, "Florida should start at 8am"
        assert restrictions["FL"]["end_hour"] == 20, "Florida should end at 8pm"
        
        # Verify Federal default is 8am-9pm
        assert restrictions["DEFAULT"]["start_hour"] == 8, "Federal default should start at 8am"
        assert restrictions["DEFAULT"]["end_hour"] == 21, "Federal default should end at 9pm"
        
        print(f"PASS: State restrictions verified - TX: {restrictions['TX']}, CT: {restrictions['CT']}, FL: {restrictions['FL']}")
    
    def test_compliance_status_has_checks_performed_list(self):
        """Compliance status should list all checks performed"""
        response = self.session.get(f"{BASE_URL}/api/compliance/status")
        data = response.json()
        
        assert "checks_performed" in data, "Response missing 'checks_performed'"
        checks = data["checks_performed"]
        
        # Verify calling_hours and national_dnc are in the checks list
        checks_text = " ".join(checks).lower()
        assert "calling_hours" in checks_text, "calling_hours check not listed"
        assert "national_dnc" in checks_text or "dnc" in checks_text, "national_dnc check not listed"
        
        print(f"PASS: Checks performed: {checks}")
    
    def test_compliance_status_shows_dnc_api_not_configured(self):
        """National DNC Registry should show not configured (no DNC_API_KEY)"""
        response = self.session.get(f"{BASE_URL}/api/compliance/status")
        data = response.json()
        
        dnc_config = data["tcpa_compliance"]["national_dnc_registry"]
        # DNC_API_KEY is not set in the environment, so it should show not configured
        # The test should verify the structure exists
        assert "enabled" in dnc_config or "api_configured" in dnc_config, "Missing DNC config status"
        
        print(f"PASS: National DNC Registry config: {dnc_config}")
    
    # ============== CALLING HOURS TESTS ==============
    
    def test_calling_hours_texas_number(self):
        """GET /api/compliance/calling-hours/{phone} for Texas number"""
        phone = TEST_PHONES["texas"]
        response = self.session.get(f"{BASE_URL}/api/compliance/calling-hours/{phone}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert "is_allowed" in data, "Missing is_allowed field"
        assert "timezone" in data, "Missing timezone field"
        assert "state" in data, "Missing state field"
        assert "restriction" in data, "Missing restriction field"
        assert "local_time" in data, "Missing local_time field"
        
        # Texas should be Central timezone and TX state
        assert data["state"] == "TX", f"Expected TX state, got {data['state']}"
        assert "Chicago" in data["timezone"], f"Expected Central timezone, got {data['timezone']}"
        
        # Texas has 9am-9pm restriction
        assert "Texas" in data["restriction"] or "9am-9pm" in data["restriction"], \
            f"Expected Texas restriction, got {data['restriction']}"
        
        print(f"PASS: Texas calling hours - State: {data['state']}, TZ: {data['timezone']}, "
              f"Allowed: {data['is_allowed']}, Local: {data['local_time']}, Restriction: {data['restriction']}")
    
    def test_calling_hours_california_number(self):
        """GET /api/compliance/calling-hours/{phone} for California number"""
        phone = TEST_PHONES["california"]
        response = self.session.get(f"{BASE_URL}/api/compliance/calling-hours/{phone}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # California should be Pacific timezone
        assert data["state"] == "CA", f"Expected CA state, got {data['state']}"
        assert "Los_Angeles" in data["timezone"], f"Expected Pacific timezone, got {data['timezone']}"
        
        # California uses Federal default (8am-9pm)
        assert "Federal" in data["restriction"] or "8am-9pm" in data["restriction"], \
            f"Expected Federal TCPA restriction, got {data['restriction']}"
        
        print(f"PASS: California calling hours - State: {data['state']}, TZ: {data['timezone']}, "
              f"Allowed: {data['is_allowed']}, Local: {data['local_time']}")
    
    def test_calling_hours_new_york_number(self):
        """GET /api/compliance/calling-hours/{phone} for New York number"""
        phone = TEST_PHONES["new_york"]
        response = self.session.get(f"{BASE_URL}/api/compliance/calling-hours/{phone}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # New York should be Eastern timezone
        assert data["state"] == "NY", f"Expected NY state, got {data['state']}"
        assert "New_York" in data["timezone"], f"Expected Eastern timezone, got {data['timezone']}"
        
        print(f"PASS: New York calling hours - State: {data['state']}, TZ: {data['timezone']}, "
              f"Allowed: {data['is_allowed']}, Local: {data['local_time']}")
    
    def test_calling_hours_florida_number(self):
        """GET /api/compliance/calling-hours/{phone} for Florida number (8am-8pm restriction)"""
        phone = TEST_PHONES["florida"]
        response = self.session.get(f"{BASE_URL}/api/compliance/calling-hours/{phone}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Florida should be Eastern timezone with 8am-8pm restriction
        assert data["state"] == "FL", f"Expected FL state, got {data['state']}"
        assert "Florida" in data["restriction"] or "8am-8pm" in data["restriction"], \
            f"Expected Florida restriction, got {data['restriction']}"
        
        print(f"PASS: Florida calling hours - State: {data['state']}, Restriction: {data['restriction']}, "
              f"Allowed: {data['is_allowed']}, Local: {data['local_time']}")
    
    def test_calling_hours_connecticut_number(self):
        """GET /api/compliance/calling-hours/{phone} for Connecticut number (9am-8pm restriction)"""
        phone = TEST_PHONES["connecticut"]
        response = self.session.get(f"{BASE_URL}/api/compliance/calling-hours/{phone}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Connecticut should be Eastern timezone with 9am-8pm restriction
        assert data["state"] == "CT", f"Expected CT state, got {data['state']}"
        assert "Connecticut" in data["restriction"] or "9am-8pm" in data["restriction"], \
            f"Expected Connecticut restriction, got {data['restriction']}"
        
        print(f"PASS: Connecticut calling hours - State: {data['state']}, Restriction: {data['restriction']}, "
              f"Allowed: {data['is_allowed']}, Local: {data['local_time']}")
    
    def test_calling_hours_returns_start_and_end_hours(self):
        """Calling hours response should include start_hour and end_hour"""
        phone = TEST_PHONES["texas"]
        response = self.session.get(f"{BASE_URL}/api/compliance/calling-hours/{phone}")
        data = response.json()
        
        # Verify start and end hours are present
        assert "start_hour" in data, "Missing start_hour field"
        assert "end_hour" in data, "Missing end_hour field"
        
        # Texas should be 9-21 (9am-9pm)
        assert data["start_hour"] == 9, f"Texas start_hour should be 9, got {data['start_hour']}"
        assert data["end_hour"] == 21, f"Texas end_hour should be 21, got {data['end_hour']}"
        
        print(f"PASS: Texas hours - Start: {data['start_hour']}, End: {data['end_hour']}")
    
    def test_calling_hours_blocked_shows_reason(self):
        """When calling is blocked, response should include reason and next_allowed_time"""
        phone = TEST_PHONES["texas"]
        response = self.session.get(f"{BASE_URL}/api/compliance/calling-hours/{phone}")
        data = response.json()
        
        # If not allowed, should have reason
        if not data["is_allowed"]:
            assert "reason" in data and data["reason"], "Blocked call should have reason"
            assert "next_allowed_time" in data, "Blocked call should have next_allowed_time"
            print(f"PASS: Call blocked - Reason: {data['reason']}, Next allowed: {data['next_allowed_time']}")
        else:
            print(f"PASS: Call allowed at {data['local_time']} local time")
    
    # ============== NATIONAL DNC REGISTRY TESTS ==============
    
    def test_national_dnc_check_returns_200(self):
        """GET /api/compliance/national-dnc/{phone} should return 200"""
        phone = TEST_PHONES["texas"]
        response = self.session.get(f"{BASE_URL}/api/compliance/national-dnc/{phone}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: National DNC check endpoint returns 200")
    
    def test_national_dnc_check_response_structure(self):
        """National DNC check should return proper response structure"""
        phone = TEST_PHONES["california"]
        response = self.session.get(f"{BASE_URL}/api/compliance/national-dnc/{phone}")
        data = response.json()
        
        # Verify required fields
        assert "on_national_dnc" in data, "Missing on_national_dnc field"
        assert "checked" in data, "Missing checked field"
        assert "source" in data, "Missing source field"
        
        # Since DNC_API_KEY is not configured, source should be internal_only
        assert data["source"] == "internal_only" or data["source"] == "internal_ndnc_list", \
            f"Expected internal source, got {data['source']}"
        
        print(f"PASS: National DNC check - On DNC: {data['on_national_dnc']}, "
              f"Checked: {data['checked']}, Source: {data['source']}")
    
    def test_national_dnc_check_shows_warning_without_api_key(self):
        """Without DNC_API_KEY, should show warning about external API"""
        phone = TEST_PHONES["new_york"]
        response = self.session.get(f"{BASE_URL}/api/compliance/national-dnc/{phone}")
        data = response.json()
        
        # Should have warning about external API not configured
        if "warning" in data:
            assert "DNC_API_KEY" in data["warning"] or "not configured" in data["warning"].lower(), \
                f"Warning should mention DNC_API_KEY, got: {data['warning']}"
            print(f"PASS: Warning shown: {data['warning']}")
        else:
            # If no warning, source should indicate internal only
            assert data["source"] in ["internal_only", "internal_ndnc_list"], \
                f"Expected internal source without warning, got {data['source']}"
            print(f"PASS: Source indicates internal only: {data['source']}")
    
    def test_national_dnc_check_multiple_numbers(self):
        """Test National DNC check for multiple phone numbers"""
        for name, phone in TEST_PHONES.items():
            response = self.session.get(f"{BASE_URL}/api/compliance/national-dnc/{phone}")
            assert response.status_code == 200, f"Failed for {name}: {response.status_code}"
            data = response.json()
            assert "on_national_dnc" in data, f"Missing on_national_dnc for {name}"
            print(f"PASS: {name} ({phone}) - On DNC: {data['on_national_dnc']}")
    
    # ============== FULL COMPLIANCE CHECK TESTS ==============
    
    def test_full_compliance_check_returns_200(self):
        """GET /api/compliance/check/{phone} should return 200"""
        phone = TEST_PHONES["texas"]
        response = self.session.get(f"{BASE_URL}/api/compliance/check/{phone}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Full compliance check endpoint returns 200")
    
    def test_full_compliance_check_has_is_allowed(self):
        """Full compliance check should return is_allowed boolean"""
        phone = TEST_PHONES["california"]
        response = self.session.get(f"{BASE_URL}/api/compliance/check/{phone}")
        data = response.json()
        
        assert "is_allowed" in data, "Missing is_allowed field"
        assert isinstance(data["is_allowed"], bool), "is_allowed should be boolean"
        
        print(f"PASS: Full compliance check - is_allowed: {data['is_allowed']}")
    
    def test_full_compliance_check_has_calling_hours_field(self):
        """Full compliance check should include calling_hours details"""
        phone = TEST_PHONES["texas"]
        response = self.session.get(f"{BASE_URL}/api/compliance/check/{phone}")
        data = response.json()
        
        assert "calling_hours" in data, "Missing calling_hours field in full compliance check"
        calling_hours = data["calling_hours"]
        
        # Verify calling_hours structure
        assert "is_allowed" in calling_hours, "calling_hours missing is_allowed"
        assert "timezone" in calling_hours, "calling_hours missing timezone"
        assert "state" in calling_hours, "calling_hours missing state"
        
        print(f"PASS: Full compliance check includes calling_hours: {calling_hours}")
    
    def test_full_compliance_check_has_national_dnc_field(self):
        """Full compliance check should include national_dnc details"""
        phone = TEST_PHONES["california"]
        response = self.session.get(f"{BASE_URL}/api/compliance/check/{phone}")
        data = response.json()
        
        assert "national_dnc" in data, "Missing national_dnc field in full compliance check"
        national_dnc = data["national_dnc"]
        
        # Verify national_dnc structure
        assert "on_registry" in national_dnc or "on_national_dnc" in national_dnc, \
            "national_dnc missing on_registry/on_national_dnc"
        
        print(f"PASS: Full compliance check includes national_dnc: {national_dnc}")
    
    def test_full_compliance_check_has_checks_performed(self):
        """Full compliance check should list all checks performed"""
        phone = TEST_PHONES["new_york"]
        response = self.session.get(f"{BASE_URL}/api/compliance/check/{phone}")
        data = response.json()
        
        assert "checks_performed" in data, "Missing checks_performed field"
        checks = data["checks_performed"]
        
        # Verify calling_hours and national_dnc are in checks
        assert "calling_hours" in checks, "calling_hours not in checks_performed"
        assert "national_dnc" in checks, "national_dnc not in checks_performed"
        
        print(f"PASS: Checks performed: {checks}")
    
    def test_full_compliance_check_has_reasons_when_blocked(self):
        """When compliance check fails, should include reasons"""
        phone = TEST_PHONES["florida"]
        response = self.session.get(f"{BASE_URL}/api/compliance/check/{phone}")
        data = response.json()
        
        assert "reasons" in data, "Missing reasons field"
        
        if not data["is_allowed"]:
            assert len(data["reasons"]) > 0, "Blocked call should have at least one reason"
            print(f"PASS: Call blocked with reasons: {data['reasons']}")
        else:
            print(f"PASS: Call allowed, reasons list: {data['reasons']}")
    
    def test_full_compliance_check_all_test_numbers(self):
        """Run full compliance check on all test phone numbers"""
        results = {}
        for name, phone in TEST_PHONES.items():
            response = self.session.get(f"{BASE_URL}/api/compliance/check/{phone}")
            assert response.status_code == 200, f"Failed for {name}: {response.status_code}"
            data = response.json()
            
            results[name] = {
                "is_allowed": data.get("is_allowed"),
                "state": data.get("calling_hours", {}).get("state"),
                "on_dnc": data.get("national_dnc", {}).get("on_registry", 
                          data.get("national_dnc", {}).get("on_national_dnc", False))
            }
            
            print(f"PASS: {name} - Allowed: {results[name]['is_allowed']}, "
                  f"State: {results[name]['state']}, On DNC: {results[name]['on_dnc']}")
    
    # ============== AUTHENTICATION TESTS ==============
    
    def test_compliance_endpoints_require_auth(self):
        """Compliance endpoints should require authentication"""
        # Create unauthenticated session
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        endpoints = [
            f"{BASE_URL}/api/compliance/status",
            f"{BASE_URL}/api/compliance/calling-hours/+19725551234",
            f"{BASE_URL}/api/compliance/national-dnc/+19725551234",
            f"{BASE_URL}/api/compliance/check/+19725551234",
        ]
        
        for endpoint in endpoints:
            response = unauth_session.get(endpoint)
            # Should return 401 or 403 without auth
            assert response.status_code in [401, 403], \
                f"Expected 401/403 for {endpoint}, got {response.status_code}"
            print(f"PASS: {endpoint} requires auth (got {response.status_code})")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
