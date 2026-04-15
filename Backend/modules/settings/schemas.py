from pydantic import BaseModel


class SmtpConfig(BaseModel):
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    encryption: str = "TLS"
    fromName: str = ""
    fromEmail: str = ""


class LdapConfig(BaseModel):
    server: str = ""
    port: int = 389
    baseDn: str = ""
    bindDn: str = ""
    bindPassword: str = ""
    userFilter: str = "(objectClass=person)"
    useSsl: bool = False


class SmtpTestRequest(BaseModel):
    toEmail: str | None = None
