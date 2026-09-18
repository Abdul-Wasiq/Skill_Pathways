# CareerBridge — AI-Powered Career, Scholarship & Internship Platform

A career and opportunity-discovery platform where users build profiles, browse
jobs/internships/scholarships, and get AI-powered, **explainable** compatibility
scores against each opportunity. Organizations post opportunities and manage
applicants.

This is an original platform with its own name, data model, and UI — it does
not copy any existing product's branding, design, or source code.

> **Status**: Auth, profiles, opportunities, applications, AI opportunity
> matching, posts/social feed, personalized feed ranking, connections/
> networking, notifications, global search, AI Resume-to-Profile, AI Career
> Assistant, AI Job Description Analyzer, AI Post Assistant, and an admin
> panel are all implemented and tested end-to-end against a live PostgreSQL
> database. Messaging and an automated test suite are not built — see
> "What's Not Built Yet" below.

---

## 1. Architecture

```
career-platform/
  backend/
    app/
      main.py              FastAPI app, CORS, error handlers
      config.py             Env-var driven settings (no hard-coded secrets)
      database.py           psycopg2 connection pool
      api/                  Route handlers (auth, profiles, opportunities, ai)
      schemas/               Pydantic request/response + AI-output validation
      services/              Business logic (matching engine, AI service, profile completion)
      repositories/          All raw SQL, fully parameterized
      utils/                  Security (JWT, bcrypt) and FastAPI auth dependencies
    requirements.txt
    .env.example
  database/
    schema.sql               Full relational schema
    seed.sql                 Safe fictional demo data
  frontend/
    index.html
    pages/                   login, signup, home (dashboard), profile,
                             opportunities, opportunity-detail
    css/style.css
    js/api.js                 Shared fetch client + auth/session handling
  README.md
  SETUP_REQUIRED.md
```

**AI Service Abstraction (`services/ai_service.py`)**: talks to *any*
OpenAI-compatible `/chat/completions` endpoint. Switching providers (Groq →
OpenAI → anything else) is a `.env` change, not a code change.

**AI Matching Engine (`services/matching_service.py`)**: the match score is
**never** just "ask an LLM for a percentage." It's computed by transparent,
configurable weights:

```
Skills:            40%
Education:         20%
Experience:        15%
Eligibility:        15%
Career interests:  10%
```

The AI provider is only used to turn the already-computed numbers into a
readable explanation — and even that output is validated (Pydantic schema)
and sanitized against overconfident claims ("definitely eligible" etc.) before
being shown. If the AI provider is unreachable or unconfigured, the feature
still works using a template-based fallback explanation.

---

## 2. Technology Stack

- **Backend**: Python, FastAPI, Pydantic, psycopg2, PostgreSQL, JWT (PyJWT),
  passlib/bcrypt, python-dotenv, Uvicorn
- **Frontend**: HTML5, CSS3, vanilla JavaScript, Fetch API
- **AI**: any OpenAI-compatible provider (Groq recommended — fast + generous free tier)

---

## 3. Installation

### 3.1 Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` — see `SETUP_REQUIRED.md` for exactly what to fill in.

### 3.2 Database (pgAdmin4 / local PostgreSQL)

1. In pgAdmin4, create a database (e.g. `career_platform`).
2. Run the schema and seed files against it. From a terminal with `psql`
   available (or via pgAdmin's Query Tool, pasting each file's contents):

```bash
psql -U your_postgres_user -d career_platform -f database/schema.sql
psql -U your_postgres_user -d career_platform -f database/seed.sql
```

3. Update `backend/.env` with the same host/port/db name/user/password you
   used in pgAdmin4.

### 3.3 Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger API docs, and
`http://127.0.0.1:8000/api/health` to confirm it's alive.

### 3.4 Run the frontend

The frontend is static HTML/JS — no build step. Simplest option: use VS
Code's "Live Server" extension on `frontend/pages/login.html`, or:

```bash
cd frontend
python3 -m http.server 5500
```

Then visit `http://127.0.0.1:5500/pages/login.html`.

**Important**: `frontend/js/api.js` hardcodes `API_BASE_URL =
"http://127.0.0.1:8000"`. If your backend runs elsewhere, update that line.
Also make sure `CORS_ORIGINS` in `backend/.env` includes whatever origin your
frontend is served from.

---

## 4. AI Configuration

This project talks to any OpenAI-compatible chat completions API.

**Groq (recommended for free/fast testing):**
1. Get a key at https://console.groq.com/keys
2. In `backend/.env`:
   ```
   AI_PROVIDER=groq
   AI_BASE_URL=https://api.groq.com/openai/v1
   AI_API_KEY=your_actual_groq_key
   AI_MODEL=llama-3.3-70b-versatile
   ```

