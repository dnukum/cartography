# In api.py, add this import at the top
from cartography.intel.o365.schema import O365UserSchema, O365GroupSchema, O365OrganizationalUnitSchema
from cartography.intel.o365.schema import O365GroupSchema
from cartography.intel.o365.schema import O365OrganizationalUnitSchema
from cartography.intel.o365.schema import O365UserToGroupRelSchema
from cartography.util.neo4j import load_relationship_data

def load_o365_groups(neo4j_session, groups: List[Dict], update_tag: str) -> None:
    """
    Load O365 groups into Neo4j using the defined schema.
    :param neo4j_session: Neo4j session object
    :param groups: List of transformed group objects
    :param update_tag: Update tag for marking nodes
    """
    group_data = [{
        'id': group.get('id'),
        'displayName': group.get('displayName'),
        'description': group.get('description'),
        'mail': group.get('mail'),
        'lastupdated': update_tag,
    } for group in groups]

    load_node_data(
        neo4j_session,
        O365GroupSchema(),
        group_data,
        lastupdated_tag=update_tag,
    )

def load_o365_users(neo4j_session, users: List[Dict], update_tag: str) -> None:
    """
    Load O365 users into Neo4j using the defined schema.
    """
    # Convert user data to the format expected by add_node_data
    user_data = [{
        'id': user.get('id'),
        'displayName': user.get('displayName'),
        'userPrincipalName': user.get('userPrincipalName'),
        'mail': user.get('mail'),
        'jobTitle': user.get('jobTitle'),
        'department': user.get('department'),
        'lastupdated': update_tag
    } for user in users]
    
    # Use the schema to load data
    cartography.util.neo4j.load_node_data(
        neo4j_session,
        O365UserSchema(),
        user_data,
        lastupdated_tag=update_tag
    )

def load_o365_organizational_units(neo4j_session, ous: List[Dict], update_tag: str) -> None:
    """
    Load O365 organizational units into Neo4j using the defined schema.
    :param neo4j_session: Neo4j session object
    :param ous: List of transformed OU objects
    :param update_tag: Update tag for marking nodes
    """
    ou_data = [{
        'id': ou.get('id'),
        'displayName': ou.get('displayName'),
        'description': ou.get('description'),
        'lastupdated': update_tag,
    } for ou in ous]

    load_node_data(
        neo4j_session,
        O365OrganizationalUnitSchema(),
        ou_data,
        lastupdated_tag=update_tag,
    )  
     
def load_user_group_relationships(neo4j_session, relationships: List[Dict], update_tag: str) -> None:
    """
    Load relationships between users and groups into Neo4j using the defined schema.
    :param neo4j_session: Neo4j session object
    :param relationships: List of relationship objects (user_id → group_id)
    :param update_tag: Update tag for marking relationships
    """
    relationship_data = [{
        'source_id': rel['user_id'],
        'target_id': rel['group_id'],
        'lastupdated': update_tag,
    } for rel in relationships]

    load_relationship_data(
        neo4j_session,
        O365UserToGroupRelSchema(),
        relationship_data,
        lastupdated_tag=update_tag,
    )

    logger.info(f"Loaded {len(users)} O365 users into Neo4j")

# cartography/intel/o365/o365.py
"""
API functions for syncing O365 data to Cartography.
"""
import logging
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger(__name__)

# Constants for Microsoft Graph API
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

def get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Authenticate with Microsoft Graph API and retrieve an access token.
    
    :param tenant_id: The O365 tenant ID
    :param client_id: The application client ID
    :param client_secret: The application client secret
    :return: Access token for Microsoft Graph API
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error authenticating with Microsoft Graph API: {e}")
        raise

# Data retrieval functions
def get_o365_users(access_token: str) -> List[Dict]:
    """
    Retrieve all users from Microsoft Graph API.
    
    :param access_token: Valid access token for Microsoft Graph API
    :return: List of user objects
    """
    users = []
    next_link = f"{GRAPH_API_BASE_URL}/users?$select=id,displayName,userPrincipalName,mail,jobTitle,department"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    while next_link:
        try:
            response = requests.get(next_link, headers=headers)
            response.raise_for_status()
            data = response.json()
            users.extend(data.get("value", []))
            next_link = data.get("@odata.nextLink")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving users from Microsoft Graph API: {e}")
            raise
            
    logger.info(f"Retrieved {len(users)} users from O365")
    return users

