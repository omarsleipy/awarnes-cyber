import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from modules.settings.models import Setting


async def get(session: AsyncSession, key: str) -> str | None:
    r = await session.execute(select(Setting).where(Setting.key == key))
    s = r.scalar_one_or_none()
    return s.value if s else None


async def set_val(session: AsyncSession, key: str, value: str) -> None:
    r = await session.execute(select(Setting).where(Setting.key == key))
    s = r.scalar_one_or_none()
    if s:
        s.value = value
    else:
        session.add(Setting(key=key, value=value))
    await session.flush()
