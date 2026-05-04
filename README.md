# SkillBridge Attendance API

A backend REST API for a state-level skilling programme attendance management system. Built with FastAPI, PostgreSQL (Neon), and deployed on  Render.

---

## Live API

**Base URL:** ` https://skillbridge-attendance-api-pckr.onrender.com`

> If the service is sleeping ( Render free tier), the first request might take 10–15 seconds to respond. Just retry once.

---

## Local Setup

Assumes Python 3.11+ and pip are installed. Nothing else.

```bash
git clone https://github.com/nehachoudhary0731/SkillBridge-Attendance-API.git
cd SkillBridge-Attendance-API

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the root

```
DATABASE_URL=postgresql://user:password@host/dbname
SECRET_KEY=some-random-secret-here
MONITORING_API_KEY=monitor-secret-key-123
```

Run migrations and seed the database:

```bash
alembic upgrade head
python -m src.seed
```

Start the server:

```bash
uvicorn src.main:app --reload
```

API will be at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

---

## Test Accounts

These are created by the seed script:

| Role | Email | Password |
|---|---|---|
| Student | student01@skillbridge.com | student@1234 |
| Trainer | rahul@skillbridge.com | trainer@1234 |
| Institution | delhi@skillbridge.com | delhi@1234 |
| Programme Manager | pm@skillbridge.com | pm@1234 |
| Monitoring Officer | monitor@skillbridge.com | monitor@1234 |

---

## curl Examples

### Auth

**Signup:**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com", "password": "pass1234", "role": "student"}'
```

**Login (save the token):**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student01@skillbridge.com", "password": "student@1234"}'
```

Set the token in a variable for convenience:
```bash
TOKEN="<paste access_token here>"
```

---

### Batches

**Create a batch (Trainer or Institution):**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/batches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Batch", "institution_id": "bbb61611-ae8e-44e3-b20e-b8955f3b44b5"}'
```

**Generate invite token (Trainer):**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/batches/fc1ffa12-e4d5-48cd-8b28-96a318d37b63/invite \
  -H "Authorization: Bearer $TOKEN"
```

**Join a batch (Student):**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/batches/join \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "<invite_token>"}'
```

**Batch summary (Institution):**
```bash
curl https://skillbridge-attendance-api-pckr.onrender.com/batches/fc1ffa12-e4d5-48cd-8b28-96a318d37b63/summary \
  -H "Authorization: Bearer $TOKEN"
```

---

### Sessions

**Create a session (Trainer):**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": "fc1ffa12-e4d5-48cd-8b28-96a318d37b63",
    "title": "Python Basics",
    "date": "2026-05-10",
    "start_time": "09:00:00",
    "end_time": "11:00:00"
  }'
```

**View session attendance (Trainer):**
```bash
curl https://skillbridge-attendance-api-pckr.onrender.com/sessions/eb779220-f53a-468d-b950-bc1bfd18ac55/attendance \
  -H "Authorization: Bearer $TOKEN"
```

---

### Attendance

**Mark attendance (Student):**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/attendance/mark \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "eb779220-f53a-468d-b950-bc1bfd18ac55", "status": "present"}'
```

---

### Programme & Institution Summaries

**Programme-wide summary (Programme Manager):**
```bash
curl https://skillbridge-attendance-api-pckr.onrender.com/programme/summary \
  -H "Authorization: Bearer $TOKEN"
```

**Institution summary (Programme Manager):**
```bash
curl https://skillbridge-attendance-api-pckr.onrender.com/institutions/bbb61611-ae8e-44e3-b20e-b8955f3b44b5/summary \
  -H "Authorization: Bearer $TOKEN"
```

---

### Monitoring Officer — Two-Token Flow

The Monitoring Officer uses a two-step auth flow. First login normally, then exchange for a scoped monitoring token.

**Step 1: Login as monitoring officer**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "monitor@skillbridge.com", "password": "monitor@1234"}'

# Save the access_token as $MO_TOKEN
```

**Step 2: Get a scoped monitoring token**
```bash
curl -X POST https://skillbridge-attendance-api-pckr.onrender.com/auth/monitoring-token \
  -H "Authorization: Bearer $MO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "monitor-secret-key-123"}'

# Save the monitoring_token as $MON_TOKEN
```

**Step 3: Hit the monitoring endpoint**
```bash
curl https://skillbridge-attendance-api-pckr.onrender.com/monitoring/attendance \
  -H "Authorization: Bearer $MON_TOKEN"
