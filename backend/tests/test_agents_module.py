"""
Test Agents Module (Phase 4 Strangler Fig)
Tests for /app/backend/routes/agents.py and /app/backend/services/agent_service.py

Features tested:
- Agent CRUD operations (Create, Read, Update, Delete)
- Voice management (preset voices, cloned voices)
- Agent voice settings update
- User isolation (users can only access their own agents)
- Authentication requirements
"""

import pytest
import requests
import os
import uuid
from typing import Optional

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable not set")

# Test credentials from test_credentials.md
ADMIN_USER = {"email": "test@example.com", "password": "Test123!"}
USER_B = {"email": "test_user_b@example.com", "password": "Test456!"}


class TestAgentsModuleSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        """Get auth token for user B (for isolation tests)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=USER_B
        )
        if response.status_code != 200:
            pytest.skip(f"User B login failed: {response.status_code} - {response.text}")
        return response.json().get("session_token")
    
    def test_api_health(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("API health check passed")


class TestAgentsCRUD:
    """Test Agent CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        """Auth headers for requests"""
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_list_agents_requires_auth(self):
        """GET /api/agents requires authentication"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("List agents requires auth - PASS")
    
    def test_list_agents_authenticated(self, headers):
        """GET /api/agents returns list for authenticated user"""
        response = requests.get(f"{BASE_URL}/api/agents", headers=headers)
        assert response.status_code == 200, f"List agents failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"List agents returned {len(data)} agents - PASS")
    
    def test_create_agent(self, headers):
        """POST /api/agents creates a new agent"""
        test_agent = {
            "name": f"TEST_Agent_{uuid.uuid4().hex[:8]}",
            "email": "testagent@example.com",
            "phone": "+1234567890",
            "calendly_link": "https://calendly.com/test-agent",
            "max_daily_calls": 100,
            "use_case": "sales_cold_calling",
            "voice_type": "preset",
            "preset_voice_id": "21m00Tcm4TlvDq8ikWAM"
        }
        
        response = requests.post(f"{BASE_URL}/api/agents", json=test_agent, headers=headers)
        assert response.status_code == 200 or response.status_code == 201, \
            f"Create agent failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain agent id"
        assert data["name"] == test_agent["name"], "Agent name should match"
        assert data["email"] == test_agent["email"], "Agent email should match"
        assert data["calendly_link"] == test_agent["calendly_link"], "Calendly link should match"
        assert data["voice_type"] == "preset", "Voice type should be preset"
        assert "user_id" in data, "Agent should have user_id"
        
        # Store agent_id for later tests
        pytest.test_agent_id = data["id"]
        print(f"Create agent successful - ID: {data['id']} - PASS")
        return data["id"]
    
    def test_get_agent_by_id(self, headers):
        """GET /api/agents/{agent_id} returns specific agent"""
        agent_id = getattr(pytest, 'test_agent_id', None)
        if not agent_id:
            pytest.skip("No test agent created")
        
        response = requests.get(f"{BASE_URL}/api/agents/{agent_id}", headers=headers)
        assert response.status_code == 200, f"Get agent failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["id"] == agent_id, "Agent ID should match"
        assert "name" in data, "Agent should have name"
        assert "email" in data, "Agent should have email"
        print(f"Get agent by ID successful - PASS")
    
    def test_get_nonexistent_agent(self, headers):
        """GET /api/agents/{agent_id} returns 404 for non-existent agent"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/agents/{fake_id}", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Get non-existent agent returns 404 - PASS")
    
    def test_update_agent(self, headers):
        """PUT /api/agents/{agent_id} updates agent"""
        agent_id = getattr(pytest, 'test_agent_id', None)
        if not agent_id:
            pytest.skip("No test agent created")
        
        updates = {
            "name": f"TEST_Updated_Agent_{uuid.uuid4().hex[:8]}",
            "max_daily_calls": 200,
            "is_active": False
        }
        
        response = requests.put(f"{BASE_URL}/api/agents/{agent_id}", json=updates, headers=headers)
        assert response.status_code == 200, f"Update agent failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["name"] == updates["name"], "Name should be updated"
        assert data["max_daily_calls"] == 200, "Max daily calls should be updated"
        assert data["is_active"] == False, "is_active should be updated"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/agents/{agent_id}", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == updates["name"], "Update should persist"
        print("Update agent successful - PASS")
    
    def test_update_nonexistent_agent(self, headers):
        """PUT /api/agents/{agent_id} returns 404 for non-existent agent"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/agents/{fake_id}",
            json={"name": "Test"},
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Update non-existent agent returns 404 - PASS")
    
    def test_delete_agent(self, headers):
        """DELETE /api/agents/{agent_id} deletes agent"""
        # Create a new agent to delete
        test_agent = {
            "name": f"TEST_ToDelete_{uuid.uuid4().hex[:8]}",
            "email": "delete@example.com",
            "calendly_link": "https://calendly.com/delete-test"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/agents", json=test_agent, headers=headers)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        agent_id = create_response.json()["id"]
        
        # Delete the agent
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}", headers=headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.status_code} - {delete_response.text}"
        
        # Verify deletion with GET
        get_response = requests.get(f"{BASE_URL}/api/agents/{agent_id}", headers=headers)
        assert get_response.status_code == 404, "Deleted agent should return 404"
        print("Delete agent successful - PASS")
    
    def test_delete_nonexistent_agent(self, headers):
        """DELETE /api/agents/{agent_id} returns 404 for non-existent agent"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/agents/{fake_id}", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Delete non-existent agent returns 404 - PASS")


