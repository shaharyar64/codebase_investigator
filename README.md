# AI Codebase Investigator

Full-stack repository investigation system built with FastAPI, Next.js, Postgres,
ripgrep, GitPython, and the OpenAI API.

This is intentionally not a semantic RAG project. It does not use embeddings,
vector databases, semantic search, or LangChain-heavy abstractions. The agent
plans literal searches, inspects real files, reads line ranges, reasons over the
observed code, and runs an independent audit pass over the answer.

## Architecture

```text
backend/
  app/
    api/                 FastAPI routes, dependencies, middleware
    agents/              investigator and independent auditor agents
    core/                config, logging, constants
    database/            SQLAlchemy async engine/session
    models/              SQLAlchemy ORM models
    repositories/        database and filesystem repository patterns
    schemas/             Pydantic request/response schemas
    services/            repository, search, analysis, AI, session services
frontend/
  src/
    app/                 Next.js App Router
    components/          chat, repository, audit, shadcn-style UI components
    hooks/               React Query hooks
    services/            Axios API client
    types/               typed API contracts
```

## Investigation Flow

1. `POST /api/v1/repositories` validates a GitHub URL, clones it with
   GitPython, and indexes lightweight metadata from the filesystem.
2. `POST /api/v1/chat` creates or continues a repository-scoped session.
3. The investigator asks OpenAI for literal ripgrep search terms, runs ripgrep,
   expands hits into line-numbered code excerpts, and generates a grounded JSON
   answer.
4. The auditor runs separately with its own prompt and service flow. It checks
   file existence, line ranges, citation excerpts, unsupported claims, and
   contradictions.
5. Sessions, chat history, citations, audit logs, and repository metadata are
   stored in Postgres via SQLAlchemy ORM. SQLite still works as a local fallback
   when no database environment variables are configured.

## Requirements

- Python 3.12+
- Node.js 22+
- Git
- ripgrep (`rg`)
- OpenAI API key

## Environment

Create `.env` from `.env.example`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.5
OPENAI_AUDIT_MODEL=gpt-5.4-mini
DB_NAME=codebase_investigator
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
REPOSITORY_STORAGE_PATH=./data/repos
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

`DATABASE_URL` is also supported and takes precedence over `DB_*` variables.
Use the async driver form for Postgres:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:your-password@localhost:5432/codebase_investigator
```

When running against a local Postgres server, create the database first. The app
creates its own tables at startup, but it does not create the Postgres database:

```bash
createdb -U postgres codebase_investigator
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For local reload mode, keep `REPOSITORY_STORAGE_PATH=../data/repos` so cloned
repositories stay outside the backend watch tree.

FastAPI documentation is available at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Docker

```bash
docker compose up --build
```

The backend runs on port `8000`; the frontend runs on port `3000`.

## API Summary

### `POST /api/v1/repositories`

Request:

```json
{
  "url": "https://github.com/org/repo"
}
```

Response includes repository ID, clone status, branch, commit, file counts,
language counts, and indexed metadata.

### `GET /api/v1/repositories/{repo_id}`

Returns repository details and analysis metadata.

### `POST /api/v1/chat`

Request:

```json
{
  "repository_id": "uuid",
  "session_id": "uuid-or-null",
  "question": "How does authentication work?"
}
```

Response:

```json
{
  "session_id": "uuid",
  "answer": "Grounded answer text",
  "citations": [
    {
      "file": "backend/app/auth/jwt.py",
      "start_line": 10,
      "end_line": 72,
      "excerpt": "..."
    }
  ],
  "audit": {
    "verified": true,
    "warnings": [],
    "unsupported_claims": [],
    "checked_citations": [],
    "details": "..."
  },
  "reasoning_summary": "Searches and files inspected."
}
```

### `GET /api/v1/sessions/{session_id}`

Returns conversation history, citations, audit payloads, and compact memory.

## Quality Checks

```bash
cd backend
ruff check app
pytest

cd ../frontend
npm run typecheck
npm run build
```

## Notes

- Repository storage defaults to `backend/data/repos`.
- Postgres is used when `DB_NAME` and `DB_USER` are present. SQLite defaults to
  `backend/data/app.db` only when no database configuration is provided.
- The OpenAI model is configurable; the defaults favor strong code reasoning for
  generation and a smaller independent model for audit.
- The audit path is deliberately independent from answer generation.
