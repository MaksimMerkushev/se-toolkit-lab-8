# se-toolkit-hackathon

se-toolkit-hackathon is a student progress dashboard that turns lab data into clear next actions.

## Screenshots

The app includes a compact login screen, a lab progress hero, charts for scores and submissions, and an assistant panel that explains what to do next.

- Dashboard overview
- Assistant response view

## Product context

### End users

Students who need to understand their lab progress quickly.

### Problem

Lab data is spread across raw API responses, charts, and task lists. That makes it hard to see what is actually blocking progress.

### Solution

LabLens aggregates the existing LMS data into a single workspace that highlights weak tasks, group performance, and a recommended next step.

## Features

### Implemented

- Lab selector based on the current LMS catalog.
- Completion rate, weak task, best group, and top learner summaries.
- Score distribution, submission timeline, group comparison, and task pass-rate charts.
- Assistant endpoint that answers questions about the selected lab.
- Optional OpenAI-compatible LLM integration through environment variables.

### Not yet implemented

- Per-user accounts and saved personal notes.
- Push reminders for upcoming deadlines.
- Mobile-specific layout.

## Usage

1. Start the backend, PostgreSQL, and frontend with Docker Compose or local services.
2. Open the web app in a browser.
3. Enter the LMS API key used in the previous labs. For the local demo, use `my-secret-api-key`.
4. Choose a lab and ask the assistant what to focus on next.

## Enable AI (OpenRouter)

AskLabLens supports OpenRouter with `openai/gpt-4o-mini`.

1. Set your key in `/tmp/studyflow/.env`:

	`OPENROUTER_API_KEY=<your-openrouter-key>`

2. Keep these values:

	`OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`

	`OPENROUTER_MODEL=openai/gpt-4o-mini`

3. Restart backend:

	`set -a && source /tmp/studyflow/.env && set +a && /usr/local/bin/python3 /tmp/studyflow/backend/src/lms_backend/run.py`

If the key is empty or invalid, AskLabLens automatically falls back to deterministic metric-based guidance.

## Deployment

### Target OS

Ubuntu 24.04.

### Required software

- Docker
- Docker Compose
- A PostgreSQL instance for the backend data

### Step-by-step

1. Set the environment variables required by `docker-compose.yml`, including `LMS_API_KEY`, `POSTGRES_*`, and the gateway ports.
2. Build and start the stack with `docker compose up --build`.
3. Wait for PostgreSQL, the backend, and the frontend to become healthy.
4. Open the gateway URL exposed by Caddy.
5. Optionally configure `ASSISTANT_LLM_API_URL`, `ASSISTANT_LLM_API_KEY`, and `ASSISTANT_LLM_MODEL` to enable LLM-backed answers.

### Recommended app names

- `BACKEND_NAME=LabLens`
- `BACKEND_NAME` is used by FastAPI and telemetry labels.

## Backend API

Key endpoints used by the client:

- `GET /items/`
- `GET /analytics/completion-rate?lab=lab-08`
- `GET /analytics/pass-rates?lab=lab-08`
- `GET /analytics/groups?lab=lab-08`
- `GET /analytics/timeline?lab=lab-08`
- `GET /analytics/top-learners?lab=lab-08&limit=3`
- `POST /assistant/insights`

## Stack

- FastAPI backend
- PostgreSQL database
- React + Vite frontend
- Optional OpenAI-compatible LLM for assistant summaries
