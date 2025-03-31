"""
Microsoft365 schema definitions for Cartography.
"""
from dataclasses import dataclass, field
from typing import List

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema

# ==============================
# Microsoft365 USER SCHEMA
# ==============================
@dataclass(frozen=True)
class Msft365UserProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The user id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the user'))
    userPrincipalName: PropertyRef = field(default=PropertyRef('userPrincipalName', 'The user principal name (UPN) of the user'))
    mail: PropertyRef = field(default=PropertyRef('mail', 'The primary email address of the user'))
    jobTitle: PropertyRef = field(default=PropertyRef('jobTitle', 'The job title of the user', optional=True))
    department: PropertyRef = field(default=PropertyRef('department', 'The department that the user works in', optional=True))


@dataclass(frozen=True)
class Msft365UserToGroupRelProperties(CartographyRelProperties):
    firstseen: PropertyRef = field(default=PropertyRef('firstseen', 'The time when this relationship was first seen'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))


@dataclass(frozen=True)
class Msft365UserToGroupRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365Group'
    rel_label: str = 'MEMBER_OF'
    direction: str = 'OUTGOING'
    properties: Msft365UserToGroupRelProperties = field(default=Msft365UserToGroupRelProperties())


@dataclass(frozen=True)
class Msft365UserSchema(CartographyNodeSchema):
    label: str = 'Msft365User'
    properties: Msft365UserProperties = field(default=Msft365UserProperties())
    relationships: List[Msft365UserToGroupRelSchema] = field(
        default_factory=lambda: [
            Msft365UserToGroupRelSchema(),
        ]
    )


# ==============================
# Msft365 GROUP SCHEMA
# ==============================
@dataclass(frozen=True)
class Msft365GroupProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The group id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the group'))
    description: PropertyRef = field(default=PropertyRef('description', 'The description of the group', optional=True))
    mail: PropertyRef = field(default=PropertyRef('mail', 'The email address of the group', optional=True))


@dataclass(frozen=True)
class Msft365GroupSchema(CartographyNodeSchema):
    label: str = 'Msft365Group'
    properties: Msft365GroupProperties = field(default=Msft365GroupProperties())


# ==============================
# Msft365 ORGANIZATIONAL UNIT SCHEMA
# ==============================
@dataclass(frozen=True)
class Msft365OrganizationalUnitProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The organizational unit id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the organizational unit'))
    description: PropertyRef = field(default=PropertyRef('description', 'The description of the organizational unit', optional=True))


@dataclass(frozen=True)
class Msft365OUToUserRelProperties(CartographyRelProperties):
    firstseen: PropertyRef = field(default=PropertyRef('firstseen', 'The time when this relationship was first seen'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))


@dataclass(frozen=True)
class Msft365OUToUserRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365User'
    rel_label: str = 'CONTAINS'
    direction: str = 'OUTGOING'
    properties: Msft365OUToUserRelProperties = field(default=Msft365OUToUserRelProperties())


@dataclass(frozen=True)
class Msft365OUToGroupRelProperties(CartographyRelProperties):
    firstseen: PropertyRef = field(default=PropertyRef('firstseen', 'The time when this relationship was first seen'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))


@dataclass(frozen=True)
class Msft365OUToGroupRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365Group'
    rel_label: str = 'CONTAINS'
    direction: str = 'OUTGOING'
    properties: Msft365OUToGroupRelProperties = field(default=Msft365OUToGroupRelProperties())


@dataclass(frozen=True)
class Msft365OrganizationalUnitSchema(CartographyNodeSchema):
    label: str = 'Msft365OrganizationalUnit'
    properties: Msft365OrganizationalUnitProperties = field(default=Msft365OrganizationalUnitProperties())
    relationships: List[CartographyRelSchema] = field(
        default_factory=lambda: [
            Msft365OUToUserRelSchema(),
            Msft365OUToGroupRelSchema(),
        ]
    )


# ==============================
# Msft365 DEVICE SCHEMA
# ==============================

@dataclass(frozen=True)
class Msft365DeviceProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The device id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the device'))
    operatingSystem: PropertyRef = field(default=PropertyRef('operatingSystem', 'The operating system of the device'))
    deviceOwnership: PropertyRef = field(default=PropertyRef('deviceOwnership', 'Ownership type (Corporate/Personal)'))
    approximateLastSignInDateTime: PropertyRef = field(
        default=PropertyRef('approximateLastSignInDateTime', 'Last sign-in timestamp', optional=True)
    )
    isCompliant: PropertyRef = field(
        default=PropertyRef('isCompliant', 'Compliance status', optional=True)
    )

@dataclass(frozen=True)
class Msft365DeviceOwnerRelProperties(CartographyRelProperties):
    firstseen: PropertyRef = field(default=PropertyRef('firstseen', 'The time when this relationship was first seen'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))

@dataclass(frozen=True)
class Msft365DeviceOwnerRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365User'
    rel_label: str = 'OWNED_BY'
    direction: str = 'OUTGOING'
    properties: Msft365DeviceOwnerRelProperties = field(default=Msft365DeviceOwnerRelProperties())

@dataclass(frozen=True)
class Msft365DeviceSchema(CartographyNodeSchema):
    label: str = 'Msft365Device'
    properties: Msft365DeviceProperties = field(default=Msft365DeviceProperties())
    relationships: List[CartographyRelSchema] = field(
        default_factory=lambda: [
            Msft365DeviceOwnerRelSchema(),
        ]
    )
