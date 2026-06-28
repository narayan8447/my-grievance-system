# Configuration Refactor Report — Centralized Settings

This report summarizes the refactoring changes applied to establish a single source of truth for runtime configurations, eliminating raw environment fetching and static constants.

---

## 🎯 Refactoring Objectives Met

1. **Removed Raw Environment Calls (`os.getenv`)**: Direct calls to `os.getenv` in `app/utils/security.py` were replaced with properties loaded from the validated `settings` instance.
2. **Eliminated Hardcoded Connections (`API_BASE_URL`)**: The hardcoded API URL inside `gradio_app.py` was replaced with the centralized Pydantic settings parameter `settings.API_BASE_URL`.
3. **Established Fail-Fast Validation**: The Settings class was updated to make `MONGODB_URL` and `SECRET_KEY` required, failing startup immediately if either is missing.
4. **Conditional Requirements Validation**: Implemented Pydantic `@model_validator` checks to enforce key requirements for Groq/HuggingFace APIs depending on the selected LLM provider.

---

## 🛠️ Refactored Components

### 1. Centralized Settings: [config.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/config.py)
* **Changes**:
  * Made `MONGODB_URL: str` required (removed the empty default fallback).
  * Added `API_BASE_URL: str = "http://localhost:8000/api/v1"` under the Server section.
  * Added a `@model_validator(mode="after")` to verify that `GROQ_API_KEY` or `HUGGINGFACE_API_KEY` is present if they are selected as the provider.
* **Why**: Prevents silent startup failures and consolidates Gradio routing properties.

### 2. Token Security: [security.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/utils/security.py)
* **Changes**:
  * Removed `import os`.
  * Imported `from app.config import settings`.
  * Replaced `os.getenv("SECRET_KEY", "")` with `settings.SECRET_KEY`.
  * Replaced token expiration `os.getenv` calls with `settings.ACCESS_TOKEN_EXPIRE_MINUTES` and `settings.REFRESH_TOKEN_EXPIRE_MINUTES`.
* **Why**: Solves a critical bug where `os.getenv` returned `None` due to missing `load_dotenv` calls, which caused JWTs to be signed with insecure empty string keys (`""`).

### 3. Gradio Frontend Interface: [gradio_app.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/gradio_app.py)
* **Changes**:
  * Imported `from app.config import settings`.
  * Replaced hardcoded `API_BASE_URL = "http://localhost:8000/api/v1"` with `settings.API_BASE_URL`.
* **Why**: Enables Docker Compose to inject the correct backend gateway address (`http://backend:8000/api/v1`) via environment variables, resolving container-to-container connection failures.

---

## 🧪 Refactor Verification & Testing
- **Command Executed**: `python -m pytest`
- **Verification Result**: **9 passed successfully** in 41.97s.
- **Outcome**: Confirmed that all token generation, refresh endpoints, user roles validation, and E2E integration tests compile and run successfully with the centralized config.
