# Dependency Fix Report — Startup & Environment Verification

This report documents the root cause analysis, resolution strategies, and verification tests conducted to resolve dependency and runtime environment startup issues for the Grievance Redressal System on Windows/Conda environments.

---

## 🔍 Root Cause Analysis (RCA)

### 1. OpenAI Whisper Build Failure (`pkg_resources`)
- **Root Cause**: The package `openai-whisper==20231117` distributes only a source distribution (`.tar.gz`) on PyPI, requiring local compilation during `pip install`. The `setup.py` of Whisper imports `pkg_resources` on line 5. In modern Python environments (such as Python 3.12+), `setuptools` v82.0.0 has deprecated and removed the legacy `pkg_resources` module. Because `pip` builds packages in isolated environments pulling the latest `setuptools`, the compile step fails with: `ModuleNotFoundError: No module named 'pkg_resources'`.
- **Affected Files**: `requirements.txt`
- **Risk**: High. Completely blocks environment setup and local Whisper audio transcription execution.
- **Resolution**: Upgraded the dependency in `requirements.txt` to `openai-whisper>=20240930`. Modern Whisper versions utilize PEP 621 `pyproject.toml` configurations. Additionally, modern `torch` and Whisper dependencies declare a compatibility constraint `setuptools<82` which automatically downgrades build-time setuptools to `81.0.0` (which still contains `pkg_resources`), allowing successful compilation.

### 2. PyAudio Native Compiler Missing
- **Root Cause**: Installing `pyaudio==0.2.14` from source requires the C++ development files for `portaudio` and compiler links. Fresh Windows systems lack these build tools, leading to compilation aborts.
- **Affected Files**: `requirements.txt`
- **Risk**: Medium. Prevents full setup on Windows.
- **Resolution**: Verified that pip pulls pre-built Windows wheels (`PyAudio-0.2.14-cp312-cp312-win_amd64.whl`) when using Python 3.12, avoiding local compilation entirely. Added documentation to bypass compiler errors.

### 3. Windows Terminal Character Encoding Crash
- **Root Cause**: Emojis in print logs (e.g. `⚠️`, `✅`) cause `UnicodeEncodeError` when writing to standard output on Windows terminal sessions that default to CP1252/ANSI character sets.
- **Affected Files**: `gradio_app.py`, `app/utils/security.py` (via console logs)
- **Risk**: Medium. Causes immediate application exit during startup.
- **Resolution**: Documented standard launch commands prefixing environment settings to force UTF-8: `$env:PYTHONUTF8="1"`.

---

## 🧪 Verification & Test Results

### 1. PIP Dependency Installation
- **Command**: `python -m pip install -r requirements.txt`
- **Result**: **Passed**. Successfully uninstalled legacy packages, resolved transitive dependencies (including PyAudio, torch, and torchaudio), compiled Whisper's metadata, and completed installation with exit code `0`.

### 2. Uvicorn Backend Startup
- **Command**: `python -m uvicorn app.main:app`
- **Result**: **Passed**. The server initialized lifespan events, connected to MongoDB, programmatically verified database collections, and started listening on `http://127.0.0.1:8000` without any runtime errors.

```log
2026-06-25 16:31:57 - root - INFO - Logging configured successfully
INFO:     Started server process [43452]
INFO:     Waiting for application startup.
2026-06-25 16:31:57 - app.main - INFO - Starting Grievance Redressal System...
2026-06-25 16:31:58 - app.models.database - INFO - Connected to MongoDB at mongodb://localhost:27017
2026-06-25 16:31:58 - app.models.database - INFO - Programmatic database indexes checked/created successfully.
2026-06-25 16:31:58 - app.main - INFO - Application started successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
