# Production Deployment Guide

This guide details the steps required to deploy the AI-Powered Grievance Redressal System to a production environment using Docker and Docker Compose.

---

## 1. System Architecture
The system consists of three main containers coordinated over a bridge network:
1. **Database Container (`grievance-mongodb`)**: Official MongoDB 7.0 database persisting records and logs in mapped volumes.
2. **Backend API Container (`grievance-backend`)**: Python FastAPI application running the LangGraph state machine, database indexing, and AI ingestion routes.
3. **Frontend UI Container (`grievance-frontend`)**: Python Gradio application serving Citizens, Addressers, and Admins.

---

## 2. Prerequisites
Ensure the following packages are installed on the deployment host:
* **Docker Engine** (version 20.10.0 or later)
* **Docker Compose** (version 2.0.0 or later)
* **API Keys**:
  * **Groq API Key** (Required for LLM classification and Whisper transcription).
  * **Hugging Face Token** (Optional, for alternative LLM routing).

---

## 3. Configuration Setup

### Step 1: Initialize Environment Variables
Copy the `.env.example` template into a new `.env` file:
```bash
cp .env.example .env
```

### Step 2: Configure Production Secrets
Edit `.env` and configure the following parameters:
* **SECRET_KEY**: Generate a secure 32-character hexadecimal key:
  ```bash
  openssl rand -hex 32
  ```
  Paste this key as the value for `SECRET_KEY` in your `.env`.
* **MONGODB_URL**:
  * For local MongoDB container: `mongodb://admin:password123@mongodb:27017/grievance_db?authSource=admin`
  * For external MongoDB Atlas: paste your Atlas connection URI.
* **GROQ_API_KEY**: Paste your production Groq cloud key (`gsk_...`).
* **LLM_PROVIDER**: Set to `groq`.
* **PORT**: Set backend port (default: `8000`).

---

## 4. Container Controls & Deployment

### Build and Launch Services
Start the containers in detached (background) mode:
```bash
docker-compose up -d --build
```
This builds the application image (installing system dependencies like `ffmpeg` and `tesseract-tel`) and launches all services.

### Verify Deployment Status
* **List Running Containers**:
  ```bash
  docker-compose ps
  ```
* **Verify Health Endpoints**:
  * Backend Health Check: `http://localhost:8000/api/v1/health`
  * Frontend Portal: `http://localhost:7863`

---

## 5. Reverse Proxy & SSL (Recommended for Production)
For secure public access (HTTPS), uncomment the `nginx` service in [docker-compose.yml](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/docker-compose.yml) and map SSL certs:

```nginx
# Sample Nginx block inside container
server {
    listen 80;
    server_name grievance.yourdomain.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name grievance.yourdomain.gov.in;

    ssl_certificate /etc/nginx/ssl/live/grievance.yourdomain.gov.in/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/grievance.yourdomain.gov.in/privkey.pem;

    location / {
        proxy_pass http://frontend:7863;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 6. Monitoring & Troubleshooting

### Log Inspection
* **Backend Logs**:
  ```bash
  docker-compose logs -f backend
  ```
* **Frontend Logs**:
  ```bash
  docker-compose logs -f frontend
  ```
* **MongoDB Logs**:
  ```bash
  docker-compose logs -f mongodb
  ```

### Database Maintenance
Programmatic indexes are automatically checked and configured upon backend container startup. To execute manual database backups:
```bash
docker-compose exec mongodb mongodump --out /data/db/backups/
```
