# Release Notes — Grievance Redressal System v2.0.0

This release marks the transition of the intelligent Grievance Redressal System to **production-ready** status. It incorporates major security updates, backend bug fixes, database index configurations, E2E integration test coverages, and frontend enhancements.

---

## 🚀 New Features

### 1. Dual-Path Citizen Ingestion
* **Guided Chatbot Submission**: Step-by-step conversational chatbot assistant (`Grievance Assistant`) directing citizens through text/voice input, location tagging, and file attachments.
* **Traditional Form Submission**: Single-page input form (text, language, location, and multiple file uploads in one view) for rapid complaint ingestion, aligning with all README specifications.

### 2. Multi-Modal Analysis Pipelines
* **OCR pre-processing**: Bilingual (English + Telugu) OCR text extraction with Pillow contrast and noise sharpening. Deterministic regex entity fallback when LLM parsing fails.
* **Speech-to-Text Ingestion**: Validates file formats and enforces size limits (1KB-25MB). Features fallback from Groq cloud Whisper to local Whisper models, and client-side Google Speech recognition.

### 3. Production Security & Auth
* **Argon2 Secure Hashing**: Implements Argon2id as the default user password hashing scheme, with Bcrypt verification fallbacks.
* **Access & Refresh JWT Tokens**: Separated token validation claims, preventing token type confusion. Exposed `/api/v1/auth/refresh` route for stateless session renewal.

### 4. Database Optimizations
* **Programmatic Index Creation**: Creates unique indexes (`user_id`, `email`, `phone`, `grievance_id`) and compound sorting/filtering indexes dynamically on database initialization.
* **RAG Retrieval**: Metadata-driven retrieval matching resolved cases, sorted chronologically (`resolved_at` desc) to construct references for redressal chains.

---

## 🛠️ Resolved Issues & Bug Fixes

* **MongoDB Path Conflict (Admin Reassignment)**: Fixed a database write conflict in [admin.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/api/routes/admin.py) where the backend attempted to update the top-level `assignment` field and push to nested `assignment.assignment_history` concurrently. Resolved by nesting the history updates directly inside the top-level dictionary payload prior to database update calls.
* **JWT Namespace Collision**: Replaced standard `jwt` references with explicit `from jose import jwt` imports in [security.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/utils/security.py) to prevent conflicts in environments where both PyJWT and python-jose are present.
* **Docker Compose Frontend File**: Resolved container failure by correcting the volume mount and execution command filename references in [docker-compose.yml](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/docker-compose.yml).
* **LangChain Alternative Workflow**: Fixed unimportable module references and geospatial dependencies inside the backup [langchain_workflow.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/workflows/langchain_workflow.py).

---

## 📋 System Prerequisites

* **Docker Engine** (20.10.0+) and **Docker Compose** (2.0.0+)
* **Tesseract OCR Engine** installed with English (`eng`) and Telugu (`tel`) data packs.
* **FFmpeg** installed on the deployment host.

---

## ⚡ Quick Start
To build and launch the production application stack:
```bash
# 1. Initialize env settings
cp .env.example .env

# 2. Start all services
docker-compose up -d --build
```
Verify the health endpoint at `http://localhost:8000/api/v1/health` and open the web portal at `http://localhost:7863`.
