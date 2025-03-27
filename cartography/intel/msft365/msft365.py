"""
API functions for syncing Msft365 data to Cartography using schema-based loading.
"""

import logging
from typing import Dict, List, Optional, Any
import requests
from cartography.util.neo4j import load_node_data, load_relationship_data, GraphJob
from cartography.intel.msft365.schema import (
    Msft365UserSchema,
    Msft365GroupSchema,
    Msft365OrganizationalUnitSchema,
    Msft365UserToGroupRelSchema,
    Msft365OUToUserRelSchema,
    Msft365OUToGroupRelSchema
)

logger = logging.getLogger(__name__)
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

# ==================================================================
# Authentication and Data Retrieval
# ==================================================================

def get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Authenticate with Microsoft Graph API and retrieve access token.
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication failed: {e}")
        raise

def paginated_api_call(access_token: str, endpoint: str, params: str = "") -> List[Dict]:
    """
    Generic paginated API call handler for Microsoft Graph.
    """
    results = []
    next_link = f"{GRAPH_API_BASE_URL}/{endpoint}?{params}"
    headers = {"Authorization": f"Bearer {access_token}"}

    while next_link:
        try:
            response = requests.get(next_link, headers=headers)
            response.raise_for_status()
            data = response.json()
            results.extend(data.get("value", []))
            next_link = data.get("@odata.nextLink")
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            raise
    
    return results

# ==================================================================
# Data Collection Functions
# ==================================================================

def get_Msft365_users(access_token: str) -> List[Dict]:
    """Retrieve all users from Microsoft Graph API."""
    return paginated_api_call(
        access_token,
        "users",
        "$select=id,displayName,userPrincipalName,mail,jobTitle,department"
    )

def get_Msft365_groups(access_token: str) -> List[Dict]:
    """Retrieve all groups from Microsoft Graph API."""
    return paginated_api_call(
        access_token,
        "groups",
        "$select=id,displayName,description,mail"
    )

