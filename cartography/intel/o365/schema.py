"""
O365 schema definitions for Cartography.
"""
from dataclasses import dataclass, field
from typing import List

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema

# ==============================
# O365 USER SCHEMA
# ==============================
@dataclass(frozen=True)
class O365UserProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The user id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the user'))
    userPrincipalName: PropertyRef = field(default=PropertyRef('userPrincipalName', 'The user principal name (UPN) of the user'))
    mail: PropertyRef = field(default=PropertyRef('mail', 'The primary email address of the user'))
    jobTitle: PropertyRef = field(default=PropertyRef('jobTitle', 'The job title of the user', optional=True))
    department: PropertyRef = field(default=PropertyRef('department', 'The department that the user works in', optional=True))


@dataclass(frozen=True)
class O365UserToGroupRelProperties(CartographyRelProperties):
    firstseen: PropertyRef = field(default=PropertyRef('firstseen', 'The time when this relationship was first seen'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))


@dataclass(frozen=True)
class O365UserToGroupRelSchema(CartographyRelSchema):
    target_node_label: str = 'O365Group'
    rel_label: str = 'MEMBER_OF'
    direction: str = 'OUTGOING'
    properties: O365UserToGroupRelProperties = field(default=O365UserToGroupRelProperties())


@dataclass(frozen=True)
class O365UserSchema(CartographyNodeSchema):
    label: str = 'O365User'
    properties: O365UserProperties = field(default=O365UserProperties())
    relationships: List[O365UserToGroupRelSchema] = field(
        default_factory=lambda: [
            O365UserToGroupRelSchema(),
        ]
    )


# ==============================
# O365 GROUP SCHEMA
# ==============================
@dataclass(frozen=True)
class O365GroupProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The group id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the group'))
    description: PropertyRef = field(default=PropertyRef('description', 'The description of the group', optional=True))
    mail: PropertyRef = field(default=PropertyRef('mail', 'The email address of the group', optional=True))


@dataclass(frozen=True)
class O365GroupSchema(CartographyNodeSchema):
    label: str = 'O365Group'
    properties: O365GroupProperties = field(default=O365GroupProperties())


# ==============================
# O365 ORGANIZATIONAL UNIT SCHEMA
# ==============================
@dataclass(frozen=True)
class O365OrganizationalUnitProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The organizational unit id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the organizational unit'))
    description: PropertyRef = field(default=PropertyRef('description', 'The description of the organizational unit', optional=True))


@dataclass(frozen=True)
class O365OUToUserRelProperties(CartographyRelProperties):
    firstseen: PropertyRef = field(default=PropertyRef('firstseen', 'The time when this relationship was first seen'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))


@dataclass(frozen=True)
class O365OUToUserRelSchema(CartographyRelSchema):
    target_node_label: str = 'O365User'
    rel_label: str = 'CONTAINS'
    direction: str = 'OUTGOING'
    properties: O365OUToUserRelProperties = field(default=O365OUToUserRelProperties())


@dataclass(frozen=True)
class O365OUToGroupRelProperties(CartographyRelProperties):
    firstseen: PropertyRef = field(default=PropertyRef('firstseen', 'The time when this relationship was first seen'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))


@dataclass(frozen=True)
class O365OUToGroupRelSchema(CartographyRelSchema):
    target_node_label: str = 'O365Group'
    rel_label: str = 'CONTAINS'
    direction: str = 'OUTGOING'
    properties: O365OUToGroupRelProperties = field(default=O365OUToGroupRelProperties())


@dataclass(frozen=True)
class O365OrganizationalUnitSchema(CartographyNodeSchema):
    label: str = 'O365OrganizationalUnit'
    properties: O365OrganizationalUnitProperties = field(default=O365OrganizationalUnitProperties())
    relationships: List[CartographyRelSchema] = field(
        default_factory=lambda: [
            O365OUToUserRelSchema(),
            O365OUToGroupRelSchema(),
        ]
    )
