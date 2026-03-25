"""
Test Setup Status API and Getting Started Features
Tests the setup wizard, getting started page, and call blocking functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Test123!"


class TestSetupStatusAPI:
    """Tests for /api/setup/status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_setup_status_endpoint_returns_200(self):
        """Test that setup status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Setup status endpoint returns 200")
    
    def test_setup_status_returns_steps_array(self):
        """Test that setup status returns steps array"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "steps" in data, "Response should contain 'steps' field"
        assert isinstance(data["steps"], list), "Steps should be a list"
        assert len(data["steps"]) >= 5, f"Expected at least 5 steps, got {len(data['steps'])}"
        print(f"PASS: Setup status returns {len(data['steps'])} steps")
    
    def test_setup_status_step_structure(self):
        """Test that each step has required fields"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "title", "completed", "required"]
        for step in data["steps"]:
            for field in required_fields:
                assert field in step, f"Step missing required field: {field}"
            assert isinstance(step["completed"], bool), f"completed should be boolean, got {type(step['completed'])}"
            assert isinstance(step["required"], bool), f"required should be boolean, got {type(step['required'])}"
        print("PASS: All steps have required fields with correct types")
    
    def test_setup_status_contains_all_required_steps(self):
        """Test that all required setup steps are present"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        step_ids = [s["id"] for s in data["steps"]]
        required_step_ids = ["twilio", "calendly", "compliance", "agent", "campaign"]
        
        for step_id in required_step_ids:
            assert step_id in step_ids, f"Missing required step: {step_id}"
        print(f"PASS: All required steps present: {required_step_ids}")
    
    def test_setup_status_completion_percentage(self):
        """Test that completion percentage is calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "completion_percentage" in data, "Response should contain completion_percentage"
        assert isinstance(data["completion_percentage"], (int, float)), "completion_percentage should be numeric"
        assert 0 <= data["completion_percentage"] <= 100, f"completion_percentage should be 0-100, got {data['completion_percentage']}"
        print(f"PASS: Completion percentage is {data['completion_percentage']}%")
    
    def test_setup_status_all_required_complete_field(self):
        """Test that all_required_complete field is present"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "all_required_complete" in data, "Response should contain all_required_complete"
        assert isinstance(data["all_required_complete"], bool), "all_required_complete should be boolean"
        print(f"PASS: all_required_complete = {data['all_required_complete']}")
    
    def test_setup_status_can_make_calls_field(self):
        """Test that can_make_calls field is present and matches all_required_complete"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "can_make_calls" in data, "Response should contain can_make_calls"
        assert isinstance(data["can_make_calls"], bool), "can_make_calls should be boolean"
        assert data["can_make_calls"] == data["all_required_complete"], "can_make_calls should match all_required_complete"
        print(f"PASS: can_make_calls = {data['can_make_calls']}")
    
    def test_setup_status_setup_wizard_completed_field(self):
        """Test that setup_wizard_completed field is present"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "setup_wizard_completed" in data, "Response should contain setup_wizard_completed"
        assert isinstance(data["setup_wizard_completed"], bool), "setup_wizard_completed should be boolean"
        print(f"PASS: setup_wizard_completed = {data['setup_wizard_completed']}")
    
    def test_setup_status_required_counts(self):
        """Test that required step counts are present"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "required_complete_count" in data, "Response should contain required_complete_count"
        assert "required_total_count" in data, "Response should contain required_total_count"
        assert data["required_total_count"] == 5, f"Expected 5 required steps, got {data['required_total_count']}"
        assert data["required_complete_count"] <= data["required_total_count"], "Completed count should not exceed total"
        print(f"PASS: Required steps: {data['required_complete_count']}/{data['required_total_count']} complete")
    
    def test_setup_status_requires_authentication(self):
        """Test that setup status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/setup/status")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Setup status requires authentication")


