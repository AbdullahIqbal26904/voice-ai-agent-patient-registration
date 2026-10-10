# Voice AI Agent — Patient Registration System

A voice-based AI agent that collects patient demographic information through natural phone conversations, persists data to PostgreSQL, and exposes a REST API.

## Live Demo

- **Phone Number**: `+1 (267) 933-9058`
- **API Base URL**: `https://voice.nidassalon.com`
- **Dashboard**: `https://voice.nidassalon.com/dashboard`
- **API Docs**: `https://voice.nidassalon.com/docs`

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
6. The same server exposes a **REST API** for querying patient records and a **web dashboard** for viewing them

## Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Voice AI + Telephony | **Vapi** | Abstracts STT/TTS/telephony complexity. Lets us focus on prompt quality and backend logic. |
| LLM | **OpenAI GPT-4o** | Best conversational quality for voice. Handles varied phrasing, corrections, interruptions. |
| Backend | **Python + FastAPI** | Async support, automatic validation via Pydantic, auto-generated OpenAPI docs. |
| Database | **Amazon RDS PostgreSQL** | Managed, persistent, proper relational constraints. Survives restarts. |
| Hosting | **AWS EC2 (Dockerized)** | Full control, custom domain with HTTPS via Nginx + Let's Encrypt. |
| Reverse Proxy | **Nginx + Let's Encrypt** | SSL termination, HTTP-to-HTTPS redirect, auto-renewing certificates. |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/patients` | List all patients. Filters: `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| `GET` | `/patients/:id` | Get a single patient by UUID |
| `POST` | `/patients` | Create a new patient (with full validation) |
| `PUT` | `/patients/:id` | Update a patient (partial updates allowed) |
| `DELETE` | `/patients/:id` | Soft-delete (sets `deleted_at`, does not hard-delete) |
| `GET` | `/dashboard` | Web dashboard for viewing patient records |

All responses use the envelope: `{ "data": {...}, "error": null }`

---

## AWS Deployment

This application is deployed on AWS using **EC2** for the Dockerized backend and **RDS** for the managed PostgreSQL database. HTTPS is provided via **Nginx** + **Let's Encrypt** using an existing domain from Namecheap.

### Infrastructure Overview

```
Internet ──► voice.nidassalon.com (DNS A Record)
                  │
                  ▼
          Elastic IP: 13.238.49.172
                  │
                  ▼
     ┌─── EC2 Instance (c7i.flex.large) ───┐
     │                                      │
     │  ┌──────────┐    ┌───────────────┐  │
     │  │  Nginx   │───►│  FastAPI App   │  │
     │  │ (SSL/443)│    │  (port 8000)  │  │
     │  └──────────┘    └───────┬───────┘  │
     │  ┌──────────┐            │          │
     │  │ Certbot  │            │          │
     │  │(auto SSL)│            │          │
     │  └──────────┘            │          │
     └──────────────────────────┼──────────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │  Amazon RDS       │
                    │  PostgreSQL 16    │
                    │  (ap-southeast-2) │
                    └───────────────────┘
```

### Step 1: EC2 Instance

An EC2 instance named **`voice-ai-agent`** was launched in the **ap-southeast-2** (Sydney) region running Ubuntu 26.04 LTS.

- **Instance ID**: `i-037d26323daec572c`
- **Instance Type**: `c7i.flex.large`
- **Region/AZ**: `ap-southeast-2a`
- **Private IP**: `172.31.6.29`
- **Security Group**: Inbound rules allow ports 22 (SSH), 80 (HTTP), and 443 (HTTPS)

![EC2 Instance running in AWS Console](screenshots/ec2_instance.png)

### Step 2: Elastic IP

An **Elastic IP** was allocated and associated with the EC2 instance to ensure the public IP address remains fixed across instance restarts — critical for DNS resolution.

- **Elastic IP**: `13.238.49.172`
- **Allocation ID**: `eipalloc-07940d11f889e1e14`
- **Associated Instance**: `i-037d26323daec572c` (voice-ai-agent)

![Elastic IP allocated and associated with EC2](screenshots/elastic_ip.png)

### Step 3: Domain & HTTPS (Namecheap + Let's Encrypt)