def get_o365_groups(access_token: str) -> List[Dict]:
    """
    Retrieve all groups from Microsoft Graph API.
    
    :param access_token: Valid access token for Microsoft Graph API
    :return: List of group objects
    """
    groups = []
    next_link = f"{GRAPH_API_BASE_URL}/groups?$select=id,displayName,description,mail"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    while next_link:
        try:
            response = requests.get(next_link, headers=headers)
            response.raise_for_status()
            data = response.json()
            groups.extend(data.get("value", []))
            next_link = data.get("@odata.nextLink")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving groups from Microsoft Graph API: {e}")
            raise
            
    logger.info(f"Retrieved {len(groups)} groups from O365")
    return groups

def get_o365_group_members(access_token: str, group_id: str) -> List[Dict]:
    """
    Retrieve members of a specific group from Microsoft Graph API.
    
    :param access_token: Valid access token for Microsoft Graph API
    :param group_id: ID of the group
    :return: List of member objects
    """
    members = []
    next_link = f"{GRAPH_API_BASE_URL}/groups/{group_id}/members?$select=id"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    while next_link:
        try:
            response = requests.get(next_link, headers=headers)
            response.raise_for_status()
            data = response.json()
            members.extend(data.get("value", []))
            next_link = data.get("@odata.nextLink")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving group members from Microsoft Graph API: {e}")
            raise
            
    return members

def get_o365_organizational_units(access_token: str) -> List[Dict]:
    """
    Retrieve all administrative units (as organizational units) from Microsoft Graph API.
    
    Note: Microsoft Graph API doesn't have a direct concept of OUs like GSuite.
    Administrative Units in Azure AD are the closest equivalent.
    
    :param access_token: Valid access token for Microsoft Graph API
    :return: List of administrative unit objects
    """
    admin_units = []
    next_link = f"{GRAPH_API_BASE_URL}/directory/administrativeUnits?$select=id,displayName,description"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(next_link, headers=headers)
        # If 404 or other status, it might mean the API isn't available in this tenant
        if response.status_code == 404:
            logger.warning("Administrative Units API endpoint not found. This may not be available in your tenant.")
            return []
        
        response.raise_for_status()
        data = response.json()
        admin_units.extend(data.get("value", []))
        next_link = data.get("@odata.nextLink")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving administrative units from Microsoft Graph API: {e}")
        # Return empty list instead of raising, as this isn't critical functionality
        return []
            
    logger.info(f"Retrieved {len(admin_units)} administrative units from O365")
    return admin_units

# Data transformation functions
def transform_users(users: List[Dict]) -> List[Dict]:
    """
    Transform user data into a format suitable for Neo4j.
    
    :param users: List of user objects from Microsoft Graph API
    :return: List of transformed user objects
    """
    transformed_users = []
    
    for user in users:
        transformed_users.append({
            "id": user.get("id"),
            "displayName": user.get("displayName"),
            "userPrincipalName": user.get("userPrincipalName"),
            "mail": user.get("mail"),
            "jobTitle": user.get("jobTitle"),
            "department": user.get("department"),
        })
    
    return transformed_users

def transform_groups(groups: List[Dict]) -> List[Dict]:
    """
    Transform group data into a format suitable for Neo4j.
    
    :param groups: List of group objects from Microsoft Graph API
    :return: List of transformed group objects
    """
    transformed_groups = []
    
    for group in groups:
        transformed_groups.append({
            "id": group.get("id"),
            "displayName": group.get("displayName"),
            "description": group.get("description"),
            "mail": group.get("mail"),
        })
    
    return transformed_groups

def transform_ous(admin_units: List[Dict]) -> List[Dict]:
    """
    Transform administrative unit data into organizational unit format for Neo4j.
    
    :param admin_units: List of administrative unit objects from Microsoft Graph API
    :return: List of transformed OU objects
    """
    transformed_ous = []
    
    for unit in admin_units:
        transformed_ous.append({
            "id": unit.get("id"),
            "displayName": unit.get("displayName"),
            "description": unit.get("description"),
        })
    
    return transformed_ous

# Data loading functions
def load_o365_users(neo4j_session, users: List[Dict], update_tag: str) -> None:
    """
    Load O365 users into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param users: List of transformed user objects
    :param update_tag: Update tag for marking nodes
    """
    query = """
    UNWIND $Users as user
    MERGE (u:O365User {id: user.id})
    ON CREATE SET u.firstseen = timestamp()
    SET u.displayName = user.displayName,
        u.userPrincipalName = user.userPrincipalName,
        u.mail = user.mail,
        u.jobTitle = user.jobTitle,
        u.department = user.department,
        u.lastupdated = $update_tag
    """
    
    neo4j_session.run(
        query,
        Users=users,
        update_tag=update_tag
    )
    
    logger.info(f"Loaded {len(users)} O365 users into Neo4j")

