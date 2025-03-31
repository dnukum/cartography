import unittest
import requests
from neo4j import GraphDatabase
from .test_msft365_basic import TestMsft365BasicFunctionality

class TestMsft365Neo4jSync(TestMsft365BasicFunctionality):
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
        # Get Msft365 data
        self.test_can_authenticate_with_graph_api()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        users = requests.get("https://graph.microsoft.com/v1.0/users?$top=5", headers=headers).json().get("value", [])
        
        # Write to Neo4j
        with GraphDatabase.driver(self.neo4j_uri,
                                auth=(self.neo4j_user, self.neo4j_password)) as driver:
            with driver.session() as session:
                # Clear existing test data (FIXED)
                session.run("MATCH (u:Msft365User) DETACH DELETE u")  # 👈 Changed to DETACH DELETE
                
                # Insert users
                for user in users:
                    session.run(
                        "CREATE (u:Msft365User {id: $user_id, name: $name, email: $email})",
                        user_id=user['id'],
                        name=user.get('displayName'),
                        email=user.get('userPrincipalName')
                    )
                
                # Verify sync
                result = session.run("MATCH (u:Msft365User) RETURN count(u) AS count")
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
                session.run("MATCH (g:Msft365Group) DETACH DELETE g")  # 👈 Changed to DETACH DELETE
                
                # Create group nodes
                for group in groups[:1]:
                    session.run(
                        "MERGE (g:Msft365Group {id: $id}) "
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
                        """MATCH (u:Msft365User {id: $user_id}), (g:Msft365Group {id: $group_id})
                        MERGE (u)-[:MEMBER_OF]->(g)""",
                        user_id=member['id'],
                        group_id=group_id
                    )
                
                # Verify relationships
                result = session.run(
                    "MATCH (u:Msft365User)-[:MEMBER_OF]->(g:Msft365Group) RETURN count(*) AS count"
                )
                self.assertGreater(result.single()['count'], 0)

    # End-to-end test of device data sync
    def test_device_sync_to_neo4j(self):
        
        # Get device data
        devices = self.test_can_fetch_devices()
        if not devices:
            self.skipTest("No devices available for testing")

        with GraphDatabase.driver(self.neo4j_uri,
                                auth=(self.neo4j_user, self.neo4j_password)) as driver:
            with driver.session() as session:
                # Clear existing device data
                session.run("MATCH (d:Msft365Device) DETACH DELETE d")
                
                # Insert devices
                for device in devices:
                    session.run(
                        """CREATE (d:Msft365Device {
                            id: $id, 
                            displayName: $name,
                            operatingSystem: $os,
                            deviceOwnership: $ownership
                        })""",
                        id=device['id'],
                        name=device.get('displayName'),
                        os=device.get('operatingSystem'),
                        ownership=device.get('deviceOwnership')
                    )

                # Verify sync
                result = session.run("MATCH (d:Msft365Device) RETURN count(d) AS count")
                self.assertEqual(result.single()['count'], len(devices))

    #  """Validate device ownership relationships in Neo4j"""
    def test_device_ownership_relationships(self):
       
        # Get test data
        devices = self.test_can_fetch_devices()
        if not devices:
            self.skipTest("No devices available for testing")
            
        device_id = devices[0]['id']
        headers = {"Authorization": f"Bearer {self.access_token}"}
        owners = requests.get(
            f"https://graph.microsoft.com/v1.0/devices/{device_id}/registeredOwners",
            headers=headers
        ).json().get('value', [])

        with GraphDatabase.driver(self.neo4j_uri,
                                auth=(self.neo4j_user, self.neo4j_password)) as driver:
            with driver.session() as session:
                # Clear existing relationships
                session.run("MATCH ()-[r:OWNED_BY]->() DELETE r")
                
                # Create relationships
                for owner in owners:
                    session.run(
                        """MATCH (u:Msft365User {id: $user_id}), (d:Msft365Device {id: $device_id})
                        MERGE (u)-[:OWNED_BY]->(d)""",
                        user_id=owner['id'],
                        device_id=device_id
                    )

                # Verify relationships
                result = session.run(
                    "MATCH (u:Msft365User)-[:OWNED_BY]->(d:Msft365Device) RETURN count(*) AS count"
                )
                self.assertGreater(result.single()['count'], 0)

            

        
