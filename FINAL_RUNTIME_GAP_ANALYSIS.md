# Final Runtime Gap Analysis — Grievance Redressal System

This document outlines the final runtime readiness audit for the Grievance Redressal System, evaluating potential runtime failure points and gaps.

---

## ❓ Audit Questions & Answers

### 1. What is still missing?
* **Local Configuration File (`.env`)**: A fresh clone does not contain a `.env` file, which is required to start the application.
* **System Binary Files**: The Tesseract OCR executable and FFmpeg transcoder binaries are missing from a standard Windows installation and must be installed manually.
* **Database Seed Records**: While the code connects to MongoDB and programmatically sets up collection indexes, it starts with an empty database. Citizen tracking and administrative tests require importing the dump files located in `data/`.
* **Gradio Environment Variable Loading**: In `gradio_app.py`, the constant `API_BASE_URL` is hardcoded as a static string `http://localhost:8000/api/v1`. It does not fall back to `os.getenv("API_BASE_URL")`, meaning that the containerized frontend will attempt to query `localhost` internally instead of the backend container.

### 2. What can prevent the application from starting?
* **Pydantic Validation Error (`SECRET_KEY`)**: Pydantic's `Settings` class requires `SECRET_KEY` as a string. If this is not set in `.env` or in environment variables, the backend crashes immediately on startup.
* **Database Connection Timeout**: The backend lifespan event executes a `ping` command to MongoDB on startup. If local MongoDB is not running or the Atlas URL is incorrect, the server blocks for the timeout duration and then crashes.
* **Unicode Output Encodes on Windows**: Printing logs containing emojis (e.g. `⚠️`, `✅`) inside `gradio_app.py` will cause a `UnicodeEncodeError` and crash the application on Windows terminals operating in CP1252 character maps, unless `PYTHONUTF8=1` is explicitly set in the shell.
* **PyAudio Compilation Errors**: Standard Python installation of PyAudio on Windows will fail if Visual C++ compiler tools are missing, preventing the full installation of `requirements.txt`.

### 3. Which configuration files still require user input?
* **`.env`**: Must be copied from `.env.example` and customized with credentials and generated secrets before the first start.
* **`gradio_app.py`**: The `API_BASE_URL` constant on line 30 must be manually updated to point to the backend host (e.g. `http://backend:8000/api/v1` inside Docker networks) if the environment variable loading patch is not applied.

### 4. Which services require API keys?
* **Groq API**: Required if `LLM_PROVIDER=groq` (default in configuration) for ticket categorization, routing, RAG integration, and audio Whisper cloud transcription.
* **Hugging Face Hub**: Required if `LLM_PROVIDER=huggingface` to load open-source models.
* **MongoDB Atlas**: Cloud database access credentials (username and password) are required inside the MongoDB connection string URL.

### 5. Which services require local installation?
* **Python 3.10+**: Core programming runtime.
* **Tesseract OCR (UB-Mannheim installer)**: Required for extraction of Telugu/English image text.
* **FFmpeg Build (gyan.dev)**: Required for voice input file conversion.
* **MongoDB Community Server (or Compass)**: Required for local database storage and verification.
* **Docker Desktop**: Required to orchestrate containerized microservices.

### 6. Which files must be edited manually before the first run?
* **`.env`**: Populate database URLs, API keys, and secret parameters.
* **`gradio_app.py`**: Line 30 needs updating if running in Docker compose environments or if backend and frontend are hosted on separate IPs.

### 7. What is the exact order in which the project should be started?
To ensure smooth runtime execution, spin up components in the following sequence:
1. **Database Service**: Start local MongoDB (or ensure Atlas cluster network routes are whitelisted).
2. **Database Seeding**: Run `mongoimport` to import user and grievance collections from `data/`.
3. **Database Migration**: Run `python -m app.db.migrate` to create database indexes programmatically.
4. **Backend Server**: Run `python -m uvicorn app.main:app --port 8000` (verify port binding and health check routes).
5. **Frontend UI**: Execute `$env:PYTHONUTF8="1"; python gradio_app.py` (ensure port `7863` serves HTML).

---

## 🚀 Runtime Gaps Summary & Solution Strategies

| Gap Identified | Impact | Severity | Recommended Solution |
| :--- | :--- | :--- | :--- |
| **Gradio static API_BASE_URL** | Docker Compose frontend container cannot communicate with backend service. | **High** | Modify line 30 of `gradio_app.py` to: `API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")` and import `os`. |
| **Windows Console CP1252 Crash** | Frontend crashes immediately on launch when logging emojis. | **Medium** | Launch python scripts with the environment variable `PYTHONUTF8=1` set. |
| **Windows PyAudio pip build fail** | `requirements.txt` fails to install due to missing compile tools. | **Medium** | Install precompiled PyAudio wheels via pipwin or release binaries. |
| **MongoDB empty collection state** | No citizen history, resolved cases (RAG), or users exist. | **Low** | Run manual JSON imports from `data/` dump files. |