def load_o365_groups(neo4j_session, groups: List[Dict], update_tag: str) -> None:
    """
    Load O365 groups into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param groups: List of transformed group objects
    :param update_tag: Update tag for marking nodes
    """
    query = """
    UNWIND $Groups as group
    MERGE (g:O365Group {id: group.id})
    ON CREATE SET g.firstseen = timestamp()
    SET g.displayName = group.displayName,
        g.description = group.description,
        g.mail = group.mail,
        g.lastupdated = $update_tag
    """
    
    neo4j_session.run(
        query,
        Groups=groups,
        update_tag=update_tag
    )
    
    logger.info(f"Loaded {len(groups)} O365 groups into Neo4j")

def load_o365_organizational_units(neo4j_session, ous: List[Dict], update_tag: str) -> None:
    """
    Load O365 organizational units (administrative units) into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param ous: List of transformed OU objects
    :param update_tag: Update tag for marking nodes
    """
    if not ous:
        logger.info("No O365 organizational units to load")
        return
    
    query = """
    UNWIND $OUs as ou
    MERGE (o:O365OrganizationalUnit {id: ou.id})
    ON CREATE SET o.firstseen = timestamp()
    SET o.displayName = ou.displayName,
        o.description = ou.description,
        o.lastupdated = $update_tag
    """
    
    neo4j_session.run(
        query,
        OUs=ous,
        update_tag=update_tag
    )
    
    logger.info(f"Loaded {len(ous)} O365 organizational units into Neo4j")

def load_o365_user_group_relationships(neo4j_session, access_token: str, groups: List[Dict], update_tag: str) -> None:
    """
    Load relationships between O365 users and groups into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param access_token: Valid access token for Microsoft Graph API
    :param groups: List of group objects
    :param update_tag: Update tag for marking relationships
    """
    for group in groups:
        group_id = group.get("id")
        if not group_id:
            continue
            
        members = get_o365_group_members(access_token, group_id)
        
        if not members:
            continue
            
        query = """
        MATCH (g:O365Group {id: $group_id})
        UNWIND $members AS member
        MATCH (u:O365User {id: member.id})
        MERGE (u)-[r:MEMBER_OF]->(g)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        """
        
        neo4j_session.run(
            query,
            group_id=group_id,
            members=members,
            update_tag=update_tag
        )
        
        logger.info(f"Loaded {len(members)} members for group {group.get('displayName', group_id)}")

def load_o365_ou_relationships(neo4j_session, access_token: str, ous: List[Dict], update_tag: str) -> None:
    """
    Load relationships between O365 OUs and users/groups into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param access_token: Valid access token for Microsoft Graph API
    :param ous: List of OU objects
    :param update_tag: Update tag for marking relationships
    """
    if not ous:
        logger.info("No O365 OU relationships to load")
        return
    
    # Implementation depends on specific requirements
    # This is a placeholder for future implementation
    pass

# Cleanup functions
def run_cleanup_jobs(neo4j_session, update_tag: str, common_job_parameters: Dict) -> None:
    """
    Run cleanup jobs to remove stale O365 data from Neo4j.
    
    :param neo4j_session: Neo4j session
    :param update_tag: Update tag for identifying stale data
    :param common_job_parameters: Common job parameters
    """
    run_cleanup_job(
        neo4j_session,
        "MATCH (u:O365User) WHERE u.lastupdated <> $update_tag DETACH DELETE u",
        {"update_tag": update_tag}
    )
    
    run_cleanup_job(
        neo4j_session,
        "MATCH (g:O365Group) WHERE g.lastupdated <> $update_tag DETACH DELETE g",
        {"update_tag": update_tag}
    )
    
    run_cleanup_job(
        neo4j_session,
        "MATCH (o:O365OrganizationalUnit) WHERE o.lastupdated <> $update_tag DETACH DELETE o",
        {"update_tag": update_tag}
    )
    
    run_cleanup_job(
        neo4j_session,
        "MATCH (:O365User)-[r:MEMBER_OF]->(:O365Group) WHERE r.lastupdated <> $update_tag DELETE r",
        {"update_tag": update_tag}
    )
    
    logger.info("Completed O365 cleanup jobs")

