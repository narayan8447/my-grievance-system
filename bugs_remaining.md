# Remaining Bugs & Warnings

This document lists the remaining warnings, minor issues, environment-specific prerequisites, and future optimization points identified during Phase 16 Integration Testing.

---

## 1. Environment-Specific Caveats

### Tesseract OCR Binary Path (Windows)
* **Status**: Warning / Configuration Prerequisite.
* **Detail**: In [image_service.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/services/image_service.py), the Tesseract execution path defaults to `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows systems. If Tesseract is not installed there, OCR text extraction will fail gracefully and log a fallback error, returning `success: False` in the OCR state.
* **Resolution**: Install Tesseract OCR or add the custom path to the `.env` file for environments outside Docker containers.

### Local Whisper Ingestion Requirements
* **Status**: Dependency Requirement.
* **Detail**: If the primary Groq cloud Whisper API is unavailable, the system falls back to a local `openai-whisper` model. Loading this model on low-memory or CPU-only developer machines can result in initialization latencies of 15–30 seconds on the first run.
* **Resolution**: Keep Groq credentials valid in the environment to avoid local model fallback overhead, or ensure CUDA is enabled if running locally.

---

## 2. Code Warnings & Deprecations (Runtime Diagnostics)

### Python 3.12 datetime deprecation warnings
* **Status**: Warning.
* **Detail**: The Python interpreter reports `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version.` across several files (e.g. `auth_service.py`, `security.py`, `admin.py`, `addresser.py`, `citizen.py`).
* **Resolution**: In a future refactoring cycle, replace occurrences of `datetime.utcnow()` with `datetime.now(datetime.UTC)` to comply with Python 3.12+ timezone requirements.

### Pydantic V2 Class-based Config Deprecation
* **Status**: Warning.
* **Detail**: The system uses `class Config` for model configuration in [config.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/config.py) and [schemas.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/models/schemas.py), throwing:
  `PydanticDeprecatedSince20: Support for class-based config is deprecated, use ConfigDict instead.`
* **Resolution**: Replace `class Config:` inner declarations with `model_config = ConfigDict(...)` imports from `pydantic`.

---

## 3. Future Architectural Enhancements

### Stateless JWT Logout Revocation
* **Status**: Security Enhancement.
* **Detail**: There is no server-side token deny-list (or block-list) implemented for revoked tokens. When a user clicks "Logout" in Gradio, the client discards the JWT token, but the token remains technically valid on the backend until its expiration time passes.
* **Resolution**: Implement a Redis-based block-list for revoked access tokens to enable instant server-side revocation on user logout.
