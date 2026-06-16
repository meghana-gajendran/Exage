# ExAge — Expose What You Don't Know

ExAge is an AI-powered diagnostic learning tool that helps learners discover hidden gaps in their understanding through Socratic questioning.

It does not explain or teach. It probes, challenges assumptions, and surfaces what you don't know you don't know.

---

## Two modes

### Option 1 — Chat mode
The learner explains what they know about a topic. ExAge analyses their explanation, detects conceptual gaps, and asks probing questions. Each question builds on the previous answer, escalating from surface to systemic understanding.

### Option 2 — Repo mode
The learner points ExAge at a GitHub repository or local folder. ExAge reads the codebase, infers what the developer understands from their code, identifies gaps in their mental model, and ranks them by consequence for their learning goal  without asking the learner to self-report anything.

Both modes hand off to the same Socratic chat interface for probing.

---

## How Option 1 works

1. Choose a topic and learning goal (interview prep, exam, project, teaching, curiosity)
2. Explain what you know in your own words
3. ExAge analyses your response, detects conceptual gaps, and asks 1–2 probing questions
4. Each question builds on your previous answer
5. After 8 turns (or when you say "done"), a synthesis summary shows all gaps found, misconceptions flagged, and 3 curiosity paths to explore next

## How Option 2 works

1. Paste a GitHub URL or local folder path
2. Choose a learning goal
3. ExAge reads the repository (no cloning uses GitHub API or local file system)
4. 4 agents run sequentially: concept extraction → skill inference → gap detection → consequence ranking
5. An analysis report shows detected concepts, strongest areas, and top gaps ranked for your goal
6. Click "Start probing"  opens a chat session pre-loaded with your gaps, skipping onboarding entirely

---

## Architecture

```
exage-backend/      Python · FastAPI · SQLite · OpenAI API
exage-frontend/     Next.js · TypeScript
```

Communication between frontend and backend uses **Server-Sent Events (SSE)** for real-time streaming.

### Option 1 agent pipeline

| Agent | Role |
|---|---|
| Concept Extractor | Parses what the learner said |
| Gap Detector | Identifies missing concepts |
| Question Generator | Generates Socratic probing questions |
| Response Composer | Selects and phrases the final response |
| Synthesis Agent | End-of-session summary and curiosity paths |
| Evaluation Agent | Measures whether each question exposed a real gap |

### Option 2 agent pipeline

| Agent | Role |
|---|---|
| Repo Ingester | Reads repo structure, selects key files, detects frameworks |
| Concept Extractor | Extracts concepts and patterns observed in the code |
| Skill Inferrer | Infers understanding depth from code evidence |
| Gap Detector | Finds missing or shallow concepts vs full technology graph |
| Consequence Ranker | Ranks gaps by impact for the learner's specific goal |

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
git clone https://github.com/meghana-gajendran/Exage.git
cd Exage
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

| Terminal | Command |
|---|---|
| Tab 1 (backend) | `cd exage-backend && source venv/bin/activate && uvicorn main:app --reload --port 8000` |
| Tab 2 (frontend) | `cd exage-frontend && npm run dev` |

Then open `http://localhost:3000` in your browser.

---

## Running tests

```bash
cd exage-backend
source venv/bin/activate
pytest tests/ -v
```

Expected: **65 tests passing** (23 Option 1 + 42 Option 2)

---

## Project structure

```
ExAge/
├── exage-backend/
│   ├── agents/                     # Option 1 agents
│   │   ├── base.py
│   │   ├── concept_extractor.py
│   │   ├── gap_detector.py
│   │   ├── question_generator.py
│   │   ├── response_composer.py
│   │   ├── synthesis_agent.py
│   │   └── evaluation_agent.py
│   ├── agents_option2/             # Option 2 agents
│   │   ├── concept_extractor_v2.py
│   │   ├── skill_inferrer.py
│   │   ├── gap_detector_v2.py
│   │   ├── consequence_ranker.py
│   │   └── pipeline_v2.py
│   ├── repo_analysis/              # Repo ingestion
│   │   ├── file_scorer.py
│   │   ├── framework_detector.py
│   │   ├── ingester.py
│   │   └── ingesters/
│   │       ├── local_ingester.py
│   │       └── github_ingester.py
│   ├── pipeline/
│   │   └── runner.py
│   ├── routers/
│   │   ├── sessions.py
│   │   ├── chat.py
│   │   └── repo_analysis.py
│   ├── tests/
│   │   ├── test_agents.py
│   │   ├── test_api.py
│   │   ├── test_pipeline.py
│   │   ├── test_new_agents.py
│   │   ├── test_ingester.py
│   │   ├── test_phase2.py
│   │   └── test_phase3.py
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
    │   ├── chat/page.tsx           # Option 1 chat interface
    │   └── repo/page.tsx           # Option 2 repo analysis
    ├── components/
    │   ├── OnboardingModal.tsx
    │   ├── Sidebar.tsx
    │   ├── ChatHeader.tsx
    │   ├── MessageList.tsx
    │   ├── Message.tsx
    │   ├── GapBlock.tsx
    │   ├── SynthesisBlock.tsx
    │   ├── StatusBar.tsx
    │   ├── InputArea.tsx
    │   ├── RepoInputModal.tsx
    │   └── RepoAnalysisReport.tsx
    └── lib/
        ├── api.ts
        └── types.ts
```

---

## API routes

| Method | Route | Purpose |
|---|---|---|
| POST | `/sessions/` | Create chat session |
| GET | `/sessions/` | Get all sessions |
| GET | `/sessions/{id}` | Get single session |
| GET | `/sessions/{id}/messages` | Get message history |
| POST | `/sessions/{id}/chat` | Send message, stream SSE response |
| DELETE | `/sessions/{id}` | Delete session |
| POST | `/repo-analysis/` | Run Option 2 pipeline |
| POST | `/repo-analysis/stream` | Run Option 2 pipeline with SSE status |
| POST | `/repo-analysis/create-session` | Create chat session from repo analysis |

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
- Option 1 synthesis triggers automatically after 8 turns, or by sending: `done`, `wrap up`, `summarize`, `finish`, or `that's all`
- Option 2 supports public GitHub repositories and local folder paths
- Option 2 repo analysis takes 30–60 seconds (4 sequential LLM calls)
