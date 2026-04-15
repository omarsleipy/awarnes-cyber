"""Schemas for organization administration."""
from pydantic import BaseModel


class OrganizationCreateRequest(BaseModel):
    name: str


class OrganizationAuthUpdateRequest(BaseModel):
    authMode: str  # local | ldap


class OrganizationStatusUpdateRequest(BaseModel):
    status: str  # active | suspended


class OrganizationLdapConfigRequest(BaseModel):
    ldapServer: str = ""
    ldapPort: int = 389
    ldapBaseDn: str = ""
    ldapBindDn: str = ""
    ldapBindPassword: str = ""
    ldapUserFilter: str = "(objectClass=person)"
    ldapUseSsl: bool = False


class OrganizationOut(BaseModel):
    id: str
    name: str
    status: str
    authMode: str
    ldapServer: str = ""
    ldapPort: int = 389
    ldapBaseDn: str = ""
    ldapBindDn: str = ""
    ldapUserFilter: str = "(objectClass=person)"
    ldapUseSsl: bool = False

