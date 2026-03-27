"""
Test Voice Preview Feature for AI Cold Calling SaaS (DialGenix.ai)
Tests the /api/voices/preview endpoint and related functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVoicePreview:
    """Voice Preview endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get auth token"""
        # Login with test credentials
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("session_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get agents to find Sarah Johnson
        agents_response = requests.get(f"{BASE_URL}/api/agents", headers=self.headers)
        assert agents_response.status_code == 200, f"Failed to get agents: {agents_response.text}"
        self.agents = agents_response.json()
        
        # Find Sarah Johnson agent
        self.sarah_agent = None
        for agent in self.agents:
            if agent.get("name") == "Sarah Johnson":
                self.sarah_agent = agent
                break
    
    def test_login_success(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert "user" in data
        print(f"Login successful, user: {data['user'].get('email')}")
    
    def test_agents_page_loads(self):
        """Test that agents endpoint returns data including Sarah Johnson"""
        response = requests.get(f"{BASE_URL}/api/agents", headers=self.headers)
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)
        print(f"Found {len(agents)} agents")
        
        # Check for Sarah Johnson
        sarah_found = any(a.get("name") == "Sarah Johnson" for a in agents)
        assert sarah_found, "Sarah Johnson agent not found"
        print("Sarah Johnson agent found")
    
    def test_sarah_johnson_has_voice_settings(self):
        """Test that Sarah Johnson agent has voice_type and preset_voice_id"""
        assert self.sarah_agent is not None, "Sarah Johnson agent not found"
        
        # Check voice settings
        voice_type = self.sarah_agent.get("voice_type")
        preset_voice_id = self.sarah_agent.get("preset_voice_id")
        
        print(f"Sarah Johnson voice_type: {voice_type}")
        print(f"Sarah Johnson preset_voice_id: {preset_voice_id}")
        
        assert voice_type == "preset", f"Expected voice_type='preset', got '{voice_type}'"
        assert preset_voice_id is not None, "preset_voice_id should not be None"
        print(f"Voice settings verified: type={voice_type}, voice_id={preset_voice_id}")
    
    def test_voice_preview_endpoint_exists(self):
        """Test that /api/voices/preview endpoint exists and requires auth"""
        # Test without auth - should fail
        response = requests.post(f"{BASE_URL}/api/voices/preview", data={
            "text": "Test",
            "voice_id": "test"
        })
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print("Voice preview endpoint requires authentication - PASS")
    
    def test_voice_preview_generates_audio(self):
        """Test that voice preview generates audio for Sarah Johnson's voice"""
        assert self.sarah_agent is not None, "Sarah Johnson agent not found"
        
        voice_id = self.sarah_agent.get("preset_voice_id", "AZnzlk1XvdvUeBnXmlld")
        preview_text = f"Hi, this is {self.sarah_agent.get('name')}. I'm your AI sales agent, ready to help you connect with qualified leads and close more deals!"
        
        response = requests.post(
            f"{BASE_URL}/api/voices/preview",
            headers=self.headers,
            data={
                "text": preview_text,
                "voice_id": voice_id
            }
        )
        
        print(f"Voice preview response status: {response.status_code}")
        
        if response.status_code == 503:
            pytest.skip("ElevenLabs not configured - skipping audio generation test")
        
        assert response.status_code == 200, f"Voice preview failed: {response.text}"
        
        data = response.json()
        assert "audio" in data, "Response should contain 'audio' field"
        assert data["audio"].startswith("data:audio/mpeg;base64,"), "Audio should be base64 encoded"
        
        # Check audio data is not empty
        audio_b64 = data["audio"].replace("data:audio/mpeg;base64,", "")
        assert len(audio_b64) > 100, "Audio data should not be empty"
        
        print(f"Voice preview generated successfully, audio size: {len(audio_b64)} chars")
    
    def test_voice_preview_with_different_text(self):
        """Test voice preview with custom text"""
        voice_id = "AZnzlk1XvdvUeBnXmlld"  # Sarah's voice
        custom_text = "Hello, this is a test of the voice preview feature."
        
        response = requests.post(
            f"{BASE_URL}/api/voices/preview",
            headers=self.headers,
            data={
                "text": custom_text,
                "voice_id": voice_id
            }
        )
        
        if response.status_code == 503:
            pytest.skip("ElevenLabs not configured")
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert data["text"] == custom_text
        print("Custom text voice preview - PASS")
    
    def test_voice_preview_text_limit(self):
        """Test that voice preview limits text to 500 characters"""
        voice_id = "AZnzlk1XvdvUeBnXmlld"
        long_text = "A" * 600  # More than 500 chars
        
        response = requests.post(
            f"{BASE_URL}/api/voices/preview",
            headers=self.headers,
            data={
                "text": long_text,
                "voice_id": voice_id
            }
        )
        
        if response.status_code == 503:
            pytest.skip("ElevenLabs not configured")
        
        assert response.status_code == 200
        data = response.json()
        # Backend should truncate to 500 chars
        assert len(data.get("text", "")) <= 500, "Text should be truncated to 500 chars"
        print("Text truncation test - PASS")
    
    def test_voice_settings_button_data(self):
        """Test that agent has all required fields for voice settings button"""
        assert self.sarah_agent is not None, "Sarah Johnson agent not found"
        
        # Check required fields for UI
        required_fields = ["id", "name", "voice_type"]
        for field in required_fields:
            assert field in self.sarah_agent, f"Agent missing required field: {field}"
        
        print(f"Agent ID for data-testid: {self.sarah_agent['id']}")
        print(f"Expected data-testid: preview-voice-{self.sarah_agent['id']}")
        print("All required fields present - PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
