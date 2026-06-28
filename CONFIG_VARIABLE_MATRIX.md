# Configuration Variable Matrix — Grievance Redressal System

This matrix maps all configuration variables handled by the centralized `Settings` class, indicating where they are validated, consumed, and their operational parameters.

---

## 📊 Centralized Settings Matrix

| Variable Name | Type | Required? | Default Value | Validated In | Consumed In | Validation Crash Trigger |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`MONGODB_URL`** | `str` | **Yes** | *None* | `app/config.py` | `app/models/database.py` | Missing from environment/dotenv |
| **`DATABASE_NAME`** | `str` | No | `"grievance_db"` | `app/config.py` | `app/models/database.py` | None |
| **`LLM_PROVIDER`** | `str` | No | `"ollama"` | `app/config.py` | `app/services/llm_service.py`<br>`app/services/audio_service.py` | None |
| **`OLLAMA_BASE_URL`** | `str` | No | `""` | `app/config.py` | `app/services/llm_service.py` | None |
| **`OLLAMA_MODEL`** | `str` | No | `"llama2"` | `app/config.py` | `app/services/llm_service.py` | None |
| **`GROQ_API_KEY`** | `str` | **Conditional** | `""` | `app/config.py` | `app/services/llm_service.py`<br>`app/services/audio_service.py` | `LLM_PROVIDER="groq"` and value is empty or spaces |
| **`GROQ_MODEL`** | `str` | No | `"llama-3.3-70b-versatile"` | `app/config.py` | `app/services/llm_service.py` | None |
| **`HUGGINGFACE_API_KEY`** | `str` | **Conditional** | `""` | `app/config.py` | `app/services/llm_service.py` | `LLM_PROVIDER="huggingface"` and value is empty or spaces |
| **`SECRET_KEY`** | `str` | **Yes** | *None* | `app/config.py` | `app/utils/security.py` | Missing from environment/dotenv |
| **`ALGORITHM`** | `str` | No | `"HS256"` | `app/config.py` | `app/utils/security.py` | None |
| **`ACCESS_TOKEN_EXPIRE_MINUTES`** | `int` | No | `43200` | `app/config.py` | `app/utils/security.py` | None |
| **`REFRESH_TOKEN_EXPIRE_MINUTES`** | `int` | No | `10080` | `app/config.py` | `app/utils/security.py` | None |
| **`HOST`** | `str` | No | `"0.0.0.0"` | `app/config.py` | `app/main.py` | None |
| **`PORT`** | `int` | No | `8000` | `app/config.py` | `app/main.py` | None |
| **`LOG_LEVEL`** | `str` | No | `"INFO"` | `app/config.py` | `app/main.py` | None |
| **`API_BASE_URL`** | `str` | No | `"http://localhost:8000/api/v1"` | `app/config.py` | `gradio_app.py` | None |
| **`SUPPORTED_LANGUAGES`** | `List[str]` | No | `["telugu", "english"]` | `app/config.py` | (Internal configuration) | None |
| **`DEPARTMENTS`** | `List[str]` | No | *List of 10* | `app/config.py` | `app/models/database.py` | None |
| **`GRIEVANCE_CATEGORIES`** | `List[str]` | No | *List of 11* | `app/config.py` | `app/models/database.py` | None |
