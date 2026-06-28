# Environment Variable Audit — Grievance Redressal System

This document details the environment variable verification audit for the Grievance Redressal System. It scans the repository for `os.getenv()`, `os.environ`, Pydantic's `BaseSettings`/`Settings()`, `config.py`, and `dotenv`, analyzing how variables are declared, validated, and consumed.

---

## 🔍 1. Repository Scan Results

A complete search of the codebase was conducted for the target terms. The findings reveal a split configuration design:
1. **Pydantic Configuration (`app/config.py`)**: Defines `Settings` inheriting from `BaseSettings` which reads variables from `.env` or system environment. It is instantiated once as `settings = Settings()`.
2. **Direct Environment Fetching (`app/utils/security.py`)**: Directly calls `os.getenv` to read JWT configurations.
3. **Environment Setup Scripts**: Virtual environments and compose configuration files inject environment parameters.

---

## 📊 2. Environment Variable Audit Table

| Variable Name | Required? | Default Value | File Used | Line Number | Purpose | Example Value | Can Application Start Without It? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`MONGODB_URL`** | **Yes** | `""` | `app/config.py`<br>`app/models/database.py` | Line 10<br>Line 20 | Connection URL for the MongoDB instance. | `mongodb://localhost:27017` | **No**. Application Lifespan pings database on startup. Crashing if empty or invalid. |
| **`DATABASE_NAME`** | No | `"grievance_db"` | `app/config.py`<br>`app/models/database.py` | Line 11<br>Line 97 | Name of the database to create/query. | `"grievance_db"` | Yes (falls back to default). |
| **`LLM_PROVIDER`** | No | `"ollama"` | `app/config.py`<br>`app/services/llm_service.py`<br>`app/services/audio_service.py` | Line 14<br>Line 35<br>Line 42 | Inference engine selector (`ollama`, `groq`, `huggingface`). | `"groq"` | Yes (falls back to default). |
| **`OLLAMA_BASE_URL`** | No | `""` | `app/config.py`<br>`app/services/llm_service.py` | Line 17<br>Line 55 | Connection URL for local Ollama service. | `http://localhost:11434` | Yes. |
| **`OLLAMA_MODEL`** | No | `"llama2"` | `app/config.py`<br>`app/services/llm_service.py` | Line 18<br>Line 56 | Local model name for Ollama inference. | `"mistral"` | Yes. |
| **`GROQ_API_KEY`** | **Conditional** | `""` | `app/config.py`<br>`app/services/llm_service.py`<br>`app/services/audio_service.py` | Line 21<br>Line 48<br>Line 75 | Authentication token for Groq Cloud API. | `gsk_XYZ...` | Yes, unless `LLM_PROVIDER="groq"`, in which case queries throw startup ValueErrors. |
| **`GROQ_MODEL`** | No | `"llama-3.3-70b-versatile"` | `app/config.py`<br>`app/services/llm_service.py` | Line 22<br>Line 49 | Model name for Groq inference. | `"llama-3.3-70b-versatile"` | Yes. |
| **`HUGGINGFACE_API_KEY`** | **Conditional** | `""` | `app/config.py`<br>`app/services/llm_service.py` | Line 25<br>Line 67 | Authentication token for Hugging Face Hub. | `hf_ABC...` | Yes, unless `LLM_PROVIDER="huggingface"`. |
| **`SECRET_KEY`** | **Yes** | *None* | `app/config.py`<br>`app/utils/security.py` | Line 28<br>Lines 30, 133 | Secret key used for signing JWT access and refresh tokens. | `2b95b8755...` | **No**. Pydantic Settings validation fails on startup if missing. |
| **`ALGORITHM`** | No | `"HS256"` | `app/config.py` | Line 29 | Encryption algorithm for token signatures. | `"HS256"` | Yes. |
| **`ACCESS_TOKEN_EXPIRE_MINUTES`** | No | `43200` | `app/config.py`<br>`app/utils/security.py` | Line 30<br>Line 36 | Life duration of access tokens (in minutes). | `43200` | Yes (uses default). |
| **`REFRESH_TOKEN_EXPIRE_MINUTES`** | No | `10080` | `app/config.py`<br>`app/utils/security.py` | Line 31<br>Line 39 | Life duration of refresh tokens (in minutes). | `10080` | Yes (uses default). |
| **`HOST`** | No | `"0.0.0.0"` | `app/config.py`<br>`app/main.py` | Line 34<br>Line 92 | Host IP for FastAPI Uvicorn web server. | `"127.0.0.1"` | Yes. |
| **`PORT`** | No | `8000` | `app/config.py`<br>`app/main.py` | Line 35<br>Line 93 | Network port for FastAPI Uvicorn server. | `8000` | Yes. |
| **`LOG_LEVEL`** | No | `"INFO"` | `app/config.py`<br>`app/main.py` | Line 36<br>Line 95 | Uvicorn logging verbosity context. | `"DEBUG"` | Yes. |
| **`DEPARTMENTS`** | No | *List of 10* | `app/config.py` | Line 42 | JSON string override of default departments list. | `["Revenue", "Health"]` | Yes. |
| **`GRIEVANCE_CATEGORIES`** | No | *List of 11* | `app/config.py` | Line 56 | JSON string override of categories list. | `["Pension"]` | Yes. |

