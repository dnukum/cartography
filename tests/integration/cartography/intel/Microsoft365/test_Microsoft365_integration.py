import unittest
import requests
from neo4j import GraphDatabase
from .test_Microsoft365_basic import TestO365BasicFunctionality

class TestO365Neo4jSync(TestO365BasicFunctionality):
    def setUp(self):
        super().setUp()
        if not hasattr(self, 'access_token'):
            self.test_can_authenticate_with_graph_api()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def test_user_sync_to_neo4j(self):
        """End-to-end test of user data sync"""
        # Get O365 data
        self.test_can_authenticate_with_graph_api()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        users = requests.get("https://graph.microsoft.com/v1.0/users?$top=5", headers=headers).json().get("value", [])
        
        # Write to Neo4j
        with GraphDatabase.driver(self.neo4j_uri,
                                auth=(self.neo4j_user, self.neo4j_password)) as driver:
            with driver.session() as session:
                # Clear existing test data (FIXED)
                session.run("MATCH (u:O365User) DETACH DELETE u")  # 👈 Changed to DETACH DELETE
                
                # Insert users
                for user in users:
                    session.run(
                        "CREATE (u:O365User {id: $user_id, name: $name, email: $email})",
                        user_id=user['id'],
                        name=user.get('displayName'),
                        email=user.get('userPrincipalName')
                    )
                
                # Verify sync
                result = session.run("MATCH (u:O365User) RETURN count(u) AS count")
                self.assertEqual(result.single()['count'], len(users))


    def test_group_membership_sync(self):
        """Validate group membership relationships in Neo4j"""
        # Get test data
        groups = super().test_can_fetch_groups()
        group_id = groups[0].get('id')
        members = super().test_can_fetch_group_members()
        
        # Sync groups to Neo4j first
        with GraphDatabase.driver(self.neo4j_uri,
                                auth=(self.neo4j_user, self.neo4j_password)) as driver:
            with driver.session() as session:
                # Clear existing groups (FIXED)
                session.run("MATCH (g:O365Group) DETACH DELETE g")  # 👈 Changed to DETACH DELETE
                
                # Create group nodes
                for group in groups[:1]:
                    session.run(
                        "MERGE (g:O365Group {id: $id}) "
                        "SET g.name = $name",
                        id=group['id'],
                        name=group.get('displayName')
                    )
        
        # Create relationships
        with GraphDatabase.driver(self.neo4j_uri,
                                auth=(self.neo4j_user, self.neo4j_password)) as driver:
            with driver.session() as session:
                # Clear existing relationships
                session.run("MATCH ()-[r:MEMBER_OF]->() DELETE r")
                
                # Create relationships
                for member in members:
                    session.run(
                        """MATCH (u:O365User {id: $user_id}), (g:O365Group {id: $group_id})
                        MERGE (u)-[:MEMBER_OF]->(g)""",
                        user_id=member['id'],
                        group_id=group_id
                    )
                
                # Verify relationships
                result = session.run(
                    "MATCH (u:O365User)-[:MEMBER_OF]->(g:O365Group) RETURN count(*) AS count"
                )
                self.assertGreater(result.single()['count'], 0)

        

    
