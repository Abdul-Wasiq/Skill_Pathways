# SETUP REQUIRED — Read Before Running

This file lists every step that requires a human decision or external
credentials. The codebase will not run correctly until these are done.

---

## 1. PostgreSQL Database (pgAdmin4)

- [ ] Open pgAdmin4 and create a new database — e.g. `career_platform`.
- [ ] Note the host (usually `localhost`), port (usually `5432` or `5433`),
      username, and password for that server.
- [ ] Run these three SQL files against it, IN ORDER:
      1. `database/schema.sql`
      2. `database/schema_social.sql` (posts, connections, notifications, reports)
      3. `database/seed.sql`
      (Query Tool in pgAdmin4, or `psql -U <user> -d <dbname> -f <file>`.)

## 2. Backend Environment Variables

- [ ] `cd backend && cp .env.example .env`
- [ ] Fill in `DATABASE_USER` and `DATABASE_PASSWORD` with your real pgAdmin4
      credentials from step 1.
- [ ] Generate a JWT secret and put it in `JWT_SECRET`:
      ```
      python3 -c "import secrets; print(secrets.token_urlsafe(64))"
      ```
- [ ] Decide on an AI provider (see step 3) and fill in `AI_API_KEY` / `AI_MODEL`.

## 3. AI Provider API Key

- [ ] Choose a provider. Groq is recommended for a fast, low-cost start:
      https://console.groq.com/keys
- [ ] Set in `backend/.env`:
      ```
      AI_PROVIDER=groq
      AI_BASE_URL=https://api.groq.com/openai/v1
      AI_API_KEY=<your real key>
      AI_MODEL=llama-3.3-70b-versatile
      ```
- [ ] If you skip this, the app still runs — AI match *scores* are always
      computed by the rule-based engine regardless, but the natural-language
      explanation will use a simpler fallback template instead of an
      LLM-generated sentence.

## 4. CORS Configuration

- [ ] If you serve the frontend from something other than
      `http://localhost:5500` / `http://127.0.0.1:5500`, add that origin to
      `CORS_ORIGINS` in `backend/.env` (comma-separated).

## 5. Frontend API Base URL

- [ ] If your backend does not run at `http://127.0.0.1:8000`, edit
      `API_BASE_URL` at the top of `frontend/js/api.js`.

## 6. Things Deliberately Left Undone (Future Work)

- [ ] No admin account is seeded — the `admin` role exists in the schema and
      auth system but no admin UI/endpoints exist yet.
- [ ] No file storage is configured for resumes or profile pictures (resume
      upload/parsing is not yet implemented — see README §6).
- [ ] No production deployment configuration (Docker, reverse proxy, HTTPS,
      managed Postgres) is included — this is a local-development setup only.
- [ ] No automated test suite exists yet.

---

Once steps 1–5 are complete, follow README.md section 3 to run the backend
and frontend.