The domain **nidassalon.com** was already registered on Namecheap. Instead of purchasing a new domain, a **subdomain** was created by adding an A record in Namecheap's DNS settings:

| Record Type | Host | Value | TTL |
|-------------|------|-------|-----|
| A Record | `voice` | `13.238.49.172` | Automatic |

This points `voice.nidassalon.com` to the EC2 Elastic IP.

**SSL/HTTPS** was configured using **Let's Encrypt** via **Certbot** running as a Docker container. The setup uses:
- **Nginx** as a reverse proxy — terminates SSL on port 443 and proxies requests to the FastAPI app on port 8000
- **Certbot** running in a container that auto-renews the certificate every 12 hours
- All HTTP traffic on port 80 is automatically redirected to HTTPS

### Step 4: Dockerized Deployment on EC2

The application runs as three Docker containers orchestrated with Docker Compose:

1. **app** — FastAPI application (gunicorn + uvicorn workers)
2. **nginx** — Reverse proxy with SSL termination
3. **certbot** — Automatic certificate renewal

![SSH into EC2 showing Docker containers running](screenshots/ubuntu_ssh.png)

The SSH session shows all three containers running:
- `voice-ai-agent-patient-registration-app-1` — The FastAPI backend
- `voice-ai-agent-patient-registration-nginx-1` — Nginx handling ports 80 and 443
- `voice-ai-agent-patient-registration-certbot-1` — Certbot for SSL renewal

### Step 5: RDS PostgreSQL

An Amazon RDS PostgreSQL instance provides the persistent database:

- **Engine**: PostgreSQL 16
- **Instance**: `db.t3.micro`
- **Region**: `ap-southeast-2` (same region as EC2 for low latency)
- **Database Name**: `postgres`
- **Security Group**: Allows inbound on port 5432 from the EC2 instance's security group

Data persists across application restarts. Patients registered via phone call on Call 1 are available via the API and dashboard on Call 2.

---

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- AWS account (for RDS + EC2)
- Vapi account (vapi.ai)
- OpenAI API key
- A domain name (for HTTPS)

### Local Development

```bash
# Clone the repository
git clone <repo-url>
cd care_cloud

# Create .env file
cp .env.example .env
# Edit .env with your DATABASE_URL and VAPI_API_KEY

# Start with Docker Compose (includes local Postgres)
docker compose up --build
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Production Deployment (AWS EC2 + RDS + Nginx HTTPS)

**1. Create RDS PostgreSQL instance**
- Engine: PostgreSQL 16, Instance: `db.t3.micro`
- Security group: allow inbound on port 5432 from your EC2 security group

**2. Launch EC2 instance** (Ubuntu, any size)
- Security group: allow inbound on ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Allocate and attach an Elastic IP

**3. Point your domain to EC2**
- Add an A Record in your DNS provider pointing to the EC2 Elastic IP
- Wait for DNS propagation

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
DATABASE_URL=postgresql+asyncpg://user:pass@your-rds-endpoint:5432/dbname
VAPI_API_KEY=your-vapi-api-key
EOF

# Start services (HTTP first for SSL cert)
sed -i 's|./nginx/nginx.conf|./nginx/nginx.init.conf|' docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d app nginx

# Get SSL certificate
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d voice.nidassalon.com --email your@email.com --agree-tos --no-eff-email

# Switch to full HTTPS config and restart
git checkout docker-compose.prod.yml
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

**5. Configure Vapi** to point the tool server URL to `https://voice.nidassalon.com/vapi/tool-call`

**6. Verify**: `curl https://voice.nidassalon.com/patients`

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
- **RDS security group**: For simplicity, the RDS instance accepts connections from the EC2 security group. Production would use VPC peering or private subnets.

## Next Steps (with more time)

- Add API authentication (API key or JWT)
- Implement Alembic migrations for proper schema versioning
- Add automated tests (pytest + httpx for async API testing)
- Add call transcript storage linked to patient records
- Implement appointment scheduling as a follow-up action
- Add multi-language support (Spanish, Creole)
- Set up CloudWatch logging and health monitoring
- Add VPC private networking between EC2 and RDS
