# Voice AI Agent — Patient Registration System

A voice-based AI agent that collects patient demographic information through natural phone conversations, persists data to PostgreSQL, and exposes a REST API.

## Live Demo

- **Phone Number**: `+1 (XXX) XXX-XXXX` _(update after Vapi provisioning)_
- **API Base URL**: `http://<ec2-public-ip>:8000` _(update after deployment)_

## Architecture

```
Caller ──► Vapi (Phone + STT + TTS + LLM) ──► FastAPI Server ──► PostgreSQL (RDS)
                                                     │
                                                     ▼
                                              REST API (public)
```

1. **Caller** dials the Vapi-provisioned U.S. phone number
2. **Vapi** handles telephony, speech-to-text, text-to-speech, and LLM orchestration
3. **LLM (GPT-4o)** runs with a custom system prompt to conduct a natural intake conversation
4. When the caller confirms their info, the LLM invokes the **`save_patient` tool** — a webhook call to our FastAPI server
5. **FastAPI** validates the data with Pydantic and writes to **PostgreSQL on Amazon RDS**
6. The same server exposes a **REST API** for querying patient records

## Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Voice AI + Telephony | **Vapi** | Abstracts STT/TTS/telephony complexity. Lets us focus on prompt quality and backend logic. |
| LLM | **OpenAI GPT-4o** | Best conversational quality for voice. Handles varied phrasing, corrections, interruptions. |
| Backend | **Python + FastAPI** | Async support, automatic validation via Pydantic, auto-generated OpenAPI docs. |
| Database | **Amazon RDS PostgreSQL** | Managed, persistent, proper relational constraints. Survives restarts. |
| Hosting | **AWS EC2 (Dockerized)** | Full control, same cloud as RDS, reproducible deployment via Docker. |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/patients` | List all patients. Filters: `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| `GET` | `/patients/:id` | Get a single patient by UUID |
| `POST` | `/patients` | Create a new patient (with full validation) |
| `PUT` | `/patients/:id` | Update a patient (partial updates allowed) |
| `DELETE` | `/patients/:id` | Soft-delete (sets `deleted_at`, does not hard-delete) |

All responses use the envelope: `{ "data": {...}, "error": null }`

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- AWS account (for RDS + EC2 deployment)
- Vapi account (vapi.ai)
- OpenAI API key

### Local Development

```bash
# Clone the repository
git clone <repo-url>
cd care_cloud

# Create .env file
cp .env.example .env
# Edit .env with your VAPI_API_KEY

# Start with Docker Compose (includes local Postgres)
docker compose up --build
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Production Deployment (AWS)

1. **Create RDS PostgreSQL instance** (db.t3.micro, PostgreSQL 16)
2. **Launch EC2 instance** (t2.micro, Ubuntu 22.04)
3. **SSH into EC2 and deploy**:

```bash
sudo apt update && sudo apt install docker.io docker-compose-v2 git -y
sudo usermod -aG docker $USER && newgrp docker

git clone <repo-url>
cd care_cloud

cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://user:pass@your-rds-endpoint:5432/care_cloud
VAPI_API_KEY=your-vapi-api-key
EOF

docker build -t care-cloud .
docker run -d --name care-cloud --env-file .env -p 8000:8000 --restart unless-stopped care-cloud
```

4. **Configure Vapi** to point the tool server URL to `http://<ec2-public-ip>:8000/vapi/tool-call`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg format) | Yes |
| `VAPI_API_KEY` | Vapi API key for authentication | Yes |

## Voice Agent Prompt

The full system prompt is documented in [`vapi_config/agent_prompt.md`](vapi_config/agent_prompt.md), including:
- Conversational flow design
- Validation rules
- Edge case handling (corrections, interruptions, starting over)
- Tool definitions for Vapi

## Known Limitations & Trade-offs

- **No HTTPS on EC2**: For a 3-hour challenge, the server runs on HTTP. Production would use Nginx + Let's Encrypt or an ALB.
- **No authentication on the REST API**: The API is open. Production would add API key auth or OAuth.
- **No HIPAA compliance**: This is a technical demo, not a production healthcare system.
- **SQLAlchemy `create_all`**: Tables are auto-created on startup instead of using Alembic migrations. Fine for a demo; production would use proper migrations.
- **Single EC2 instance**: No load balancing or auto-scaling. Single point of failure.

## Next Steps (with more time)

- Add HTTPS with Nginx reverse proxy + Let's Encrypt SSL
- Add API authentication (API key or JWT)
- Implement Alembic migrations for proper schema versioning
- Add automated tests (pytest + httpx for async API testing)
- Build a simple web dashboard to view registered patients
- Add call transcript storage linked to patient records
- Implement appointment scheduling as a follow-up action
- Add multi-language support (Spanish, Creole)
- Set up CloudWatch logging and health monitoring
