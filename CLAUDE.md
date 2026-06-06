# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a course design project for "Application Software Architecture" - a **Lake and Sea Testing Ground Digital Twin Panoramic Monitoring and Data Management System** for university ship and ocean engineering testing facilities.

The system covers the complete experimental workflow: reservation → approval → preparation → execution → monitoring → archiving → AI analysis.

**Key Course Requirements:**
- 4-6 demonstrable functional modules
- At least 1 master-detail table business feature
- Clear frontend-backend separation
- Layered backend architecture
- DM8 (DaMeng) national database integration
- DeepSeek API integration
- WebSocket/MQTT real-time data interface
- Digital twin monitoring visualization

## Tech Stack

**Frontend:** Vue 3 + TypeScript + Vite + Element Plus + ECharts + Three.js  
**Backend:** FastAPI + SQLAlchemy + Pydantic + Uvicorn + WebSocket  
**Database:** SQLite (dev) / DM8 (production)  
**AI Integration:** DeepSeek API

## Development Commands

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
copy .env.example .env          # Windows
cp .env.example .env            # macOS/Linux
python -m scripts.seed_db       # Initialize database
uvicorn app.main:app --reload   # Start server
```

Backend runs on http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev         # Development server
npm run build       # Production build
npm run preview     # Preview build
```

Frontend runs on http://localhost:5173  
Proxies `/api` → `http://127.0.0.1:8000` and `/ws` → `ws://127.0.0.1:8000`

### Database Initialization

**SQLite (default):** Automatic table creation via ORM on startup  
**DM8 (production):** Execute `backend/scripts/init_db.sql` in DM client, then run `python -m scripts.seed_db`

## Architecture

### Backend Layered Structure

The backend MUST maintain strict layering - do NOT write all logic in API routes.

```
API Layer (api/)           → Receive requests, validate params, return responses
Service Layer (services/)  → Business logic, workflow control, transaction handling
Repository Layer (repos/)  → Database CRUD operations
Model Layer (models/)      → SQLAlchemy database models
Schema Layer (schemas/)    → Pydantic request/response models
Core Layer (core/)         → Database connection, config, security, tokens
```

**Critical Rule:** Never bypass the Service layer. Complex business logic must not be written directly in API routes.

```
Correct flow: API → Service → Repository → Model/Database
```

### Key Directories

```
backend/app/
├── api/            # API route handlers (auth, reservation, resource, experiment, monitor, alarm, ai, ws)
├── services/       # Business logic layer
├── repositories/   # Data access layer
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic schemas
└── core/           # Config, database, security, deps, response, ws_manager

frontend/src/
├── api/            # Backend API clients
├── views/          # Page components
├── components/     # Reusable components
├── router/         # Vue Router config
├── stores/         # Pinia state management
├── layouts/        # Layout components
└── utils/          # Utilities
```

## Core Business Logic

### Master-Detail Table Business (Course Requirement)

**Master:** `EXP_RESERVATION` (试验预约)  
**Detail:** `EXP_RESERVATION_RESOURCE` (预约资源明细)  

A single reservation can occupy multiple resources (towing tank, model ship, IMU sensors, cameras, towing equipment).

### Two-Level Approval Workflow

```
Student creates draft → Student submits → Teacher reviews → Director approves → System generates experiment task
```

- Resource conflict check happens at submission and before director approval
- Approval rejection requires a reason
- Once approved/completed/archived, cannot be re-approved

### Experiment Task State Machine

```
PENDING_PREPARE → READY → RUNNING → COMPLETED → ARCHIVED
```

### Resource Conflict Rules

- Same resource cannot be reserved for overlapping time periods
- Resources in FAULT, DISABLED, or MAINTENANCE status cannot be reserved
- Draft reservations do not lock resources
- Submitted reservations create future time-slot occupancy
- Running experiments set resources to IN_USE status

### Alarm Types

- Model ship approaching boundary
- Model ship out of bounds
- Battery level too low
- Sensor data anomaly
- Device offline
- Speed exceeds threshold
- Data not updating