def get_Msft365_organizational_units(access_token: str) -> List[Dict]:
    """Retrieve administrative units from Microsoft Graph API."""
    try:
        return paginated_api_call(
            access_token,
            "directory/administrativeUnits",
            "$select=id,displayName,description"
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning("Administrative Units API not available in this tenant")
            return []
        raise

def get_group_members(access_token: str, group_id: str) -> List[Dict]:
    """Retrieve members of a specific group."""
    return paginated_api_call(
        access_token,
        f"groups/{group_id}/members",
        "$select=id"
    )

# ==================================================================
# Data Transformation
# ==================================================================

def transform_users(raw_users: List[Dict]) -> List[Dict]:
    """Transform user data for schema-based loading."""
    return [{
        "id": u.get("id"),
        "displayName": u.get("displayName"),
        "userPrincipalName": u.get("userPrincipalName"),
        "mail": u.get("mail"),
        "jobTitle": u.get("jobTitle"),
        "department": u.get("department")
    } for u in raw_users]

def transform_groups(raw_groups: List[Dict]) -> List[Dict]:
    """Transform group data for schema-based loading."""
    return [{
        "id": g.get("id"),
        "displayName": g.get("displayName"),
        "description": g.get("description"),
        "mail": g.get("mail")
    } for g in raw_groups]

def transform_ous(raw_units: List[Dict]) -> List[Dict]:
    """Transform organizational unit data for schema-based loading."""
    return [{
        "id": u.get("id"),
        "displayName": u.get("displayName"),
        "description": u.get("description")
    } for u in raw_units]

# ==================================================================
# Schema-Based Loading Functions
# ==================================================================

def load_Msft365_users(neo4j_session, users: List[Dict], update_tag: str) -> None:
    """Load users using Msft365UserSchema."""
    user_data = [{**u, "lastupdated": update_tag} for u in users]
    load_node_data(neo4j_session, Msft365UserSchema(), user_data, update_tag)
    logger.info(f"Loaded {len(user_data)} users")

def load_Msft365_groups(neo4j_session, groups: List[Dict], update_tag: str) -> None:
    """Load groups using Msft365GroupSchema."""
    group_data = [{**g, "lastupdated": update_tag} for g in groups]
    load_node_data(neo4j_session, Msft365GroupSchema(), group_data, update_tag)
    logger.info(f"Loaded {len(group_data)} groups")

def load_Msft365_organizational_units(neo4j_session, ous: List[Dict], update_tag: str) -> None:
    """Load OUs using Msft365OrganizationalUnitSchema."""
    if not ous:
        return
    ou_data = [{**ou, "lastupdated": update_tag} for ou in ous]
    load_node_data(neo4j_session, Msft365OrganizationalUnitSchema(), ou_data, update_tag)
    logger.info(f"Loaded {len(ou_data)} organizational units")

def load_user_group_relationships(neo4j_session, groups: List[Dict], access_token: str, update_tag: str) -> None:
    """Load user-group relationships using schema."""
    relationships = []
    for group in groups:
        members = get_group_members(access_token, group["id"])
        relationships.extend({
            "source_id": member["id"],
            "target_id": group["id"],
            "lastupdated": update_tag
        } for member in members)
    
    if relationships:
        load_relationship_data(
            neo4j_session,
            Msft365UserToGroupRelSchema(),
            relationships,
            update_tag
        )
        logger.info(f"Loaded {len(relationships)} user-group relationships")

def load_ou_relationships(neo4j_session, ous: List[Dict], access_token: str, update_tag: str) -> None:
    """Load OU relationships using schema."""
    # Implementation depends on specific OU relationship requirements
    # Placeholder for future expansion
    pass

# ==================================================================
# Cleanup Operations
# ==================================================================

def run_cleanup_jobs(neo4j_session, common_job_parameters: Dict) -> None:
    """Schema-based cleanup using GraphJob."""
    logger.info("Running Msft365 cleanup")
    
    cleanup_jobs = [
        GraphJob.from_node_schema(Msft365UserSchema(), common_job_parameters),
        GraphJob.from_node_schema(Msft365GroupSchema(), common_job_parameters),
        GraphJob.from_node_schema(Msft365OrganizationalUnitSchema(), common_job_parameters)
    ]

    for job in cleanup_jobs:
        job.run(neo4j_session)
    
    logger.info("Completed Msft365 cleanup")

# ==================================================================
# Sync Orchestration
# ==================================================================

def sync_Msft365_users(neo4j_session, tenant_id: str, client_id: str, client_secret: str, update_tag: str, _: Dict) -> List[Dict]:
    """Full sync workflow for Msft365 users."""
    logger.info("Syncing Msft365 users")
    access_token = get_access_token(tenant_id, client_id, client_secret)
    raw_users = get_Msft365_users(access_token)
    transformed = transform_users(raw_users)
    load_Msft365_users(neo4j_session, transformed, update_tag)
    return transformed

def sync_Msft365_groups(neo4j_session, tenant_id: str, client_id: str, client_secret: str, update_tag: str, _: Dict) -> List[Dict]:
    """Full sync workflow for Msft365 groups."""
    logger.info("Syncing Msft365 groups")
    access_token = get_access_token(tenant_id, client_id, client_secret)
    raw_groups = get_Msft365_groups(access_token)
    transformed = transform_groups(raw_groups)
    load_Msft365_groups(neo4j_session, transformed, update_tag)
    return transformed

def sync_Msft365_organizational_units(neo4j_session, tenant_id: str, client_id: str, client_secret: str, update_tag: str, _: Dict) -> List[Dict]:
    """Full sync workflow for Msft365 organizational units."""
    logger.info("Syncing Msft365 organizational units")
    access_token = get_access_token(tenant_id, client_id, client_secret)
    raw_units = get_Msft365_organizational_units(access_token)
    transformed = transform_ous(raw_units)
    load_Msft365_organizational_units(neo4j_session, transformed, update_tag)
    return transformed

def sync_Msft365_user_group_relationships(neo4j_session, tenant_id: str, client_id: str, client_secret: str, groups: List[Dict], update_tag: str, _: Dict) -> None:
    """Sync user-group relationships."""
    logger.info("Syncing user-group relationships")
    access_token = get_access_token(tenant_id, client_id, client_secret)
    load_user_group_relationships(neo4j_session, groups, access_token, update_tag)

def sync_Msft365_ou_relationships(neo4j_session, tenant_id: str, client_id: str, client_secret: str, ous: List[Dict], update_tag: str, _: Dict) -> None:
    """Sync OU relationships."""
    if not ous:
        return
    logger.info("Syncing OU relationships")
    access_token = get_access_token(tenant_id, client_id, client_secret)
    load_ou_relationships(neo4j_session, ous, access_token, update_tag)
