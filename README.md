# Voice AI Agent — Patient Registration System

A voice-based AI agent that collects patient demographic information through natural phone conversations, persists data to PostgreSQL, and exposes a REST API.

## Live Demo

- **Phone Number**: `+1 (XXX) XXX-XXXX` _(update after Vapi provisioning)_
- **API Base URL**: `https://voice.nidassalon.com` _(update with your domain)_

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
| Hosting | **AWS EC2 (Dockerized)** | Full control, custom domain with HTTPS via Nginx + Let's Encrypt. |

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

### Production Deployment (AWS EC2 + RDS + Nginx HTTPS)

**1. Create RDS PostgreSQL instance** (db.t3.micro, PostgreSQL 16)
- Security group: allow inbound on port 5432 from your EC2 security group

**2. Launch EC2 instance** (t2.micro, Ubuntu 22.04)
- Security group: allow inbound on ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Attach an Elastic IP so the IP stays fixed

**3. Point your Namecheap domain to EC2**
- In Namecheap DNS settings, add an **A Record**:
  - Host: `@` (or subdomain like `api`)
  - Value: your EC2 Elastic IP
  - TTL: Automatic
- Wait a few minutes for DNS propagation

**4. SSH into EC2 and deploy**

```bash
# Install Docker
sudo apt update && sudo apt install docker.io docker-compose-v2 git -y
sudo usermod -aG docker $USER && newgrp docker

# Clone repo
git clone <your-repo-url>
cd care_cloud

# Create .env
cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://user:pass@your-rds-endpoint:5432/care_cloud
VAPI_API_KEY=your-vapi-api-key
EOF

# Replace voice.nidassalon.com in nginx config
sed -i 's/voice.nidassalon.com/yourdomain.com/g' nginx/nginx.conf

# Step 1: Get SSL certificate (start Nginx on port 80 first)
docker compose -f docker-compose.prod.yml up -d app nginx
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d yourdomain.com --email your@email.com --agree-tos --no-eff-email

# Step 2: Restart Nginx to load the SSL cert
docker compose -f docker-compose.prod.yml restart nginx
```

**5. Configure Vapi** to point the tool server URL to `https://yourdomain.com/vapi/tool-call`

**6. Verify**: `curl https://yourdomain.com/patients` should return patient data

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

- **No authentication on the REST API**: The API is open. Production would add API key auth or OAuth.
- **No HIPAA compliance**: This is a technical demo, not a production healthcare system.
- **SQLAlchemy `create_all`**: Tables are auto-created on startup instead of using Alembic migrations. Fine for a demo; production would use proper migrations.
- **RDS publicly accessible**: For simplicity, RDS accepts connections from any IP. Production would use VPC peering or private networking.

## Next Steps (with more time)

- Add API authentication (API key or JWT)
- Implement Alembic migrations for proper schema versioning
- Add automated tests (pytest + httpx for async API testing)
- Build a simple web dashboard to view registered patients
- Add call transcript storage linked to patient records
- Implement appointment scheduling as a follow-up action
- Add multi-language support (Spanish, Creole)
- Set up CloudWatch logging and health monitoring