class TestVoiceManagement:
    """Test voice management endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        """Auth headers for requests"""
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_get_preset_voices_requires_auth(self):
        """GET /api/voices/presets requires authentication"""
        response = requests.get(f"{BASE_URL}/api/voices/presets")
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("Get preset voices requires auth - PASS")
    
    def test_get_preset_voices(self, headers):
        """GET /api/voices/presets returns list of ElevenLabs preset voices"""
        response = requests.get(f"{BASE_URL}/api/voices/presets", headers=headers)
        assert response.status_code == 200, f"Get preset voices failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "voices" in data, "Response should contain 'voices' key"
        voices = data["voices"]
        assert isinstance(voices, list), "Voices should be a list"
        assert len(voices) > 0, "Should have at least one preset voice"
        
        # Verify voice structure
        first_voice = voices[0]
        assert "id" in first_voice, "Voice should have id"
        assert "name" in first_voice, "Voice should have name"
        assert "description" in first_voice, "Voice should have description"
        
        # Check for known preset voice (Rachel)
        voice_names = [v["name"] for v in voices]
        assert "Rachel" in voice_names, "Rachel should be in preset voices"
        
        print(f"Get preset voices returned {len(voices)} voices - PASS")
    
    def test_get_cloned_voices_requires_auth(self):
        """GET /api/voices/cloned requires authentication"""
        response = requests.get(f"{BASE_URL}/api/voices/cloned")
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("Get cloned voices requires auth - PASS")
    
    def test_get_cloned_voices(self, headers):
        """GET /api/voices/cloned returns user's cloned voices"""
        response = requests.get(f"{BASE_URL}/api/voices/cloned", headers=headers)
        assert response.status_code == 200, f"Get cloned voices failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "voices" in data, "Response should contain 'voices' key"
        assert isinstance(data["voices"], list), "Voices should be a list"
        print(f"Get cloned voices returned {len(data['voices'])} voices - PASS")


