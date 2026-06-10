# BFK Admin — Boxing Federation of Kenya
### FastAPI · SQLAlchemy · SQLite · Static HTML Frontend

A local-first admin system for managing fighters, clubs, coaches, bouts,
events, medical records, suspensions, titles, and matchmaking.
Everything runs from a single `python main.py` command — no Docker,
no external database, no separate frontend server.

---

## Folder Structure

```
bfk_backend/                    ← project root (cd here for all commands)
│
├── main.py                     ← FastAPI app + static mount + entry point
├── seed.py                     ← Populates bfk.db with dummy data
├── requirements.txt            ← Python dependencies
├── bfk.db                      ← SQLite database (auto-created on first run)
│
├── static/                     ← Frontend lives here
│   └── index.html              ← ← DROP YOUR HTML FILE HERE
│
└── app/                        ← Python package
    ├── __init__.py
    ├── database.py             ← SQLAlchemy engine, session, Base
    ├── models.py               ← All ORM table definitions
    ├── schemas.py              ← All Pydantic request/response schemas
    └── routers/
        ├── __init__.py
        ├── fighters.py         ← /fighters  (CRUD + sub-resources)
        ├── clubs.py            ← /clubs
        ├── coaches.py          ← /coaches
        ├── competition.py      ← /weight-classes  /events  /bouts
        │                          /titles  /suspensions
        └── matchmaking.py      ← /matchmaking/pool  /suggest  /check
```

---

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.10 or newer | `python --version` |
| pip | any recent | `pip --version` |

No other external tools are needed — SQLite is built into Python.

---

## Setup (First Time)

### 1. Get the project

If you downloaded a zip, unzip it. If you cloned git:
```bash
git clone <repo-url>
cd bfk_backend
```

### 2. Create a virtual environment (recommended)

**macOS / Linux**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt)**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` appear at the start of your terminal prompt.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `python-multipart`, `aiofiles`.

### 4. Place the HTML frontend

Copy your `kenya_boxing_admin.html` file into the `static/` folder and rename it `index.html`:

```
bfk_backend/
└── static/
    └── index.html      ← your HTML file goes here
```

```bash
# macOS / Linux example:
cp /path/to/kenya_boxing_admin.html static/index.html

# Windows example:
copy C:\Users\YourName\Downloads\kenya_boxing_admin.html static\index.html
```

### 5. Seed the database with dummy data

```bash
python seed.py
```

Expected output:
```
⚡  Dropping and recreating all tables…
✓   Tables created
🥊  Seeding weight classes…
🏟   Seeding clubs…
👨‍🏫  Seeding coaches…
🥊  Seeding fighters…
📋  Seeding events…
🥊  Seeding bouts…
🏆  Seeding titles…
🚫  Seeding suspensions…
🎯  Seeding matchmaking pool…

✅  Seed complete!
   Weight classes : 42
   Clubs          : 6
   Coaches        : 6
   Fighters       : 12
   Bouts          : 8
   Events         : 6
   Titles         : 4
   Suspensions    : 4
   Pool entries   : 8
```

This creates `bfk.db` in the project root. **Run seed.py only once** — re-running it drops and recreates all data.

---

## Running the Server

```bash
python main.py
```

You will see:
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

---

## Opening in the Browser

| URL | What you get |
|---|---|
| `http://127.0.0.1:8001/` | **Admin UI** (your HTML frontend) |
| `http://127.0.0.1:8001/docs` | **Swagger UI** — interactive API explorer |
| `http://127.0.0.1:8001/redoc` | **ReDoc** — clean API reference docs |
| `http://127.0.0.1:8001/health` | Health check JSON |
| `http://127.0.0.1:8001/dashboard` | Dashboard summary JSON |

---

## Development Mode (auto-reload on file changes)

If you are actively editing Python files and want the server to restart automatically:

```bash
uvicorn main:app --reload --port 8001
```

> **Note:** `--reload` watches `.py` files only, not the HTML file. You still need to manually refresh the browser after editing `static/index.html`.

---

## API Reference

All endpoints are prefixed with their resource name. Full interactive docs are at `/docs`.

