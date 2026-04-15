"""LDAP authentication provider."""
from __future__ import annotations

from ldap3 import ALL, Connection, Server


def _safe_account(email_or_username: str) -> str:
    return email_or_username.split("@")[0].strip()


def authenticate_ldap_user(
    *,
    server_host: str,
    server_port: int,
    use_ssl: bool,
    bind_dn: str,
    bind_password: str,
    base_dn: str,
    user_filter: str,
    login: str,
    password: str,
) -> bool:
    """Validate LDAP credentials by searching user DN then binding as user."""
    if not server_host or not base_dn or not login or not password:
        return False

    account = _safe_account(login)
    server = Server(server_host, port=server_port, use_ssl=use_ssl, get_info=ALL)

    try:
        if bind_dn:
            admin_conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)
        else:
            admin_conn = Connection(server, auto_bind=True)
    except Exception:
        return False

    search_filter = (
        f"(&{user_filter}"
        f"(|(mail={login})(userPrincipalName={login})(sAMAccountName={account})))"
    )
    try:
        ok = admin_conn.search(
            search_base=base_dn,
            search_filter=search_filter,
            attributes=["distinguishedName"],
        )
        if not ok or not admin_conn.entries:
            return False
        user_dn = str(admin_conn.entries[0].entry_dn)
    except Exception:
        return False

    try:
        user_conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        return bool(user_conn.bound)
    except Exception:
        return False

