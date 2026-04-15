"""Organization (tenant) model."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active | suspended
    auth_mode: Mapped[str] = mapped_column(String(32), default="local")  # local | ldap

    # Optional per-organization LDAP configuration
    ldap_server: Mapped[str] = mapped_column(String(255), default="")
    ldap_port: Mapped[int] = mapped_column(Integer, default=389)
    ldap_base_dn: Mapped[str] = mapped_column(String(500), default="")
    ldap_bind_dn: Mapped[str] = mapped_column(String(500), default="")
    ldap_bind_password: Mapped[str] = mapped_column(String(500), default="")
    ldap_user_filter: Mapped[str] = mapped_column(String(255), default="(objectClass=person)")
    ldap_use_ssl: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