### Fighters — `/fighters`
| Method | Path | Description |
|---|---|---|
| `GET` | `/fighters/` | List all fighters (filter: county, gender, status, search) |
| `POST` | `/fighters/` | Register a new fighter |
| `GET` | `/fighters/{id}` | Full profile with all sub-resources |
| `PATCH` | `/fighters/{id}` | Update fighter details |
| `DELETE` | `/fighters/{id}` | Delete fighter |
| `GET` | `/fighters/{id}/record` | Boxing record (W/L/D breakdown) |
| `PATCH` | `/fighters/{id}/record` | Manually adjust boxing record |
| `GET` | `/fighters/{id}/bouts` | All bouts for this fighter |
| `GET` | `/fighters/{id}/medical` | All medical records |
| `POST` | `/fighters/{id}/medical` | Add a medical examination |
| `PATCH` | `/fighters/{id}/medical/{rid}` | Update a medical record |
| `GET` | `/fighters/{id}/physical` | Physical measurement history |
| `POST` | `/fighters/{id}/physical` | Add a physical measurement |
| `GET` | `/fighters/{id}/titles` | All titles held |
| `GET` | `/fighters/{id}/suspensions` | All suspensions |
| `POST` | `/fighters/{id}/clubs` | Assign to a club |
| `POST` | `/fighters/{id}/coaches` | Assign a coach |

### Clubs — `/clubs`
| Method | Path | Description |
|---|---|---|
| `GET` | `/clubs/` | List clubs (filter: county, type) |
| `POST` | `/clubs/` | Create club |
| `GET` | `/clubs/{id}` | Club detail with coaching staff |
| `PATCH` | `/clubs/{id}` | Update club |
| `DELETE` | `/clubs/{id}` | Delete club |
| `GET` | `/clubs/{id}/fighters` | Current fighters at this club |

### Coaches — `/coaches`
| Method | Path | Description |
|---|---|---|
| `GET` | `/coaches/` | List coaches (filter: club_id) |
| `POST` | `/coaches/` | Register coach |
| `GET` | `/coaches/{id}` | Coach detail |
| `PATCH` | `/coaches/{id}` | Update coach |
| `DELETE` | `/coaches/{id}` | Delete coach |

### Weight Classes — `/weight-classes`
| Method | Path | Description |
|---|---|---|
| `GET` | `/weight-classes/` | List (filter: gender, category, governing_body) |
| `POST` | `/weight-classes/` | Create weight class |
| `GET` | `/weight-classes/{id}` | Single weight class |
| `PATCH` | `/weight-classes/{id}` | Update |

### Events — `/events`
| Method | Path | Description |
|---|---|---|
| `GET` | `/events/` | List (filter: status, type, county, date range) |
| `POST` | `/events/` | Create event |
| `GET` | `/events/{id}` | Event detail with bout card |
| `PATCH` | `/events/{id}` | Update event |
| `DELETE` | `/events/{id}` | Delete event |

### Bouts — `/bouts`
| Method | Path | Description |
|---|---|---|
| `GET` | `/bouts/` | List (filter: event_id, fighter_id, weight_class_id) |
| `POST` | `/bouts/` | Schedule a bout (no result yet) |
| `GET` | `/bouts/{id}` | Bout detail with fighters, scorecards |
| `PATCH` | `/bouts/{id}/result` | Record result — auto-updates both fighters' records |
| `DELETE` | `/bouts/{id}` | Delete bout |

### Titles — `/titles`
| Method | Path | Description |
|---|---|---|
| `GET` | `/titles/` | List (filter: is_active, governing_body) |
| `POST` | `/titles/` | Record a title |
| `GET` | `/titles/{id}` | Title detail |
| `PATCH` | `/titles/{id}` | Update (vacate, add defence, etc.) |

### Suspensions — `/suspensions`
| Method | Path | Description |
|---|---|---|
| `GET` | `/suspensions/` | List (filter: is_active, type) |
| `POST` | `/suspensions/` | Issue a suspension — sets fighter status to `suspended` |
| `GET` | `/suspensions/{id}` | Suspension detail |
| `PATCH` | `/suspensions/{id}` | Update / lift suspension — restores fighter to `active` |

