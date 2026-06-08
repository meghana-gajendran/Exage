# ExAge — Expose What You Don't Know

ExAge is an AI-powered diagnostic learning tool that helps learners discover hidden gaps in their understanding through Socratic questioning.

It does not explain or teach. It probes, challenges assumptions, and surfaces what you don't know you don't know.

---

## How it works

1. Choose a topic and learning goal (interview prep, exam, project, teaching, curiosity)
2. Explain what you know — in your own words
3. ExAge analyses your response, detects conceptual gaps, and asks probing questions
4. Each question builds on your previous answer, escalating from surface to systemic
5. After 8 turns (or when you say "done"), a synthesis summary is generated showing all gaps found, misconceptions flagged, and 3 curiosity paths to explore next

---

## Architecture

```
exage-backend/      Python · FastAPI · SQLite · OpenAI API
exage-frontend/     Next.js · TypeScript
```

Communication between frontend and backend uses **Server-Sent Events (SSE)** for real-time streaming.

### Agent pipeline (sequential)

| Agent              | Role                                              |
| ------------------ | ------------------------------------------------- |
| Concept Extractor  | Parses what the learner said                      |
| Gap Detector       | Identifies missing concepts                       |
| Question Generator | Generates Socratic probing questions              |
| Response Composer  | Selects and phrases the final response            |
| Synthesis Agent    | End-of-session summary and curiosity paths        |
| Evaluation Agent   | Measures whether each question exposed a real gap |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- An OpenAI API key

---

## Setup & Running

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ExAge.git
cd ExAge
```

### 2. Backend setup

```bash
cd exage-backend

# Create virtual environment
uv venv venv
source venv/bin/activate

# Install dependencies
uv pip install fastapi uvicorn sqlalchemy openai pydantic-settings pydantic pytest pytest-asyncio httpx2
```

Create a `.env` file in `exage-backend/`:

```
OPENAI_API_KEY=sk-your-openai-key-here
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 3. Frontend setup

Open a new terminal tab:

```bash
cd exage-frontend

# Install dependencies
npm install

# Start the frontend
npm run dev
```

Frontend runs at: `http://localhost:3000`

---

## Running both servers

You need two terminal tabs running simultaneously:

| Terminal         | Command                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------- |
| Tab 1 (backend)  | `cd exage-backend && source venv/bin/activate && uvicorn main:app --reload --port 8000` |
| Tab 2 (frontend) | `cd exage-frontend && npm run dev`                                                      |

Then open `http://localhost:3000` in your browser.

---

## Running tests

```bash
cd exage-backend
source venv/bin/activate
pytest tests/ -v
```

Expected: **23 tests passing**

---

## Project structure

```
ExAge/
├── exage-backend/
│   ├── agents/
│   │   ├── base.py
│   │   ├── concept_extractor.py
│   │   ├── gap_detector.py
│   │   ├── question_generator.py
│   │   ├── response_composer.py
│   │   ├── synthesis_agent.py
│   │   └── evaluation_agent.py
│   ├── pipeline/
│   │   └── runner.py
│   ├── routers/
│   │   ├── sessions.py
│   │   └── chat.py
│   ├── tests/
│   │   ├── test_agents.py
│   │   ├── test_api.py
│   │   ├── test_pipeline.py
│   │   └── test_new_agents.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── config.py
│
└── exage-frontend/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   └── chat/page.tsx
    ├── components/
    │   ├── OnboardingModal.tsx
    │   ├── Sidebar.tsx
    │   ├── ChatHeader.tsx
    │   ├── MessageList.tsx
    │   ├── Message.tsx
    │   ├── GapBlock.tsx
    │   ├── SynthesisBlock.tsx
    │   ├── StatusBar.tsx
    │   └── InputArea.tsx
    └── lib/
        ├── api.ts
        └── types.ts
```

---

## Environment variables

### Backend (`exage-backend/.env`)

```
OPENAI_API_KEY=sk-your-key-here
```

This file is gitignored and must be created manually.

---

## Notes

- SQLite database (`exage.db`) is created automatically on first run — no setup needed
- Sessions persist across page refreshes
- Synthesis is triggered automatically after 8 turns, or by sending: `done`, `wrap up`, `summarize`, `finish`, or `that's all`