class TestAgentVoiceSettings:
    """Test agent voice settings update"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        """Auth headers for requests"""
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_agent(self, headers):
        """Create a test agent for voice settings tests"""
        test_agent = {
            "name": f"TEST_VoiceAgent_{uuid.uuid4().hex[:8]}",
            "email": "voicetest@example.com",
            "calendly_link": "https://calendly.com/voice-test"
        }
        response = requests.post(f"{BASE_URL}/api/agents", json=test_agent, headers=headers)
        if response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create test agent: {response.text}")
        return response.json()
    
    def test_update_agent_voice_preset(self, headers, test_agent):
        """PUT /api/agents/{agent_id}/voice updates voice settings with preset"""
        agent_id = test_agent["id"]
        
        # Use form data for this endpoint
        form_data = {
            "voice_type": "preset",
            "voice_id": "TxGEqnHWrfWFTfGW9XjX",  # Josh voice
            "stability": "0.6",
            "similarity_boost": "0.8",
            "style": "0.4"
        }
        
        # Remove Content-Type header for form data
        form_headers = {"Authorization": headers["Authorization"]}
        
        response = requests.put(
            f"{BASE_URL}/api/agents/{agent_id}/voice",
            data=form_data,
            headers=form_headers
        )
        assert response.status_code == 200, f"Update voice failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["voice_type"] == "preset", "Voice type should be preset"
        assert data["voice_id"] == "TxGEqnHWrfWFTfGW9XjX", "Voice ID should match"
        print("Update agent voice with preset - PASS")
    
    def test_update_voice_nonexistent_agent(self, headers):
        """PUT /api/agents/{agent_id}/voice returns 404 for non-existent agent"""
        fake_id = str(uuid.uuid4())
        
        form_data = {
            "voice_type": "preset",
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "stability": "0.5",
            "similarity_boost": "0.75",
            "style": "0.3"
        }
        
        form_headers = {"Authorization": headers["Authorization"]}
        
        response = requests.put(
            f"{BASE_URL}/api/agents/{fake_id}/voice",
            data=form_data,
            headers=form_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Update voice for non-existent agent returns 404 - PASS")


class TestUserIsolation:
    """Test that users can only access their own agents"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def user_b_token(self):
        """Get auth token for user B"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=USER_B
        )
        if response.status_code != 200:
            pytest.skip(f"User B login failed: {response.status_code}")
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def user_b_headers(self, user_b_token):
        return {"Authorization": f"Bearer {user_b_token}", "Content-Type": "application/json"}
    
    def test_user_cannot_access_other_users_agent(self, admin_headers, user_b_headers):
        """User B cannot access admin's agent"""
        # Create agent as admin
        test_agent = {
            "name": f"TEST_AdminAgent_{uuid.uuid4().hex[:8]}",
            "email": "adminagent@example.com",
            "calendly_link": "https://calendly.com/admin-agent"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/agents", json=test_agent, headers=admin_headers)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create admin agent: {create_response.text}")
        
        admin_agent_id = create_response.json()["id"]
        
        # Try to access as User B
        get_response = requests.get(f"{BASE_URL}/api/agents/{admin_agent_id}", headers=user_b_headers)
        assert get_response.status_code == 404, \
            f"User B should not access admin's agent, got {get_response.status_code}"
        
        # Cleanup - delete the agent
        requests.delete(f"{BASE_URL}/api/agents/{admin_agent_id}", headers=admin_headers)
        print("User isolation - cannot access other user's agent - PASS")
    
    def test_user_cannot_update_other_users_agent(self, admin_headers, user_b_headers):
        """User B cannot update admin's agent"""
        # Create agent as admin
        test_agent = {
            "name": f"TEST_AdminAgent2_{uuid.uuid4().hex[:8]}",
            "email": "adminagent2@example.com",
            "calendly_link": "https://calendly.com/admin-agent2"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/agents", json=test_agent, headers=admin_headers)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create admin agent: {create_response.text}")
        
        admin_agent_id = create_response.json()["id"]
        
        # Try to update as User B
        update_response = requests.put(
            f"{BASE_URL}/api/agents/{admin_agent_id}",
            json={"name": "Hacked Agent"},
            headers=user_b_headers
        )
        assert update_response.status_code == 404, \
            f"User B should not update admin's agent, got {update_response.status_code}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/{admin_agent_id}", headers=admin_headers)
        print("User isolation - cannot update other user's agent - PASS")
    
    def test_user_cannot_delete_other_users_agent(self, admin_headers, user_b_headers):
        """User B cannot delete admin's agent"""
        # Create agent as admin
        test_agent = {
            "name": f"TEST_AdminAgent3_{uuid.uuid4().hex[:8]}",
            "email": "adminagent3@example.com",
            "calendly_link": "https://calendly.com/admin-agent3"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/agents", json=test_agent, headers=admin_headers)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create admin agent: {create_response.text}")
        
        admin_agent_id = create_response.json()["id"]
        
        # Try to delete as User B
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{admin_agent_id}", headers=user_b_headers)
        assert delete_response.status_code == 404, \
            f"User B should not delete admin's agent, got {delete_response.status_code}"
        
        # Verify agent still exists for admin
        get_response = requests.get(f"{BASE_URL}/api/agents/{admin_agent_id}", headers=admin_headers)
        assert get_response.status_code == 200, "Agent should still exist for admin"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/{admin_agent_id}", headers=admin_headers)
        print("User isolation - cannot delete other user's agent - PASS")
    
    def test_users_see_only_their_own_agents(self, admin_headers, user_b_headers):
        """Each user only sees their own agents in list"""
        # Create agent as admin
        admin_agent = {
            "name": f"TEST_AdminOnly_{uuid.uuid4().hex[:8]}",
            "email": "adminonly@example.com",
            "calendly_link": "https://calendly.com/admin-only"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/agents", json=admin_agent, headers=admin_headers)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create admin agent: {create_response.text}")
        
        admin_agent_id = create_response.json()["id"]
        
        # List agents as User B
        list_response = requests.get(f"{BASE_URL}/api/agents", headers=user_b_headers)
        assert list_response.status_code == 200
        
        user_b_agents = list_response.json()
        user_b_agent_ids = [a["id"] for a in user_b_agents]
        
        assert admin_agent_id not in user_b_agent_ids, \
            "Admin's agent should not appear in User B's list"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/{admin_agent_id}", headers=admin_headers)
        print("User isolation - users see only their own agents - PASS")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get auth token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_USER
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        return response.json().get("session_token")
    
    @pytest.fixture(scope="class")
    def headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    def test_cleanup_test_agents(self, headers):
        """Clean up TEST_ prefixed agents"""
        response = requests.get(f"{BASE_URL}/api/agents", headers=headers)
        if response.status_code != 200:
            print("Could not list agents for cleanup")
            return
        
        agents = response.json()
        deleted_count = 0
        
        for agent in agents:
            if agent.get("name", "").startswith("TEST_"):
                delete_response = requests.delete(
                    f"{BASE_URL}/api/agents/{agent['id']}",
                    headers=headers
                )
                if delete_response.status_code == 200:
                    deleted_count += 1
        
        print(f"Cleanup: Deleted {deleted_count} test agents - PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
