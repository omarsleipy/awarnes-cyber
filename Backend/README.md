# CyberAware Backend (FastAPI)

Production-ready modular monolith: auth, users, exams (with proctoring), phishing, monitoring, courses, settings.

## Setup

1. **Python 3.10+** and create a virtualenv:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **PostgreSQL:** Create a database and set `.env` (copy from `.env.example`):
   ```env
   DB_URL=postgresql+asyncpg://user:password@localhost:5432/cyberaware
   JWT_SECRET=your-long-secret
   CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
   ```

4. **Run:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

- **Health:** `GET http://localhost:8000/health`
- **API docs:** `http://localhost:8000/docs`
- **Default users (after first run):** `admin@corp.com` / `password`, `john@corp.com` / `password`

## Frontend connection

The React app in `/Frontend/shieldwise-academy` uses `VITE_API_URL` (default `http://localhost:8000/api`). Start the backend on port 8000 and the frontend on 8080; login and all API calls will use the backend.

## Module layout

- **auth** — Login, JWT
- **users** — CRUD, CSV bulk upload, SSO/LDAP stubs
- **exams** — Create exam, per-user passwords (SMTP), validate password, questions, submit, proctoring (3 violations = disqualified), certificates
- **phishing** — Campaigns, track open/click, metrics
- **monitoring** — Log suspicious activities
- **courses** — List courses, update progress
- **settings** — SMTP/LDAP get/save/test stubs
