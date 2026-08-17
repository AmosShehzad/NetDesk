# NetDesk — AI-Powered ISP Customer Support Platform

An intelligent customer support system for Internet Service Providers, featuring an **agentic AI assistant** that investigates issues, searches knowledge bases, and autonomously resolves tickets — escalating to human agents only when necessary.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React 19)                      │
│              Vite · React Router · Axios · Recharts             │
│         Customer Portal  ·  Staff Dashboard  ·  Chat UI         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (JWT)
┌────────────────────────────▼────────────────────────────────────┐
│                     Backend (Django + DRF)                       │
│                                                                 │
│  Users ──── Tickets ──── Billing ──── Notifications             │
│  (RBAC)    (Lifecycle)   (Invoices)   (Signals + Announcements) │
│                │                                                │
│                │ httpx                                          │
│    ┌───────────▼───────────┐                                    │
│    │   AI Service (FastAPI) │                                   │
│    │                       │                                    │
│    │   LangGraph Agent     │                                    │
│    │   ├─ Intent Router    │                                    │
│    │   ├─ RAG Knowledge Base│                                   │
│    │   ├─ Tool Executor    │                                    │
│    │   └─ Escalation Logic │                                    │
│    │                       │                                    │
│    │   Groq (Llama 3.1)   │                                    │
│    │   FAISS + Embeddings  │                                    │
│    └───────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────┘
                             │
                    PostgreSQL (Supabase)
```

## Key Features

### Agentic AI System
- **Multi-step reasoning** — AI classifies, investigates, and resolves in a single turn
- **Tool use** — Agent queries billing data, checks outage status, searches knowledge base
- **RAG** — Vector search over ISP troubleshooting guides using FAISS
- **Smart escalation** — Confidence-based handoff with AI-generated summary for human agents
- **Conversation memory** — Full ticket history sent as context for coherent multi-turn support

### Backend
- **5-role RBAC** — Customer, Support Agent, Technician, Manager, Admin
- **Ticket lifecycle** — Open → Assigned → In Progress → Waiting → Resolved → Closed
- **Auto-generated IDs** — Registration numbers (CUST-2026-00001) and ticket numbers (TKT-2026-00001)
- **SLA tracking** — Priority-based deadlines with breach detection
- **Notification system** — Signal-driven alerts on every ticket event + broadcast announcements
- **Billing module** — Monthly invoices managed by staff, read-only for customers
- **Activity audit log** — Every action on a ticket is tracked
- **API docs** — Auto-generated Swagger UI via drf-spectacular

### Frontend
- **Customer portal** — Dashboard, ticket management, chat with AI, billing view
- **Staff dashboard** — Analytics, agent workload, SLA compliance, escalation queue
- **Chat UI** — Real-time messaging with typing indicators and AI badges
- **Responsive design** — Mobile-friendly with collapsible sidebar

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 19, Vite, React Router | Fast dev experience, modern React |
| Backend | Django 6.1, DRF, SimpleJWT | Battle-tested, great ORM, built-in admin |
| AI Service | FastAPI, LangGraph, Groq | Async API, stateful agent graphs, fast inference |
| LLM | Llama 3.1 8B (via Groq) | Free tier, fast, good for classification |
| Vector DB | FAISS | Lightweight, no infra needed |
| Database | PostgreSQL (Supabase) | Reliable, hosted |
| Deployment | Render (backend + AI) · Vercel (frontend) | Free tier, easy CI/CD |

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/netdesk.git
cd netdesk

# Copy environment files
cp backend/.env.example backend/.env
cp ai-service/.env.example ai-service/.env
cp frontend/.env.example frontend/.env
# Fill in your actual values

# Run with Docker
docker-compose up --build

# Or run manually:

# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# AI Service (separate terminal)
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --port 8001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## API Documentation

Once the backend is running, visit: `http://localhost:8000/api/docs/`

## Screenshots

> *Coming soon*

## License

MIT
