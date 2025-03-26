# cartography/intel/o365/__init__.py
"""
O365 integration module for Cartography.
This module synchronizes users, groups, and organizational units from Microsoft 365
into the Cartography graph database.
"""

import logging
from typing import Dict, List, Any, Optional

# Import functions from api.py 
from cartography.intel.o365.api import (
    sync_o365_users,
    sync_o365_groups,
    sync_o365_organizational_units,
    sync_o365_user_group_relationships,
    sync_o365_ou_relationships,
    run_cleanup_jobs
)

# Define module-level constants
O365_USER_LABEL = "O365User"
O365_GROUP_LABEL = "O365Group"
O365_OU_LABEL = "O365OrganizationalUnit"

O365_MEMBER_OF_RELATIONSHIP = "MEMBER_OF"
O365_PART_OF_RELATIONSHIP = "PART_OF"

logger = logging.getLogger(__name__)

def start_o365_ingestion(
    neo4j_session,
    config: Dict,
    common_job_parameters: Dict,
) -> None:
    """
    Starts the O365 data ingestion process.
    
    :param neo4j_session: The Neo4j session.
    :param config: A dictionary containing necessary O365 credentials and configuration.
    :param common_job_parameters: Parameters to be passed to each Neo4j job.
    :return: None
    """
    tenant_id = config.get('o365_tenant_id')
    client_id = config.get('o365_client_id')
    client_secret = config.get('o365_client_secret')
    
    if not (tenant_id and client_id and client_secret):
        logger.warning(
            "O365 credentials are not configured correctly. Make sure o365_tenant_id, "
            "o365_client_id, and o365_client_secret are set in the config."
        )
        return
    
    logger.info("Starting O365 sync")
    
    # Get update tag
    update_tag = common_job_parameters.get('UPDATE_TAG')
    
    try:
        # Sync users from O365
        logger.info("Syncing O365 users")
        users = sync_o365_users(
            neo4j_session, tenant_id, client_id, client_secret, update_tag, common_job_parameters
        )
        
        # Sync groups from O365
        logger.info("Syncing O365 groups")
        groups = sync_o365_groups(
            neo4j_session, tenant_id, client_id, client_secret, update_tag, common_job_parameters
        )
        
        # Sync organizational units from O365
        logger.info("Syncing O365 organizational units")
        ous = sync_o365_organizational_units(
            neo4j_session, tenant_id, client_id, client_secret, update_tag, common_job_parameters
        )
        
        # Sync relationships between users and groups
        logger.info("Syncing O365 user-group relationships")
        sync_o365_user_group_relationships(
            neo4j_session, users, groups, update_tag, common_job_parameters
        )
        
        # Sync relationships between OUs and other entities
        logger.info("Syncing O365 organizational unit relationships")
        sync_o365_ou_relationships(
            neo4j_session, ous, update_tag, common_job_parameters
        )
        
        # Run cleanup to remove stale data
        logger.info("Running O365 cleanup jobs")
        run_cleanup_jobs(
            neo4j_session, update_tag, common_job_parameters
        )
        
        logger.info("O365 sync complete")
        
    except Exception as e:
        logger.error(f"Error syncing data from O365: {e}")
        raise