def run_cleanup_job(neo4j_session, query: str, parameters: Dict) -> None:
    """
    Helper function to run a cleanup job.
    
    :param neo4j_session: Neo4j session
    :param query: Cleanup query
    :param parameters: Query parameters
    """
    result = neo4j_session.run(query, parameters)
    summary = result.consume()
    logger.info(f"Cleanup job removed {summary.counters.nodes_deleted} nodes and {summary.counters.relationships_deleted} relationships")

# Main sync functions
def sync_o365_users(neo4j_session, tenant_id: str, client_id: str, client_secret: str, update_tag: str, common_job_parameters: Dict) -> List[Dict]:
    """
    Sync O365 users to Neo4j.
    
    :param neo4j_session: Neo4j session
    :param tenant_id: O365 tenant ID
    :param client_id: Application client ID
    :param client_secret: Application client secret
    :param update_tag: Update tag for marking nodes
    :param common_job_parameters: Common job parameters
    :return: List of transformed user objects
    """
    logger.info("Syncing O365 users")
    
    access_token = get_access_token(tenant_id, client_id, client_secret)
    users = get_o365_users(access_token)
    transformed_users = transform_users(users)
    load_o365_users(neo4j_session, transformed_users, update_tag)
    
    return transformed_users

def sync_o365_groups(neo4j_session, tenant_id: str, client_id: str, client_secret: str, update_tag: str, common_job_parameters: Dict) -> List[Dict]:
    """
    Sync O365 groups to Neo4j.
    
    :param neo4j_session: Neo4j session
    :param tenant_id: O365 tenant ID
    :param client_id: Application client ID
    :param client_secret: Application client secret
    :param update_tag: Update tag for marking nodes
    :param common_job_parameters: Common job parameters
    :return: List of transformed group objects
    """
    logger.info("Syncing O365 groups")
    
    access_token = get_access_token(tenant_id, client_id, client_secret)
    groups = get_o365_groups(access_token)
    transformed_groups = transform_groups(groups)
    load_o365_groups(neo4j_session, transformed_groups, update_tag)
    
    return transformed_groups

def sync_o365_organizational_units(neo4j_session, tenant_id: str, client_id: str, client_secret: str, update_tag: str, common_job_parameters: Dict) -> List[Dict]:
    """
    Sync O365 organizational units to Neo4j.
    
    :param neo4j_session: Neo4j session
    :param tenant_id: O365 tenant ID
    :param client_id: Application client ID
    :param client_secret: Application client secret
    :param update_tag: Update tag for marking nodes
    :param common_job_parameters: Common job parameters
    :return: List of transformed OU objects
    """
    logger.info("Syncing O365 organizational units")
    
    access_token = get_access_token(tenant_id, client_id, client_secret)
    admin_units = get_o365_organizational_units(access_token)
    transformed_ous = transform_ous(admin_units)
    load_o365_organizational_units(neo4j_session, transformed_ous, update_tag)
    
    return transformed_ous

def sync_o365_user_group_relationships(neo4j_session, tenant_id: str, client_id: str, client_secret: str, groups: List[Dict], update_tag: str, common_job_parameters: Dict) -> None:
    """
    Sync relationships between O365 users and groups.
    
    :param neo4j_session: Neo4j session
    :param tenant_id: O365 tenant ID
    :param client_id: Application client ID
    :param client_secret: Application client secret
    :param groups: List of group objects
    :param update_tag: Update tag for marking relationships
    :param common_job_parameters: Common job parameters
    """
    logger.info("Syncing O365 user-group relationships")
    
    access_token = get_access_token(tenant_id, client_id, client_secret)
    load_o365_user_group_relationships(neo4j_session, access_token, groups, update_tag)

def sync_o365_ou_relationships(neo4j_session, tenant_id: str, client_id: str, client_secret: str, ous: List[Dict], update_tag: str, common_job_parameters: Dict) -> None:
    """
    Sync relationships between O365 OUs and other entities.
    
    :param neo4j_session: Neo4j session
    :param tenant_id: O365 tenant ID
    :param client_id: Application client ID
    :param client_secret: Application client secret
    :param ous: List of OU objects
    :param update_tag: Update tag for marking relationships
    :param common_job_parameters: Common job parameters
    """
    if not ous:
        logger.info("No O365 OUs to sync relationships for")
        return
    
    logger.info("Syncing O365 OU relationships")
    
    access_token = get_access_token(tenant_id, client_id, client_secret)
    load_o365_ou_relationships(neo4j_session, access_token, ous, update_tag)
