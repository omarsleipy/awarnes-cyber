"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from config import get_settings
from core.database import AsyncSessionLocal, Base, engine
from core.security import hash_password
from modules.auth.router import router as auth_router
from modules.courses.router import router as courses_router
from modules.exams.router import router as exams_router
from modules.phishing.models import PhishingCampaign
from modules.phishing.router import router as phishing_router
from modules.settings.router import router as settings_router
from modules.users.models import User
from modules.users.router import router as users_router


async def _seed() -> None:
    async with AsyncSessionLocal() as session:
        r = await session.execute(select(User).limit(1))
        if r.scalar_one_or_none() is None:
            for email, name, role in (
                ("admin@corp.com", "Admin User", "admin"),
                ("john@corp.com", "John Doe", "trainee"),
            ):
                session.add(
                    User(
                        email=email,
                        name=name,
                        role=role,
                        department="IT" if role == "admin" else "Finance",
                        hashed_password=hash_password("password"),
                    )
                )
            await session.commit()

        r2 = await session.execute(select(PhishingCampaign).limit(1))
        if r2.scalar_one_or_none() is None:
            for name, template, dept, sent, clk, rep, status in (
                ("Q1 Finance Dept Phish", "Password Reset", "Finance", 245, 31, 189, "completed"),
                ("IT Password Reset Lure", "IT Alert", "IT", 180, 12, 152, "completed"),
                ("CEO Gift Card Scam", "Executive Request", "All", 320, 48, 201, "active"),
                ("HR Benefits Update", "Benefits Notice", "HR", 0, 0, 0, "draft"),
            ):
                session.add(
                    PhishingCampaign(
                        name=name,
                        template=template,
                        target_dept=dept,
                        sent=sent,
                        clicked=clk,
                        reported=rep,
                        status=status,
                    )
                )
            await session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed()
    yield
    await engine.dispose()


app = FastAPI(title="CyberAware API", lifespan=lifespan)

origins = [o.strip() for o in get_settings().CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api"
app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{api_prefix}/users", tags=["users"])
app.include_router(courses_router, prefix=f"{api_prefix}/courses", tags=["courses"])
app.include_router(exams_router, prefix=f"{api_prefix}/exams", tags=["exams"])
app.include_router(settings_router, prefix=f"{api_prefix}/settings", tags=["settings"])
app.include_router(phishing_router, prefix=f"{api_prefix}/phishing", tags=["phishing"])


@app.get("/health")
async def health():
    return {"status": "ok"}