class TestSetupCanCallAPI:
    """Tests for /api/setup/can-call endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_can_call_endpoint_returns_200(self):
        """Test that can-call endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/setup/can-call", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Can-call endpoint returns 200")
    
    def test_can_call_returns_can_make_calls_field(self):
        """Test that can-call returns can_make_calls boolean"""
        response = requests.get(f"{BASE_URL}/api/setup/can-call", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "can_make_calls" in data, "Response should contain can_make_calls"
        assert isinstance(data["can_make_calls"], bool), "can_make_calls should be boolean"
        print(f"PASS: can_make_calls = {data['can_make_calls']}")
    
    def test_can_call_returns_missing_steps(self):
        """Test that can-call returns missing_steps array"""
        response = requests.get(f"{BASE_URL}/api/setup/can-call", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "missing_steps" in data, "Response should contain missing_steps"
        assert isinstance(data["missing_steps"], list), "missing_steps should be a list"
        print(f"PASS: missing_steps = {data['missing_steps']}")
    
    def test_can_call_requires_authentication(self):
        """Test that can-call endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/setup/can-call")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Can-call endpoint requires authentication")


class TestSetupWizardComplete:
    """Tests for /api/user/setup-wizard-complete endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_setup_wizard_complete_endpoint_returns_200(self):
        """Test that setup wizard complete endpoint returns 200"""
        response = requests.post(f"{BASE_URL}/api/user/setup-wizard-complete", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Setup wizard complete endpoint returns 200")
    
    def test_setup_wizard_complete_returns_message(self):
        """Test that setup wizard complete returns success message"""
        response = requests.post(f"{BASE_URL}/api/user/setup-wizard-complete", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data, "Response should contain message"
        assert "completed" in data["message"].lower() or "setup" in data["message"].lower(), \
            f"Message should indicate completion: {data['message']}"
        print(f"PASS: Setup wizard complete message: {data['message']}")
    
    def test_setup_wizard_complete_updates_status(self):
        """Test that completing wizard updates setup_wizard_completed status"""
        # Complete the wizard
        response = requests.post(f"{BASE_URL}/api/user/setup-wizard-complete", headers=self.headers)
        assert response.status_code == 200
        
        # Check status
        status_response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert status_response.status_code == 200
        data = status_response.json()
        
        assert data["setup_wizard_completed"] == True, "setup_wizard_completed should be True after completing wizard"
        print("PASS: Setup wizard completion updates status correctly")
    
    def test_setup_wizard_complete_requires_authentication(self):
        """Test that setup wizard complete endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/user/setup-wizard-complete")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Setup wizard complete requires authentication")


class TestStepCompletionStatus:
    """Tests for individual step completion status"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_twilio_step_status(self):
        """Test Twilio step completion status"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        twilio_step = next((s for s in data["steps"] if s["id"] == "twilio"), None)
        assert twilio_step is not None, "Twilio step should exist"
        assert twilio_step["required"] == True, "Twilio step should be required"
        print(f"PASS: Twilio step - completed: {twilio_step['completed']}, required: {twilio_step['required']}")
    
    def test_calendly_step_status(self):
        """Test Calendly step completion status"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        calendly_step = next((s for s in data["steps"] if s["id"] == "calendly"), None)
        assert calendly_step is not None, "Calendly step should exist"
        assert calendly_step["required"] == True, "Calendly step should be required"
        print(f"PASS: Calendly step - completed: {calendly_step['completed']}, required: {calendly_step['required']}")
    
    def test_compliance_step_status(self):
        """Test Compliance step completion status"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        compliance_step = next((s for s in data["steps"] if s["id"] == "compliance"), None)
        assert compliance_step is not None, "Compliance step should exist"
        assert compliance_step["required"] == True, "Compliance step should be required"
        print(f"PASS: Compliance step - completed: {compliance_step['completed']}, required: {compliance_step['required']}")
    
    def test_agent_step_status(self):
        """Test Agent step completion status"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        agent_step = next((s for s in data["steps"] if s["id"] == "agent"), None)
        assert agent_step is not None, "Agent step should exist"
        assert agent_step["required"] == True, "Agent step should be required"
        print(f"PASS: Agent step - completed: {agent_step['completed']}, required: {agent_step['required']}")
    
    def test_campaign_step_status(self):
        """Test Campaign step completion status"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        campaign_step = next((s for s in data["steps"] if s["id"] == "campaign"), None)
        assert campaign_step is not None, "Campaign step should exist"
        assert campaign_step["required"] == True, "Campaign step should be required"
        print(f"PASS: Campaign step - completed: {campaign_step['completed']}, required: {campaign_step['required']}")
    
    def test_crm_step_is_optional(self):
        """Test CRM step is marked as optional"""
        response = requests.get(f"{BASE_URL}/api/setup/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        crm_step = next((s for s in data["steps"] if s["id"] == "crm"), None)
        assert crm_step is not None, "CRM step should exist"
        assert crm_step["required"] == False, "CRM step should be optional (not required)"
        print(f"PASS: CRM step - completed: {crm_step['completed']}, required: {crm_step['required']} (optional)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
