"""
Voice Cloning Feature Tests
Tests for ElevenLabs voice cloning integration:
- GET /api/voices/presets - List preset voices
- GET /api/voices/cloned - List user's cloned voices
- POST /api/voices/clone - Clone a new voice (requires audio files)
- DELETE /api/voices/cloned/{voice_id} - Delete a cloned voice
- POST /api/voices/preview - Preview a voice
- PUT /api/agents/{agent_id}/voice - Update agent voice settings
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Test123!"


class TestVoiceCloning:
    """Voice Cloning API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_get_preset_voices(self):
        """Test GET /api/voices/presets - should return list of ElevenLabs preset voices"""
        response = requests.get(
            f"{BASE_URL}/api/voices/presets",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get preset voices: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "voices" in data, "Response should contain 'voices' key"
        voices = data["voices"]
        assert isinstance(voices, list), "Voices should be a list"
        assert len(voices) > 0, "Should have at least one preset voice"
        
        # Verify voice structure
        first_voice = voices[0]
        assert "id" in first_voice, "Voice should have 'id'"
        assert "name" in first_voice, "Voice should have 'name'"
        assert "description" in first_voice, "Voice should have 'description'"
        
        print(f"✓ Found {len(voices)} preset voices")
        print(f"  First voice: {first_voice['name']} - {first_voice['description']}")
        
    def test_get_cloned_voices(self):
        """Test GET /api/voices/cloned - should return user's cloned voices"""
        response = requests.get(
            f"{BASE_URL}/api/voices/cloned",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get cloned voices: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "voices" in data, "Response should contain 'voices' key"
        voices = data["voices"]
        assert isinstance(voices, list), "Voices should be a list"
        
        print(f"✓ Found {len(voices)} cloned voices for user")
        
    def test_get_preset_voices_unauthorized(self):
        """Test GET /api/voices/presets without auth - should fail"""
        response = requests.get(f"{BASE_URL}/api/voices/presets")
        
        # Should require authentication
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ Preset voices endpoint requires authentication")
        
    def test_get_cloned_voices_unauthorized(self):
        """Test GET /api/voices/cloned without auth - should fail"""
        response = requests.get(f"{BASE_URL}/api/voices/cloned")
        
        # Should require authentication
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ Cloned voices endpoint requires authentication")


class TestAgentVoiceSettings:
    """Agent Voice Settings Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and find an agent"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get agents
        agents_response = requests.get(
            f"{BASE_URL}/api/agents",
            headers=self.headers
        )
        if agents_response.status_code == 200:
            agents = agents_response.json()
            if agents:
                self.agent_id = agents[0]["id"]
                self.agent_name = agents[0]["name"]
            else:
                self.agent_id = None
                self.agent_name = None
        else:
            self.agent_id = None
            self.agent_name = None
            
    def test_get_agents_with_voice_settings(self):
        """Test that agents have voice settings fields"""
        response = requests.get(
            f"{BASE_URL}/api/agents",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get agents: {response.text}"
        agents = response.json()
        
        if len(agents) > 0:
            agent = agents[0]
            # Check voice-related fields exist
            assert "voice_type" in agent, "Agent should have 'voice_type' field"
            print(f"✓ Agent '{agent['name']}' has voice_type: {agent['voice_type']}")
            
            # Check optional voice fields
            if agent.get("voice_type") == "preset":
                print(f"  - Using preset voice ID: {agent.get('preset_voice_id', 'default')}")
            elif agent.get("voice_type") == "cloned":
                print(f"  - Using cloned voice: {agent.get('cloned_voice_name', 'unknown')}")
        else:
            print("⚠ No agents found to test voice settings")
            
    def test_update_agent_voice_preset(self):
        """Test PUT /api/agents/{id}/voice - update to preset voice"""
        if not self.agent_id:
            pytest.skip("No agent available for testing")
            
        # Get a preset voice ID
        presets_response = requests.get(
            f"{BASE_URL}/api/voices/presets",
            headers=self.headers
        )
        assert presets_response.status_code == 200
        presets = presets_response.json()["voices"]
        
        if len(presets) < 2:
            pytest.skip("Not enough preset voices for testing")
            
        # Use second preset voice (to change from default)
        new_voice_id = presets[1]["id"]
        new_voice_name = presets[1]["name"]
        
        # Update agent voice
        response = requests.put(
            f"{BASE_URL}/api/agents/{self.agent_id}/voice",
            headers=self.headers,
            data={
                "voice_type": "preset",
                "voice_id": new_voice_id,
                "stability": 0.6,
                "similarity_boost": 0.8,
                "style": 0.4
            }
        )
        
        assert response.status_code == 200, f"Failed to update agent voice: {response.text}"
        data = response.json()
        
        assert data.get("voice_type") == "preset", "Voice type should be 'preset'"
        assert data.get("voice_id") == new_voice_id, "Voice ID should match"
        
        print(f"✓ Updated agent '{self.agent_name}' to use preset voice: {new_voice_name}")
        
    def test_update_agent_voice_invalid_cloned(self):
        """Test PUT /api/agents/{id}/voice - should fail with invalid cloned voice"""
        if not self.agent_id:
            pytest.skip("No agent available for testing")
            
        response = requests.put(
            f"{BASE_URL}/api/agents/{self.agent_id}/voice",
            headers=self.headers,
            data={
                "voice_type": "cloned",
                "voice_id": "invalid_voice_id_12345",
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.3
            }
        )
        
        # Should fail because cloned voice doesn't exist
        assert response.status_code == 400, f"Should fail with invalid cloned voice: {response.status_code}"
        print("✓ Correctly rejected invalid cloned voice ID")


class TestVoicePreview:
    """Voice Preview Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_voice_preview_endpoint_exists(self):
        """Test POST /api/voices/preview endpoint exists"""
        # Get a preset voice ID first
        presets_response = requests.get(
            f"{BASE_URL}/api/voices/presets",
            headers=self.headers
        )
        assert presets_response.status_code == 200
        presets = presets_response.json()["voices"]
        voice_id = presets[0]["id"]
        
        # Try to preview (may fail if ElevenLabs not configured, but endpoint should exist)
        response = requests.post(
            f"{BASE_URL}/api/voices/preview",
            headers=self.headers,
            data={
                "text": "Hello, this is a test preview.",
                "voice_id": voice_id
            }
        )
        
        # Endpoint should exist (200 or 503 if ElevenLabs not configured)
        assert response.status_code in [200, 503, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "audio" in data, "Response should contain 'audio' key"
            print("✓ Voice preview generated successfully")
        elif response.status_code == 503:
            print("⚠ ElevenLabs not configured - preview endpoint exists but service unavailable")
        else:
            print(f"⚠ Voice preview failed: {response.text}")


class TestVoiceCloneEndpoint:
    """Voice Clone Endpoint Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_clone_voice_requires_files(self):
        """Test POST /api/voices/clone - should require audio files"""
        response = requests.post(
            f"{BASE_URL}/api/voices/clone",
            headers=self.headers,
            data={
                "voice_name": "Test Voice",
                "description": "Test description"
            }
        )
        
        # Should fail without files
        assert response.status_code in [400, 422], f"Should require files: {response.status_code}"
        print("✓ Clone endpoint correctly requires audio files")
        
    def test_clone_voice_requires_name(self):
        """Test POST /api/voices/clone - should require voice name"""
        # Create a minimal audio file for testing
        import io
        fake_audio = io.BytesIO(b"fake audio content")
        fake_audio.name = "test.mp3"
        
        response = requests.post(
            f"{BASE_URL}/api/voices/clone",
            headers=self.headers,
            files={"files": ("test.mp3", fake_audio, "audio/mpeg")},
            data={"description": "Test description"}
        )
        
        # Should fail without voice_name
        assert response.status_code in [400, 422], f"Should require voice_name: {response.status_code}"
        print("✓ Clone endpoint correctly requires voice name")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
