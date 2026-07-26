# Deployment Guide

Complete instructions for deploying the Enterprise AI Assistant to production environments.

## Deployment Architectures

### Architecture 1: Separate Deployments (Recommended)

```
┌─────────────────┐         ┌──────────────────┐
│  Streamlit UI   │         │  FastAPI Backend │
│ (Streamlit.io)  │────────▶│   (Render/Cloud  │
│                 │         │   Run/Heroku)    │
└─────────────────┘         └──────────────────┘
                                     │
                            ┌────────▼────────┐
                            │  PostgreSQL      │
                            │  (Managed)       │
                            └──────────────────┘
```

**Benefits**:
- Independent scaling
- Separate CI/CD pipelines
- Database isolation
- Clear separation of concerns

### Architecture 2: Containerized on Single Cloud

```
┌────────────────────────────────────┐
│  Docker Container (Cloud Run/App)  │
│  ┌──────────┐  ┌──────────────┐   │
│  │ FastAPI  │  │  Streamlit   │   │
│  │ Backend  │  │  Frontend    │   │
│  └──────────┘  └──────────────┘   │
└────────────────────────────────────┘
              │
       ┌──────▼────────┐
       │  PostgreSQL   │
       │  (Managed)    │
       └───────────────┘
```

**Benefits**:
- Simpler deployment
- Single configuration
- Unified scaling
- Reduced operational overhead

---

## Deployment Option 1: Streamlit Cloud + Render (Recommended)

Best for quick, easy deployment with minimal DevOps.

### Frontend: Streamlit Cloud

#### Prerequisites
- GitHub account
- Streamlit Cloud free tier

#### Steps

1. **Push to GitHub**:
   ```bash
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your GitHub repo, branch (`main`), and file (`app.py`)
   - Click "Deploy"

3. **Configure Secrets** (in Streamlit Cloud dashboard):
   - Click "Settings" → "Secrets"
   - Add:
     ```toml
     [backend]
     BACKEND_URL = "https://your-api-url.onrender.com"
     ```

4. **Your frontend is live** at: `https://username-enterprise-ai-assistant.streamlit.app`

### Backend: Render

#### Prerequisites
- Render account ([render.com](https://render.com))
- GitHub repository

#### Steps

1. **Create `render.yaml`** in repository root:
   ```yaml
   services:
     - type: web
       name: enterprise-ai-api
       env: python
       plan: standard
       buildCommand: pip install -r requirements.txt
       startCommand: gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app
       envVars:
         - key: JWT_SECRET
           generateValue: true
         - key: GEMINI_API_KEY
           sync: false
         - key: GEMINI_MODEL
           value: gemini-2.5-flash
         - key: DATABASE_URL
           sync: false
         - key: CORS_ORIGINS
           value: https://username-enterprise-ai-assistant.streamlit.app
   ```

2. **Connect to Render**:
   - Login to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Select your GitHub repo
   - Choose auto-deploy on push

3. **Configure Environment Variables**:
   - In Render dashboard, go to "Environment"
   - Add:
     - `GEMINI_API_KEY`: (get from Google AI Studio)
     - `DATABASE_URL`: (provide your PostgreSQL URL, see below)
     - `CORS_ORIGINS`: `https://username-enterprise-ai-assistant.streamlit.app`

4. **Deploy PostgreSQL** (Render):
   - In Render dashboard, click "New +" → "PostgreSQL"
   - Choose plan (free tier: 90 days, then paid)
   - Copy the connection string to `DATABASE_URL` in your web service

5. **Deploy**:
   - Render deploys automatically on GitHub push
   - Monitor in dashboard; first deploy takes ~5 min

6. **Your API is live** at: `https://your-api-url.onrender.com`

### Verify Deployment

```bash
# Test API
curl https://your-api-url.onrender.com/health

# Test frontend
# Open https://username-enterprise-ai-assistant.streamlit.app
```

---

## Deployment Option 2: Google Cloud Run (Advanced)

Best for production workloads with auto-scaling and Google Cloud ecosystem integration.

### Prerequisites
- Google Cloud account (with billing enabled)
- `gcloud` CLI installed
- Docker installed

### Steps

1. **Create `Dockerfile`** (if not present):
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt gunicorn
   COPY . .
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "backend.main:app"]
   ```

2. **Create `.gcloudignore`**:
   ```
   .git
   .gitignore
   venv/
   __pycache__/
   *.pyc
   .env
   uploads/
   data/
   ```

3. **Build and push to Google Container Registry**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/enterprise-ai-api:latest
   ```

4. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy enterprise-ai-api \
     --image gcr.io/YOUR_PROJECT_ID/enterprise-ai-api:latest \
     --platform managed \
     --region us-central1 \
     --memory 2Gi \
     --cpu 2 \
     --timeout 3600 \
     --set-env-vars JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))"),GEMINI_API_KEY=YOUR_KEY,DATABASE_URL=postgresql://...,CORS_ORIGINS=https://your-streamlit-url.streamlit.app
   ```

5. **Configure Cloud SQL** (PostgreSQL):
   - In Google Cloud Console, create Cloud SQL PostgreSQL instance
   - Get the connection string and set `DATABASE_URL`
   - Update Cloud Run environment variable

6. **Deploy Streamlit**:
   - Same as Streamlit Cloud option above
   - Point `BACKEND_URL` to your Cloud Run service URL (shown in output)

---

## Deployment Option 3: Docker Compose on VPS (Self-Hosted)

Best for full control, lower costs, and compliance requirements.

### Prerequisites
- Linux VPS (Ubuntu 20.04+ recommended)
- SSH access
- Domain name (optional but recommended)
- SSL certificate (or use Let's Encrypt)

### Steps

1. **SSH into your VPS**:
   ```bash
   ssh user@your-vps-ip
   ```

2. **Install Docker & Docker Compose**:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose git
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Clone Repository**:
   ```bash
   git clone https://github.com/pankajbhattacharjee/Enterprise-AI-Assistant.git
   cd Enterprise-AI-Assistant
   ```

4. **Configure `.env`** (production values):
   ```env
   JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
   GEMINI_API_KEY=your-key
   GEMINI_MODEL=gemini-2.5-flash
   DATABASE_URL=postgresql://postgres:strong-password@postgres:5432/enterprise_ai
   CORS_ORIGINS=https://your-domain.com
   BACKEND_URL=https://api.your-domain.com
   FAISS_INDEX_PATH=/app/data/faiss_index
   ```

5. **Update `docker-compose.yml`** for production:
   ```yaml
   version: '3.8'
   services:
     backend:
       build: .
       ports:
         - "8000:8000"
       environment:
         - JWT_SECRET=${JWT_SECRET}
         - GEMINI_API_KEY=${GEMINI_API_KEY}
         - DATABASE_URL=${DATABASE_URL}
         - CORS_ORIGINS=${CORS_ORIGINS}
       depends_on:
         - postgres
       restart: unless-stopped
       volumes:
         - ./data:/app/data
         - ./uploads:/app/uploads
     
     frontend:
       build:
         context: .
         dockerfile: Dockerfile.streamlit
       ports:
         - "8501:8501"
       environment:
         - BACKEND_URL=${BACKEND_URL}
       depends_on:
         - backend
       restart: unless-stopped
     
     postgres:
       image: postgres:15
       environment:
         - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
         - POSTGRES_DB=enterprise_ai
       volumes:
         - postgres_data:/var/lib/postgresql/data
       restart: unless-stopped
   
   volumes:
     postgres_data:
   ```

6. **Create Nginx reverse proxy** (`/etc/nginx/sites-available/enterprise-ai`):
   ```nginx
   upstream api {
     server localhost:8000;
   }
   
   upstream ui {
     server localhost:8501;
   }
   
   server {
     listen 443 ssl http2;
     server_name api.your-domain.com;
     ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;
     
     location / {
       proxy_pass http://api;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
     }
   }
   
   server {
     listen 443 ssl http2;
     server_name your-domain.com;
     ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
     
     location / {
       proxy_pass http://ui;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
     }
   }
   ```

7. **Start Services**:
   ```bash
   docker-compose up -d
   docker-compose logs -f
   ```

8. **Setup SSL** (Let's Encrypt):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot certonly --nginx -d your-domain.com -d api.your-domain.com
   ```

