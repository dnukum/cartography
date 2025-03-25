import unittest
import os
import requests
from neo4j import GraphDatabase

class TestO365BasicFunctionality(unittest.TestCase):
    def setUp(self):
        # Get credentials from environment variables
        self.tenant_id = os.environ.get('O365_TENANT_ID')
        self.client_id = os.environ.get('O365_CLIENT_ID')
        self.client_secret = os.environ.get('O365_CLIENT_SECRET')
        
        # Neo4j connection parameters - use container name instead of localhost
        self.neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
        self.neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
        
        # Skip test if credentials are not available
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            self.skipTest("O365 credentials not available")
        
        # Print credential info for debugging (mask sensitive parts)
        print(f"Testing with tenant ID: {self.tenant_id[:4]}...{self.tenant_id[-4:]}")
        print(f"Client ID: {self.client_id[:4]}...{self.client_id[-4:]}")
        print(f"Secret length: {len(self.client_secret)} chars")
    
    def test_can_authenticate_with_graph_api(self):
        """Test that we can authenticate with Microsoft Graph API."""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            "client_id": self.client_id,
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        
        response = requests.post(url, data=payload)
        print(f"Auth response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Auth error: {response.text}")
        
        self.assertEqual(response.status_code, 200, msg=f"Authentication failed: {response.text}")
        self.assertIn("access_token", response.json())
        
        # Store token for other tests
        self.access_token = response.json().get("access_token")
        return self.access_token
