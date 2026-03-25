#!/usr/bin/env python3
"""
Backend API Testing for AI Cold Calling Machine MVP
Tests all API endpoints including CRUD operations, dashboard stats, and mocked integrations
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Use the public backend URL from frontend .env
BACKEND_URL = "https://onboard-dialgenix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class APITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.failures.append({"test": test_name, "details": details})
            print(f"❌ {test_name} - {details}")

    def test_api_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                         data: Dict = None, test_name: str = None) -> tuple:
        """Generic API endpoint tester"""
        if not test_name:
            test_name = f"{method} {endpoint}"
        
        url = f"{API_BASE}/{endpoint.lstrip('/')}"
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
                response = self.session.post(url, json=data)
            elif method == 'PUT':
                response = self.session.put(url, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            self.log_result(test_name, success, 
                           f"Expected {expected_status}, got {response.status_code}" if not success else "")
            
            return success, response.json() if success and response.content else {}
            
        except Exception as e:
            self.log_result(test_name, False, f"Exception: {str(e)}")
            return False, {}

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        print("\n🔍 Testing Dashboard Stats...")
        success, data = self.test_api_endpoint('GET', '/dashboard/stats', test_name="Dashboard Stats")
        
        if success:
            required_fields = ['total_leads', 'qualified_leads', 'booked_leads', 'total_calls', 
                              'active_campaigns', 'total_agents', 'qualification_rate', 'booking_rate']
            for field in required_fields:
                if field not in data:
                    self.log_result(f"Dashboard Stats - {field} field", False, f"Missing field: {field}")
                else:
                    self.log_result(f"Dashboard Stats - {field} field", True)

    def test_lead_discovery(self):
        """Test lead discovery endpoint (MOCKED)"""
        print("\n🔍 Testing Lead Discovery...")
        data = {
            "search_query": "credit card processing",
            "location": "test location",
            "max_results": 5
        }
        success, response = self.test_api_endpoint('POST', '/leads/discover', 200, data, 
                                                 "Lead Discovery - Discover Leads")
        
        if success:
            if 'discovered' in response and 'leads' in response:
                self.log_result("Lead Discovery - Response Format", True)
                if response['discovered'] > 0:
                    self.log_result("Lead Discovery - Leads Generated", True)
                else:
                    self.log_result("Lead Discovery - Leads Generated", False, "No leads discovered")
            else:
                self.log_result("Lead Discovery - Response Format", False, "Missing 'discovered' or 'leads' fields")

    def test_leads_crud(self):
        """Test leads CRUD operations"""
        print("\n🔍 Testing Leads CRUD...")
        
        # Test GET leads (empty initially)
        success, leads = self.test_api_endpoint('GET', '/leads', test_name="Get Leads")
        
        # Test CREATE lead
        lead_data = {
            "business_name": "Test Business",
            "contact_name": "John Doe",
            "phone": "+1-555-0123",
            "email": "test@business.com",
            "source": "manual"
        }
        success, created_lead = self.test_api_endpoint('POST', '/leads', 200, lead_data, "Create Lead")
        
        if success and 'id' in created_lead:
            lead_id = created_lead['id']
            
            # Test GET single lead
            self.test_api_endpoint('GET', f'/leads/{lead_id}', test_name="Get Single Lead")
            
            # Test UPDATE lead
            update_data = {"contact_name": "Jane Doe Updated"}
            self.test_api_endpoint('PUT', f'/leads/{lead_id}', data=update_data, test_name="Update Lead")
            
            # Test DELETE lead
            self.test_api_endpoint('DELETE', f'/leads/{lead_id}', 200, test_name="Delete Lead")
            
            return lead_id
        return None

    def test_campaigns_crud(self):
        """Test campaigns CRUD operations"""
        print("\n🔍 Testing Campaigns CRUD...")
        
        # Test GET campaigns
        self.test_api_endpoint('GET', '/campaigns', test_name="Get Campaigns")
        
        # Test CREATE campaign
        campaign_data = {
            "name": "Test Campaign",
            "description": "Test campaign for API testing",
            "ai_script": "Hello, this is a test script for testing purposes.",
            "calls_per_day": 50
        }
        success, created_campaign = self.test_api_endpoint('POST', '/campaigns', 200, campaign_data, 
                                                         "Create Campaign")
        
        if success and 'id' in created_campaign:
            campaign_id = created_campaign['id']
            
            # Test GET single campaign
            self.test_api_endpoint('GET', f'/campaigns/{campaign_id}', test_name="Get Single Campaign")
            
            # Test START campaign
            self.test_api_endpoint('POST', f'/campaigns/{campaign_id}/start', test_name="Start Campaign")
            
            # Test PAUSE campaign
            self.test_api_endpoint('POST', f'/campaigns/{campaign_id}/pause', test_name="Pause Campaign")
            
            # Test UPDATE campaign
            update_data = {"description": "Updated campaign description"}
            self.test_api_endpoint('PUT', f'/campaigns/{campaign_id}', data=update_data, 
                                 test_name="Update Campaign")
            
            return campaign_id
        return None

    def test_agents_crud(self):
        """Test agents CRUD operations"""
        print("\n🔍 Testing Agents CRUD...")
        
        # Test GET agents
        self.test_api_endpoint('GET', '/agents', test_name="Get Agents")
        
        # Test CREATE agent
        agent_data = {
            "name": "Test Agent",
            "email": "agent@test.com",
            "phone": "+1-555-0456",
            "calendly_link": "https://calendly.com/test-agent/30min",
            "max_daily_calls": 30
        }
        success, created_agent = self.test_api_endpoint('POST', '/agents', 200, agent_data, "Create Agent")
        
        if success and 'id' in created_agent:
            agent_id = created_agent['id']
            
            # Test GET single agent
            self.test_api_endpoint('GET', f'/agents/{agent_id}', test_name="Get Single Agent")
            
            # Test UPDATE agent
            update_data = {"is_active": False}
            self.test_api_endpoint('PUT', f'/agents/{agent_id}', data=update_data, test_name="Update Agent")
            
            return agent_id
        return None

    def test_calls_functionality(self, lead_id: str = None, campaign_id: str = None):
        """Test call-related functionality"""
        print("\n🔍 Testing Call Functionality...")
        
        # Test GET calls
        self.test_api_endpoint('GET', '/calls', test_name="Get Calls")
        
        if lead_id and campaign_id:
            # Test simulate call
            url = f"/calls/simulate?lead_id={lead_id}&campaign_id={campaign_id}"
            success, response = self.test_api_endpoint('POST', url, test_name="Simulate Call")
            
            if success and 'call_id' in response:
                call_id = response['call_id']
                # Wait a bit for background processing
                import time
                time.sleep(3)
                
                # Test GET single call
                self.test_api_endpoint('GET', f'/calls/{call_id}', test_name="Get Single Call")
                return call_id
        return None

    def test_booking_functionality(self, lead_id: str = None, agent_id: str = None):
        """Test booking functionality"""
        print("\n🔍 Testing Booking Functionality...")
        
        if lead_id and agent_id:
            # First need to qualify the lead
            update_data = {"status": "qualified"}
            self.test_api_endpoint('PUT', f'/leads/{lead_id}', data=update_data, 
                                 test_name="Qualify Lead for Booking")
            
            # Test booking
            booking_data = {
                "lead_id": lead_id,
                "agent_id": agent_id
            }
            success, response = self.test_api_endpoint('POST', '/bookings', data=booking_data, 
                                                     test_name="Book Meeting")
            
            if success:
                if 'calendly_link' in response:
                    self.log_result("Booking - Calendly Link", True)
                else:
                    self.log_result("Booking - Calendly Link", False, "Missing calendly_link in response")

    def test_settings(self):
        """Test settings functionality"""
        print("\n🔍 Testing Settings...")
        
        # Test GET settings
        success, settings = self.test_api_endpoint('GET', '/settings', test_name="Get Settings")
        
        if success:
            # Test UPDATE settings
            update_data = {"qualification_threshold": 70, "min_interest_level": 7}
            self.test_api_endpoint('PUT', '/settings', data=update_data, test_name="Update Settings")

    def test_twitter_mock(self):
        """Test Twitter/X mock endpoint"""
        print("\n🔍 Testing Twitter Mock...")
        
        url = "/twitter/search?query=credit card processing"
        success, response = self.test_api_endpoint('POST', url, test_name="Twitter Mock Search")
        
        if success:
            if 'results' in response and 'note' in response:
                self.log_result("Twitter Mock - Response Format", True)
            else:
                self.log_result("Twitter Mock - Response Format", False, "Missing 'results' or 'note' fields")

    def run_all_tests(self):
        """Run all test scenarios"""
        print(f"🚀 Starting API Tests for AI Cold Calling Machine")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print("="*60)
        
        # Test basic connectivity
        self.test_api_endpoint('GET', '/', test_name="API Root Connectivity")
        
        # Test dashboard
        self.test_dashboard_stats()
        
        # Test lead discovery
        self.test_lead_discovery()
        
        # Test CRUD operations
        lead_id = self.test_leads_crud()
        campaign_id = self.test_campaigns_crud() 
        agent_id = self.test_agents_crud()
        
        # Test calls (need lead and campaign)
        if lead_id and campaign_id:
            # Re-create lead since it was deleted in CRUD test
            lead_data = {
                "business_name": "Test Call Business",
                "phone": "+1-555-0789",
                "source": "manual"
            }
            success, created_lead = self.test_api_endpoint('POST', '/leads', 200, lead_data, 
                                                         "Create Lead for Call Test")
            if success:
                new_lead_id = created_lead['id']
                call_id = self.test_calls_functionality(new_lead_id, campaign_id)
                
                # Test booking
                if agent_id:
                    self.test_booking_functionality(new_lead_id, agent_id)
        
        # Test settings
        self.test_settings()
        
        # Test mocked integrations
        self.test_twitter_mock()
        
        # Print summary
        return self.print_summary()

    def print_summary(self):
        """Print test execution summary"""
        print("\n" + "="*60)
        print(f"📊 Test Summary")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failures)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0.0%")
        
        if self.failures:
            print(f"\n❌ Failed Tests:")
            for failure in self.failures:
                print(f"  • {failure['test']}: {failure['details']}")
        
        print("="*60)
        return len(self.failures) == 0

def main():
    """Main test execution"""
    tester = APITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())