9. **Setup monitoring** (optional):
   ```bash
   # Add health checks to docker-compose.yml
   # Setup log rotation
   # Monitor with Prometheus/Grafana
   ```

---

## Environment Variables for Production

| Variable | Description | Example |
|---|---|---|
| `JWT_SECRET` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` | `eG3xK9mL...` |
| `GEMINI_API_KEY` | From Google AI Studio | `AIzaSyD...` |
| `GEMINI_MODEL` | Model version | `gemini-2.5-flash` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `CORS_ORIGINS` | Allowed frontend URL | `https://your-domain.com` |
| `BACKEND_URL` | API base URL (for Streamlit) | `https://api.your-domain.com` |
| `FAISS_INDEX_PATH` | Vector index location | `/data/faiss_index` |

---

## Production Checklist

- [ ] Database backups enabled (daily minimum)
- [ ] Environment variables securely configured
- [ ] SSL/TLS certificates installed
- [ ] CORS properly configured (no wildcard `*`)
- [ ] Rate limiting enabled
- [ ] Logging aggregated (Datadog, ELK, etc.)
- [ ] Monitoring alerts setup (uptime, errors, latency)
- [ ] Load balancer in front (if traffic >1000 req/sec)
- [ ] Database connection pooling configured
- [ ] Horizontal scaling plan ready
- [ ] Disaster recovery tested
- [ ] Security audit completed

---

## Post-Deployment

### Verify Production Deployment

```bash
# Test health endpoint
curl https://api.your-domain.com/health

# Test CORS
curl -H "Origin: https://your-domain.com" https://api.your-domain.com/docs

# Monitor logs
docker-compose logs -f backend
```

### Monitoring & Maintenance

- **Daily**: Check logs for errors
- **Weekly**: Verify backups, test restore
- **Monthly**: Review performance metrics, capacity planning
- **Quarterly**: Security audit, dependency updates

### Scaling

When traffic grows:
1. **Horizontal**: Add more backend replicas with load balancer
2. **Caching**: Enable Redis for session/query caching
3. **Database**: Read replicas, connection pooling
4. **Storage**: CDN for document downloads

---

## Support & Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common deployment issues.