### Matchmaking — `/matchmaking`
| Method | Path | Description |
|---|---|---|
| `GET` | `/matchmaking/pool` | List available pool fighters |
| `POST` | `/matchmaking/pool` | Add fighter to pool |
| `GET` | `/matchmaking/pool/{id}` | Single pool entry |
| `PATCH` | `/matchmaking/pool/{id}` | Update availability / preferences |
| `DELETE` | `/matchmaking/pool/{id}` | Remove from pool |
| `GET` | `/matchmaking/pool/by-fighter/{id}` | Pool entry by fighter ID |
| `GET` | `/matchmaking/suggest` | **Generate match suggestions** |
| `GET` | `/matchmaking/check` | **Eligibility check for a specific pair** |
| `GET` | `/matchmaking/stats` | Pool stats by weight class |

### Utility
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | DB ping + service status |
| `GET` | `/dashboard` | All aggregate stats for dashboard UI |
| `GET` | `/search?q=term` | Cross-entity search (fighters, clubs, coaches, events) |

---

## Matchmaking Suggestion Engine

`GET /matchmaking/suggest` runs every BFK/KPBC eligibility rule on every available pair in the pool and returns ranked suggestions.

### Query Parameters

| Parameter | Default | Description |
|---|---|---|
| `weight_class_id` | all | Restrict to one division |
| `gender` | all | `male` or `female` |
| `experience_level` | all | `novice`, `intermediate`, `advanced`, `professional` |
| `max_experience_gap` | `1` | Max tier difference allowed (0 = exact match) |
| `no_repeat_months` | `6` | Flag pairs who fought within N months |
| `min_score` | `50.0` | Minimum compatibility score (0–100) to include |
| `event_date` | today | Used for licence expiry checks |
| `limit` | `20` | Max suggestions to return |

### Eligibility Checks (weighted)

| Check | Weight | Rule |
|---|---|---|
| Active status | 15 | `fighter.status == active` |
| No suspension | 15 | No active suspension record |
| Medical clear | 15 | `cleared_to_compete=True` + licence not expired |
| Same weight class | 15 | Both pool entries at same `weight_class_id` |
| Different clubs | 10 | BFK Rule — same-club bouts not permitted |
| Experience match | 10 | Within `max_experience_gap` tiers |
| Same gender | 10 | BFK/IBA gender separation |
| No recent bout | 5 | No prior bout within `no_repeat_months` |
| Walk-around weight | 5 | Difference ≤ 3 kg (soft check) |

Score is 0–100. Pairs below `min_score` are excluded.

### Example request

```bash
# Best available amateur lightweight matches, male only
curl "http://127.0.0.1:8001/matchmaking/suggest?weight_class_id=5&gender=male&min_score=70"

# Check a specific pair before creating the bout
curl "http://127.0.0.1:8001/matchmaking/check?fighter_a_id=1&fighter_b_id=12&weight_class_id=5"
```

---

## Common Tasks

### Re-seed (reset all data)
```bash
python seed.py
```
> ⚠ This **drops and recreates all tables** and all data. Only use during development.

### Add a fighter via API (curl example)
```bash
curl -X POST http://127.0.0.1:8001/fighters/ \
  -H "Content-Type: application/json" \
  -d '{
    "licence_number": "BFK-M-2025-060",
    "first_name": "James",
    "last_name": "Kariuki",
    "date_of_birth": "2000-03-15",
    "gender": "male",
    "county": "Nairobi",
    "phone": "+254 712 000 001",
    "blood_type": "O+",
    "status": "active"
  }'
```

### Record a bout result
```bash
# First create the bout (scheduled, no result)
curl -X POST http://127.0.0.1:8001/bouts/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 3,
    "weight_class_id": 5,
    "fighter_a_id": 1,
    "fighter_b_id": 12,
    "scheduled_rounds": 3,
    "bout_type": "non_title"
  }'

# Then record the result (auto-updates both fighters' W/L records)
curl -X PATCH http://127.0.0.1:8001/bouts/9/result \
  -H "Content-Type: application/json" \
  -d '{
    "actual_rounds_fought": 2,
    "result": "fighter_a",
    "winner_id": 1,
    "win_method": "TKO",
    "win_round": 2,
    "win_time": "1:45",
    "referee": "Julius Makokha"
  }'
```

