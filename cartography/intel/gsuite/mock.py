"""
Mock implementations for GSuite API testing.
This module provides mock classes that simulate Google Admin API responses.
"""

class MockAdmin:
    """Mock implementation of Google Admin API client."""
    def users(self):
        """Return a mock user resource."""
        return MockUserResource()
    
    def groups(self):
        """Return a mock group resource."""
        return MockGroupResource()
    
    def members(self):
        """Return a mock member resource."""
        return MockMemberResource()

class MockUserResource:
    """Handles user-related API endpoints."""
    def list(self, customer=None, maxResults=None, orderBy=None):
        """Mock the list method for users."""
        return MockRequest("users")
    
    def list_next(self, request, resp):
        """Mock pagination for users - return None to indicate no more pages."""
        return None

class MockGroupResource:
    """Handles group-related API endpoints."""
    def list(self, customer=None, maxResults=None, orderBy=None):
        """Mock the list method for groups."""
        return MockRequest("groups")
    
    def list_next(self, request, resp):
        """Mock pagination for groups."""
        return None

class MockMemberResource:
    """Handles group membership API endpoints."""
    def list(self, groupKey=None, maxResults=None):
        """Mock the list method for group members."""
        return MockRequest("members", groupKey)
    
    def list_next(self, request, resp):
        """Mock pagination for members."""
        return None

class MockRequest:
    """Mock implementation of API request object."""
    def __init__(self, request_type, key=None):
        """Initialize with request type and optional key."""
        self.request_type = request_type
        self.key = key
    
    def execute(self, num_retries=None):
        """Mock the execute method with support for num_retries parameter."""
        if self.request_type == "users":
            return {
                "users": [
                    {
                        "id": "mock123456",
                        "primaryEmail": "test.user@example.com",
                        "name": {
                            "givenName": "Test",
                            "familyName": "User",
                            "fullName": "Test User"
                        },
                        "isAdmin": False,
                        "isDelegatedAdmin": False,
                        "creationTime": "2023-01-01T00:00:00.000Z",
                        "lastLoginTime": "2023-01-02T00:00:00.000Z"
                    },
                    {
                        "id": "mock234567",
                        "primaryEmail": "admin.user@example.com",
                        "name": {
                            "givenName": "Admin",
                            "familyName": "User",
                            "fullName": "Admin User"
                        },
                        "isAdmin": True,
                        "isDelegatedAdmin": True,
                        "creationTime": "2023-01-01T00:00:00.000Z",
                        "lastLoginTime": "2023-01-02T00:00:00.000Z"
                    }
                ]
            }
        elif self.request_type == "groups":
            return {
                "groups": [
                    {
                        "id": "mockgroup123",
                        "email": "test-group@example.com",
                        "name": "Test Group",
                        "description": "A test group for GSuite integration testing",
                        "adminCreated": True
                    }
                ]
            }
        elif self.request_type == "members":
            return {
                "members": [
                    {
                        "id": "mock123456",
                        "email": "test.user@example.com",
                        "role": "MEMBER",
                        "type": "USER"
                    }
                ]
            }
        return {}
