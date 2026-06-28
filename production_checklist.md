# Production Readiness Checklist

This checklist tracks verification items required to transition the Grievance Redressal System from development to production.

---

## 🔒 1. Secrets & Credentials
- [ ] **Secure JWT Secrets**: Ensure the `SECRET_KEY` env variable is set to a secure, random hexadecimal string (generated via `openssl rand -hex 32`) and is NOT a default development placeholder.
- [ ] **Valid Groq Credentials**: Confirm that `GROQ_API_KEY` is loaded and represents a valid production API key to avoid slow/heavy local Whisper and Ollama fallback operations.
- [ ] **MongoDB Credentials**: Ensure default MongoDB credentials (`MONGO_ROOT_USERNAME=admin` and `MONGO_ROOT_PASSWORD=password123`) in `.env` are updated with strong random strings prior to service startup.
- [ ] **Config Exclusion**: Verify that the `.env` file containing secrets is added to `.gitignore` and is never committed to Git.

---

## 📦 2. Ingestion & Preprocessing Dependencies
- [ ] **OCR Engine Verification**: Confirm that `tesseract-ocr` is installed inside the target container environment, along with language packs for English (`tesseract-ocr-eng`) and Telugu (`tesseract-ocr-tel`).
- [ ] **FFmpeg Ingestion**: Ensure `ffmpeg` is available on the path to enable Whisper file preprocessing and voice input conversions.
- [ ] **Pillow & Magic Verification**: Validate python dependencies for image processing and magic format detection to enforce strict file limits (max 25MB).

---

## ⚡ 3. Performance & Scaling
- [ ] **Database Indexes**: Verify that programmatic indexing (`users` unique constraints, compound roles, compound created timestamp, and text search) is created successfully on startup.
- [ ] **LLM Rate-Limit Controls**: Validate that exponential backoff retries (3 attempts) are configured on `llm_service.py` to handle transient cloud rate-limits.
- [ ] **Worker Scaling**: Set `uvicorn` workers count to 2–4 workers depending on host CPU core availability, rather than running a single worker thread.

---

## 🩺 4. Health & Reliability
- [ ] **FastAPI Health Endpoint**: Ensure `/api/v1/health` returns status `200` and database connectivity is green.
- [ ] **Gradio Startup Sync**: Check that the frontend container starts after the backend has transitioned to a `service_healthy` status (configured via docker-compose healthchecks).
- [ ] **Container Restart Policies**: Ensure `restart: unless-stopped` is defined on all containers to recover from system reboots or daemon failures.
- [ ] **Data Persistence**: Verify that MongoDB data directory is mapped to a named Docker volume (`mongodb_data`) to prevent data loss when container instances are upgraded or rebuilt.

---

## 🛡️ 5. Networking & SSL
- [ ] **Nginx Reverse Proxy**: Deploy an Nginx container or API gateway wrapper to terminate SSL (HTTPS) and serve traffic securely on port 443.
- [ ] **CORS Settings**: Restrict `allow_origins=["*"]` in `main.py` to your specific frontend domain.
- [ ] **Stateless JWT Checks**: Enforce access/refresh token type separation inside middleware dependencies to protect all admin and department queues.