### Issue a medical suspension
```bash
curl -X POST http://127.0.0.1:8001/suspensions/ \
  -H "Content-Type: application/json" \
  -d '{
    "fighter_id": 4,
    "suspension_type": "medical",
    "reason": "Post-KO mandatory hold",
    "rule_reference": "BFK Rule 4.8",
    "start_date": "2025-08-01",
    "end_date": "2025-08-31",
    "imposed_by": "Dr. Kibuchi",
    "conditions": "Full re-examination required before return",
    "is_active": true
  }'
```

### Lift a suspension
```bash
curl -X PATCH http://127.0.0.1:8001/suspensions/1 \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "lifted_date": "2025-07-28",
    "lifted_by": "Dr. Kibuchi"
  }'
```

---

## Enum Reference

These are the exact string values accepted by the API.

| Field | Accepted values |
|---|---|
| `fighter.status` | `active` `inactive` `retired` `suspended` `deceased` |
| `fighter.gender` | `male` `female` |
| `stance` | `orthodox` `southpaw` `switch` |
| `experience_level` | `novice` `intermediate` `advanced` `professional` |
| `club.type` | `amateur` `professional` `mixed` |
| `weight_class.category` | `amateur_male` `amateur_female` `professional` |
| `governing_body` | `BFK` `KPBC` `IBA` `ABU` `WBC` `WBO` `IBF` `WBA` |
| `event.event_type` | `amateur` `professional` `mixed` |
| `event.status` | `draft` `upcoming` `in_progress` `completed` `cancelled` |
| `bout.bout_type` | `title` `title_defence` `elimination` `non_title` `exhibition` |
| `bout.result` | `fighter_a` `fighter_b` `draw` `no_contest` `technical_draw` |
| `bout.win_method` | `KO` `TKO` `TKO_medical` `TKO_corner` `UD` `MD` `SD` `DQ` `RTD` `NC` |
| `suspension.suspension_type` | `medical` `disciplinary` `administrative` `doping` |
| `pool.preferred_bout_type` | `title` `title_defence` `non_title` `any` |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'fastapi'`**
You forgot to activate the virtual environment or install requirements:
```bash
source venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

**`Address already in use` on port 8001**
Something else is already on that port. Kill it or change the port:
```bash
# Change port in main.py:  port=8001  →  port=8002
python main.py
```

**`bfk.db` is missing / empty tables**
Run the seed script first:
```bash
python seed.py
```

**Frontend shows a blank page at `/`**
Make sure the HTML file is named exactly `index.html` (lowercase) inside the `static/` folder:
```
static/
  index.html   ← must be this exact name
```

**API calls from the HTML return 404 or CORS errors**
The HTML file must be served from the same origin as the API (i.e. through FastAPI at `http://127.0.0.1:8001/`). Do **not** open `index.html` directly by double-clicking it in your file explorer — it must be served via the Python server.

**Changes to `static/index.html` don't appear**
Hard-refresh the browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (macOS).

---

## File the HTML makes API calls to

When writing `fetch()` calls in your HTML, use relative paths — they automatically point to the same server:

```javascript
// ✅ Correct — works from http://127.0.0.1:8001/
const res = await fetch('/fighters/');
const res = await fetch('/matchmaking/suggest?gender=male');
const res = await fetch('/dashboard');

// ❌ Wrong — hardcoded origin will break if port changes
const res = await fetch('http://127.0.0.1:8001/fighters/');
```

---

## Project Files Summary

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, all route registration, static file mount, `uvicorn.run()` entry point |
| `seed.py` | One-time script to populate `bfk.db` with realistic Kenyan boxing data |
| `requirements.txt` | Exact Python packages needed |
| `app/database.py` | SQLAlchemy engine (`bfk.db`), session factory, `get_db` dependency |
| `app/models.py` | Every database table as a Python class (SQLAlchemy ORM) |
| `app/schemas.py` | Every request body and response shape (Pydantic) |
| `app/routers/fighters.py` | Fighter CRUD + all fighter sub-resources |
| `app/routers/clubs.py` | Club CRUD |
| `app/routers/coaches.py` | Coach CRUD |
| `app/routers/competition.py` | Weight classes, events, bouts, titles, suspensions |
| `app/routers/matchmaking.py` | Pool CRUD + suggestion engine + eligibility checker |
| `static/index.html` | Your HTML admin frontend (you place this here) |
| `bfk.db` | SQLite database file (auto-created, do not edit manually) |