## Database Conventions

### Naming Style

- **Tables:** UPPERCASE_WITH_UNDERSCORES (e.g., `EXP_RESERVATION`, `LAB_RESOURCE`)
- **Columns:** UPPERCASE_WITH_UNDERSCORES (e.g., `EXP_NAME`, `START_TIME`, `APPLICANT_ID`)
- **Primary Key:** `ID BIGINT PRIMARY KEY`
- **Common timestamps:** `CREATE_TIME`, `UPDATE_TIME`
- **Logical deletion:** `IS_DELETED`

### Important Tables

```
SYS_USER, SYS_ROLE, SYS_USER_ROLE
EXP_RESERVATION, EXP_RESERVATION_RESOURCE (master-detail)
LAB_RESOURCE
EXPERIMENT_TASK
SENSOR_DATA, SHIP_TRACK
ALARM_RECORD
EXPERIMENT_FILE
AI_REPORT
```

## API Conventions

### REST Endpoints

All APIs start with `/api`:

```
POST   /api/auth/login
GET    /api/reservations
POST   /api/reservations
GET    /api/reservations/{id}
PUT    /api/reservations/{id}
POST   /api/reservations/{id}/submit
POST   /api/reservations/{id}/teacher-review
POST   /api/reservations/{id}/director-approve
GET    /api/resources
POST   /api/experiments/{id}/replay
POST   /api/ai/reports/generate
```

### WebSocket

```
/ws/monitor/{experiment_id}
```

Pushes: model ship position/attitude/battery, sensor data, alarms

### Response Format

**Success:**
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**Error:**
```json
{
  "code": 400,
  "message": "error message",
  "data": null
}
```

## AI Integration

- DeepSeek API calls MUST only happen in backend (`ai_service.py`)
- Frontend must NEVER store or expose API keys
- Set `MOCK_AI=true` in `.env` for local mock mode
- Set `MOCK_AI=false` and configure `DEEPSEEK_API_KEY` for real API calls

**AI Report Flow:**
```
Frontend clicks "Generate AI Analysis"
  → AI API endpoint
  → AiService queries experiment data
  → Assembles prompt with structured summary
  → Calls DeepSeek API
  → Saves to AI_REPORT table
  → Returns report to frontend
```

**AI Report Content:**
- Experiment overview
- Key data summary
- Anomaly descriptions
- Possible cause analysis
- Risk warnings
- Improvement suggestions

## Demo Accounts

All passwords are `123456`:

| Username | Role |
|----------|------|
| admin | ADMIN |
| director01 | DIRECTOR |
| teacher01 | TEACHER |
| student01 | STUDENT |
| maintainer01 | MAINTAINER |

## Testing and Demo Flow

Recommended demo sequence for course presentation:

1. Admin login - view users and resources
2. Student login - create reservation draft with multiple resource items
3. Student submits reservation
4. Teacher login - reviews and approves reservation
5. Director login - approves reservation (generates experiment task)
6. Prepare and start experiment
7. Open digital twin monitoring page
8. Show model ship trajectory, real-time charts, and alarms
9. Complete experiment and navigate to archive page
10. Generate and display AI analysis report

## What NOT to Change

When modifying this project, do NOT:

1. Change the project theme from lake/sea testing ground to generic equipment management
2. Remove the master-detail table design (EXP_RESERVATION + EXP_RESERVATION_RESOURCE)
3. Ignore the DM8 database requirement
4. Hard-code DeepSeek API keys in frontend
5. Write all backend logic in a single `main.py`
6. Bypass Service layer and write complex business logic directly in API routes
7. Remove digital twin monitoring, real-time data, or AI analysis features
8. Over-engineer with real hardware integration (simulated data is acceptable for course)

## Security Notes

- Do NOT commit database passwords or DeepSeek API keys to Git
- Use `.env` for sensitive configuration
- Frontend must NOT directly call DeepSeek API
- Use logical deletion for important business data
- Record operator and timestamp for critical approval operations
