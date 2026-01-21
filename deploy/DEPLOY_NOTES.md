# Deployment Notes

These instructions describe how to run the LENA pilot stack with the recommended cloud targets: Netlify for the Next.js frontend and a DigitalOcean Droplet for the FastAPI API plus Qdrant.

## 1. Prerequisites

- Docker Engine 24+ on your local workstation.
- DigitalOcean account with the ability to create Droplets and Firewalls.
- Netlify account with GitHub integration enabled.
- Optional: Domain or subdomain to point at the Netlify site and DigitalOcean load balancer.

## 2. Backend + Qdrant on DigitalOcean

1. **Create Droplet**
   - Marketplace image: "Docker 24.x on Ubuntu 22.04".
   - Size: at least 2 vCPUs / 4 GB RAM for comfortable CPU inference.
   - Enable SSH keys and private networking.
2. **Clone repository**
   ```bash
   ssh root@YOUR_DROPLET_IP
   git clone https://github.com/watrall/lena.git
   cd lena
   ```
3. **Configure environment**
   - Create `.env` in `backend/` with production values, for example:
     ```env
     LENA_LLM_MODE=hf
     LENA_HF_MODEL=HuggingFaceH4/zephyr-7b-beta
     LENA_QDRANT_HOST=qdrant
     LENA_STORAGE_DIR=/data/storage
     ```
   - Copy sanitized course data into `data/`.
4. **Run Docker Compose**
   ```bash
   cd docker
   docker compose up -d
   ```
   - This boots Qdrant, the FastAPI service (`api`), and an auxiliary dev web container (`web`). For production, deploy frontend separately (see next section) and optionally disable `web`.
5. **Configure firewall**
   - Allow inbound ports: `80/443` (if terminating TLS), `8000` for API (or front it with Nginx), and restrict `6333` to private access only.
6. **Health check**
   ```bash
   curl http://localhost:8000/healthz
   curl -X POST http://localhost:8000/ingest/run
   ```
7. **Sample smoke test**
   ```bash
   curl -s -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"When is Assignment 1 due?"}' | jq
   ```

## 3. Frontend on Netlify

1. **Create new site** from Git → GitHub → select `lena`.
2. **Build settings**
   - Build command: `npm run build`
   - Publish directory: `frontend/.next`
   - Base directory: `frontend`
3. **Environment variables**
   - `NEXT_PUBLIC_API_BASE=https://your-api-domain.edu` (point at the FastAPI endpoint exposed from DigitalOcean or your reverse proxy).
4. **Deploy**
   - Netlify will run `npm ci && npm run build` using the `package-lock.json`.
   - Verify the banner shows "Pilot Mode - No login. Sample data only."

## 4. Post-Deployment Checklist

- [ ] Run `curl http://API_DOMAIN/healthz` from your workstation to ensure ingress is open.
- [ ] Visit `https://your-netlify-site.netlify.app` and ask "When is Assignment 1 due?" - confirm citation links work.
- [ ] Submit a "Not helpful" response and promote it via `POST /admin/promote` to verify storage permissions.
- [ ] Review `/insights` for aggregate metrics.
- [ ] Configure HTTPS (Netlify handles TLS automatically; for the backend use Let’s Encrypt or DigitalOcean’s managed certificates).

## 5. CORS Example (FastAPI)

Add the middleware to `backend/app/main.py` before including routers:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-netlify-site.netlify.app",
        "https://your-campus-domain.edu",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 6. Health Check Script (cURL)

Useful for uptime monitors:

```bash
#!/usr/bin/env bash
set -euo pipefail

API="${1:-https://your-api-domain.edu}"

curl -fsSL "$API/healthz"
curl -fsSL -X POST "$API/ingest/run"
curl -fsSL -X POST "$API/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"When is Assignment 1 due?"}'
```

## 7. Scaling Thoughts

- Swap the JSONL storage for managed Postgres or DynamoDB to support concurrent feedback at scale.
- Configure autosensing logging (e.g., DigitalOcean tailing or Datadog) to monitor ingest and ask latency.
- Move from CPU inference to GPU or hosted endpoints when the question volume or team accuracy requirements grow.
