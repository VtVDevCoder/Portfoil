# ReviewPulse

B2B SaaS platform for AI-powered customer feedback analysis. Upload batches of reviews — get instant sentiment classification, categorization, urgency scoring, and an analytics dashboard.

---

## Architecture

## Architecture

<!-- prettier-ignore-start -->
┌──────────────┐    HTTP/JWT ┌──────────────────┐ Celery task ┌──────────────┐
│ React 18     │ ──────────▶ │ Django REST API  │ ──────────▶ │ Celery Worker│
│ TypeScript   │             │ Simple JWT Auth  │             │ (background) │
│ Recharts     │             │ Port 8000        │             └──────┬───────┘
│ Port 3000    │             └────────┬─────────┘                    │
└──────────────┘                      │                              │
                            ┌─────────▼──────────┐       ┌───────────▼────────┐
                            │ PostgreSQL 15      │       │ Gemini 1.5 Flash   │
                            │ (persistent data)  │       │ Structured Output  │
                            └────────────────────┘       └────────────────────┘
                                      │
                            ┌─────────▼──────────┐
                            │ Redis 7            │
                            │ (task queue)       │
                            └────────────────────┘
<!-- prettier-ignore-end -->

| Layer          | Technology                                                           |
| -------------- | -------------------------------------------------------------------- |
| Backend        | Python 3.12, Django 5, Django REST Framework, Simple JWT             |
| Frontend       | React 18, TypeScript, Vite, Tailwind CSS, Recharts                   |
| Async Queue    | Celery + Redis                                                       |
| Database       | PostgreSQL 15                                                        |
| AI             | Google Gemini 1.5 Flash (Structured JSON Output via Pydantic schema) |
| Infrastructure | Docker + Docker Compose                                              |

---

## Running Locally

```bash
# 1. Set your Gemini API key
export GEMINI_API_KEY=your_key_here

# 2. Start all services
docker-compose up --build

# 3. Apply database migrations (first run only)
docker-compose exec web python manage.py migrate
```

| Service      | URL                         |
| ------------ | --------------------------- |
| Frontend     | http://localhost:3000       |
| Backend API  | http://localhost:8000/api   |
| Django Admin | http://localhost:8000/admin |

---

## API Endpoints

| Method | Endpoint                   | Auth     | Description           |
| ------ | -------------------------- | -------- | --------------------- |
| `POST` | `/api/auth/register/`      | Public   | Create account        |
| `POST` | `/api/auth/login/`         | Public   | Get JWT tokens        |
| `POST` | `/api/auth/token/refresh/` | Public   | Refresh access token  |
| `POST` | `/api/feedback-batches/`   | Required | Upload feedback batch |
| `GET`  | `/api/feedback-batches/`   | Required | List user's batches   |
| `GET`  | `/api/dashboard-stats/`    | Required | Aggregated analytics  |

### Upload example

```bash
curl -X POST http://localhost:8000/api/feedback-batches/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"raw_text_list": ["App crashed on checkout", "Love the new UI!", "Support is too slow"]}'
```

Response `202 Accepted` — processing happens asynchronously.

---

## Key Design Decisions

**Why Celery + Redis?**  
AI inference takes 1–3 seconds per item. Processing 1,000 feedbacks synchronously would time out HTTP requests. Celery offloads each batch to background workers, returning `HTTP 202` immediately while work continues in the queue.

**Why Structured Outputs?**  
Gemini's `response_schema` enforces a strict Pydantic schema on every response, eliminating JSON parse errors and hallucinated fields entirely — no brittle regex parsing.

**Why JWT?**  
Stateless authentication scales horizontally without shared session storage, fitting the distributed Docker + Celery architecture.

---

## Running Tests

```bash
docker-compose exec web pytest --cov=reviews --cov-report=term-missing
```