```

Any non-GET request to `/monitoring/attendance` will return 405.

---

## JWT Payload Structure

**Standard token (all roles except monitoring):**
```json
{
  "sub": "<user_id>",
  "role": "student | trainer | institution | programme_manager | monitoring_officer",
  "iat": 1714900000,
  "exp": 1714986400
}
```
Expiry: 24 hours.

**Monitoring scoped token:**
```json
{
  "sub": "<user_id>",
  "role": "monitoring_officer",
  "token_type": "monitoring",
  "scope": "monitoring_readonly",
  "iat": 1714900000,
  "exp": 1714903600
}
```
Expiry: 1 hour. Only accepted by `/monitoring/*` endpoints, which check `token_type == "monitoring"` before proceeding.

---

## Schema Decisions

**`batch_trainers` (many-to-many):** A batch can have multiple trainers and a trainer can run multiple batches. A join table was the obvious choice here — trying to store trainer IDs as an array on the batch row would have made queries messy and relationships harder to enforce at the DB level.

**`batch_invites`:** Rather than giving trainers a way to directly add students (which would require knowing their email upfront), invite tokens felt more realistic — a trainer generates a link, shares it however they want, and the student redeems it. Tokens are single-use and expire after 7 days. The `used` flag is flipped atomically on join so the same token can't be reused.

**Dual-token for Monitoring Officer:** The monitoring officer's read-only constraint needed to be enforced at the token level, not just the role level. A regular JWT with `role: monitoring_officer` would still allow someone to swap it in on a write endpoint that doesn't check `token_type`. The scoped token forces a second authentication step and only works on monitoring endpoints. It also expires faster (1 hour vs 24 hours) since monitoring access is a deliberate act, not a persistent session.

**Token rotation / revocation in a real deployment:** Right now tokens are stateless — once issued, there's no way to invalidate them before expiry. In production I'd keep a small Redis store of revoked token JTIs, checked on every request. Refresh tokens would handle the rotation side: short-lived access tokens (15 min), longer refresh tokens stored server-side with the ability to revoke the refresh token chain. For the monitoring token specifically, tying it to a session ID and letting admins invalidate sessions would be enough.

**One security issue in the current implementation:** The `MONITORING_API_KEY` is hardcoded as a fallback string in `security.py` (`"monitor-secret-key-123"`). If someone reads the source code (open repo, leaked env), they can generate a valid monitoring token for any monitoring officer account without the `.env` key. Fix: remove the fallback entirely, raise an error if the env variable isn't set, and rotate the key on deploy.

---

## What's Working

- All endpoints from Tasks 1–3 are implemented and deployed
- Role-based access control enforced server-side via JWT on every protected route
- Two-token monitoring flow working end to end
- Validation errors return 422 with readable messages (not raw SQLAlchemy traces)
- Foreign key violations caught and returned as 404
- Students blocked with 403 if they try to mark attendance for sessions they're not in
- `/monitoring/attendance` returns 405 for POST/PUT/PATCH/DELETE
- Seed script creates realistic data across 2 institutions, 3 batches, 4 trainers, 15 students, 8 sessions, with attendance records
- Alembic migrations set up and working
- 5 pytest tests written, 2 of which hit the test database directly

## What's Partial / Skipped

- Tests: I kept the test database as SQLite for simplicity. Two tests hit it directly (signup and attendance marking); the rest test logic without DB calls. Ideally all five would run against a proper Postgres test instance.
- No refresh token implementation — tokens expire and users just log in again.
- No pagination on `/monitoring/attendance` — for a large programme this would be the first thing to add.
- The `batch_summary` attendance rate only counts `present` status; `late` records don't contribute to the rate. That's probably wrong for a real system but I didn't want to guess the business rule.

---

## One Thing I'd Do Differently

I'd add a proper dependency injection layer for the current user object earlier. Right now `require_role()` returns a raw dict decoded from the JWT, and several route handlers access `current_user["sub"]` or `current_user["role"]` directly. If the token shape ever changes, there are quiet bugs waiting. A `CurrentUser` dataclass resolved through a single `get_current_user` dependency would make this safer and easier to test.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use a local SQLite database (`test.db`) that gets created and torn down automatically. No external services needed to run the test suite.