---

## 💀 3. Dead Configuration Reports

### 1. `API_BASE_URL` in `docker-compose.yml`
- **Description**: `docker-compose.yml` passes `- API_BASE_URL=http://backend:8000/api/v1` to the frontend service environment.
- **Why it is Dead**: The file `gradio_app.py` has the constant hardcoded: `API_BASE_URL = "http://localhost:8000/api/v1"`. It does **not** read from `os.getenv()`. Thus, the passed environment variable is completely ignored.

### 2. `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `REFRESH_TOKEN_EXPIRE_MINUTES` in `app/config.py`
- **Description**: These security parameters are declared in Pydantic's `Settings` class in `config.py`.
- **Why it is Dead**: They are **never consumed** via the `settings` instance (e.g. `settings.SECRET_KEY`). Instead, `app/utils/security.py` directly fetches them from `os.getenv("SECRET_KEY")`.

---

## 🚨 4. Critical Deployment Issues

### 1. Environment Variable Isolation (Vulnerability)
- **Vulnerability**: `app/utils/security.py` reads `SECRET_KEY` directly via `os.getenv("SECRET_KEY", "")`. However, the codebase **never calls `load_dotenv()`** to load variables from `.env` into the environment. 
- **Impact**: While Pydantic Settings parses the `.env` file and populates `settings.SECRET_KEY` (preventing validation crashes), it does **not** write these variables to the system's `os.environ`. Therefore, when the application runs locally without system-level variables, `os.getenv("SECRET_KEY")` in `security.py` resolves to `None` (falling back to `""`). **All user authentication tokens are signed with an insecure empty string key `""` in local production setups.**

### 2. Gradio Containerization Connection Failure
- **Vulnerability**: Hardcoded `API_BASE_URL` in `gradio_app.py` prevents setting the URL dynamically.
- **Impact**: In container environments, the frontend container tries to contact `localhost:8000` (itself) and fails, preventing any citizen submits, assignments, or update queries.

---

## 💾 5. Final Optimized `.env.example`

In accordance with requirements, this `.env.example` contains **only** the required variables (those without which the backend cannot start or function) and nothing extra:

```env
# ==============================================================================
# Grievance Redressal System — Required Environment Variables
# ==============================================================================

# Required. Connection URL for the MongoDB instance.
# Example: mongodb://localhost:27017
MONGODB_URL=mongodb://localhost:27017

# Required. Secret key used for signing JWT access and refresh tokens.
# Must be a secure 32-byte hex string. Generate using:
#   Python: python -c "import secrets; print(secrets.token_hex(32))"
#   OpenSSL: openssl rand -hex 32
SECRET_KEY=your_secret_key_here_generate_with_openssl_or_python

# Required. API Key for Groq Cloud API.
# Required because the default LLM provider is set to Groq.
# Obtain key at: https://console.groq.com
GROQ_API_KEY=gsk_your_groq_api_key_here_from_console
```

---

## 🧪 6. Verification of Consumption in Code

- **`MONGODB_URL`**: Consumed at `app/models/database.py` line 20: `cls.client = AsyncIOMotorClient(settings.MONGODB_URL)`.
- **`SECRET_KEY`**: Validated by Pydantic on startup at `app/config.py` line 28, and consumed at `app/utils/security.py` line 30 to configure token signature cryptography.
- **`GROQ_API_KEY`**: Consumed at `app/services/llm_service.py` line 48 to initialize `ChatGroq(api_key=settings.GROQ_API_KEY)` and at `app/services/audio_service.py` line 75 to initialize `Groq(api_key=settings.GROQ_API_KEY)`.