**OpenAI:**
   ```
   AI_PROVIDER=openai
   AI_BASE_URL=https://api.openai.com/v1
   AI_API_KEY=your_actual_openai_key
   AI_MODEL=gpt-4o-mini
   ```

If this is left unconfigured, AI match scores still compute correctly — only
the natural-language explanation falls back to a simpler template instead of
an LLM-generated sentence.

---

## 5. API Overview

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

GET    /api/profile
PUT    /api/profile
POST   /api/profile/skills
DELETE /api/profile/skills/{skill_id}
POST   /api/profile/education
POST   /api/profile/experience
POST   /api/profile/projects
POST   /api/profile/certifications

POST   /api/organizations
GET    /api/organizations/{org_id}
GET    /api/organizations/{org_id}/opportunities
POST   /api/organizations/{org_id}/opportunities

GET    /api/opportunities
GET    /api/opportunities/{id}
PUT    /api/opportunities/{id}
DELETE /api/opportunities/{id}
POST   /api/opportunities/{id}/apply
POST   /api/opportunities/{id}/save
DELETE /api/opportunities/{id}/save

GET    /api/applications
GET    /api/opportunities/{id}/applications
PUT    /api/applications/{id}/status
GET    /api/saved-opportunities

POST   /api/ai/opportunity-match/{opportunity_id}   # runs a fresh analysis
GET    /api/ai/opportunity-match/{opportunity_id}   # fetches cached analysis
POST   /api/ai/resume-to-profile                    # upload PDF/DOCX -> preview
POST   /api/ai/resume-to-profile/confirm             # save reviewed data
POST   /api/ai/career-assistant                      # profile-aware Q&A
POST   /api/ai/job-analyzer                          # paste a JD -> analysis + match
POST   /api/ai/post-assistant                        # writing help for posts

POST   /api/posts
GET    /api/posts
GET    /api/posts/{id}
PUT    /api/posts/{id}
DELETE /api/posts/{id}
POST   /api/posts/{id}/like
DELETE /api/posts/{id}/like
POST   /api/posts/{id}/comments
GET    /api/posts/{id}/comments
POST   /api/posts/{id}/share
POST   /api/posts/{id}/save
GET    /api/posts/saved/me
POST   /api/posts/reports

GET    /api/feed                                     # personalized ranked feed

POST   /api/connections/{target_user_id}
PUT    /api/connections/{id}/accept
PUT    /api/connections/{id}/reject
DELETE /api/connections/{id}
GET    /api/connections
GET    /api/connections/pending

GET    /api/notifications
GET    /api/notifications/unread-count
PUT    /api/notifications/{id}/read
PUT    /api/notifications/read-all

GET    /api/search?q=...

GET    /api/admin/stats
GET    /api/admin/users
PUT    /api/admin/users/{id}/suspend
PUT    /api/admin/users/{id}/reactivate
GET    /api/admin/reports
PUT    /api/admin/reports/{id}
GET    /api/admin/organizations
PUT    /api/admin/organizations/{id}/verify
DELETE /api/admin/posts/{id}
DELETE /api/admin/opportunities/{id}
```

Full interactive docs at `/docs` once the backend is running.

**Note on running the social/admin schema**: in addition to `schema.sql` and
`seed.sql`, run `database/schema_social.sql` once (adds posts, connections,
notifications, reports, feed_interactions tables) — see SETUP_REQUIRED.md.

---

## 6. What's Not Built Yet

- Messaging (spec marks this as optional/future work anyway)
- Automated test suite (pytest-based backend tests)
- Production deployment configuration (Docker, HTTPS, managed Postgres)
- Full-text search (current search uses simple ILIKE matching — fine for a
  demo/small dataset, would need `tsvector`/external search index at scale)

---

## 7. Security Notes

- Passwords are hashed with bcrypt — never stored in plaintext.
- All SQL is parameterized (see `repositories/`) — no string-built queries.
- JWTs are signed with `JWT_SECRET` from `.env` — never hard-coded.
- The AI API key lives only in the backend `.env` — never exposed to the browser.
- CORS origins are explicit and configurable, not wildcarded in production use.

## 8. Troubleshooting

- **"Unable to reach the server"** in the frontend → backend isn't running, or
  `API_BASE_URL` in `js/api.js` doesn't match where it's actually running.
- **CORS errors in the browser console** → add your frontend's origin to
  `CORS_ORIGINS` in `backend/.env` and restart the backend.
- **`RuntimeError: Missing required environment variable`** on startup → you
  haven't filled in `backend/.env` — copy it from `.env.example` first.
- **AI match works but explanation looks templated/plain** → `AI_API_KEY` is
  missing or invalid; the app is using its fallback path, which is expected
  behavior, not a bug.
