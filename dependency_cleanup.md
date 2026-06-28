# Dependency Cleanup Report

This report evaluates python package declarations in `requirements.txt` to identify unused dependencies that can be removed to minimize Docker image sizes, build times, and runtime footprints.

---

## 1. Unused Dependencies Identification

The following 14 packages were identified as completely unused in the codebase (not imported or referenced by any active python source file or script):

| Package Name | Declared Version | Purpose in `requirements.txt` | Reason for Removal |
| :--- | :--- | :--- | :--- |
| `langchain-text-splitters` | `0.2.2` | Text chunking helper | The RAG service operates on atomic grievance documents directly using MongoDB text search; no text splitters are used. |
| `soundfile` | `0.12.1` | Audio reading / writing | Audio ingestion uses raw bytes or is passed directly to the Groq/Whisper APIs; no soundfile calls are made. |
| `librosa` | `0.10.1` | Audio feature extraction | The system does not perform custom audio signal analysis or feature extraction. |
| `pandas` | `2.3.3` | Tabular data analysis | All analytics and dashboard counters are aggregated directly using MongoDB query operators. |
| `numpy` | `1.26.4` | Numerical array computations | No scientific or multi-dimensional numerical array calculations are performed in python code. |
| `lxml` | `6.0.2` | XML and HTML parser | The system relies on python standard libraries and docx parser; no direct `lxml` parsing is done. |
| `python-dateutil` | `2.8.2` | Date parsing utilities | System uses Python standard library `datetime` for all date logic. |
| `pytz` | `2025.2` | Timezone database | MongoDB dates are stored in UTC by default; no timezone conversions are processed in Python. |
| `langsmith` | `0.1.147` | LangChain tracing and logging | Tracing is not enabled in production configurations. |
| `colorlog` | `6.8.0` | Colored logging outputs | System utilizes Python's standard `logging` library directly. |
| `rich` | `14.2.0` | Rich terminal rendering | Terminal logs use standard text log formats for container compatibility. |
| `tqdm` | `4.67.1` | Progress bars | The system is a web API and Gradio app; there are no CLI loops requiring progress bars. |
| `aiohttp` | `3.13.2` | Asynchronous HTTP client | The system uses `httpx` (for FastAPI testing and sync queries) and `requests` (in Gradio app) for HTTP client calls. |
| `httpcore` | `1.0.9` | Low-level HTTP engine | Relies on `httpx` and `requests` internal engines directly; no direct usage of `httpcore`. |

---

## 2. Proposed Action Plan

### Step 1: Modify `requirements.txt`
* Remove the 14 unused packages from `requirements.txt` to streamline installs.

### Step 2: Rebuild Docker Containers
* Re-run the container build process to verify the package footprint reduction.
  ```bash
  docker compose build --no-cache
  ```

### Step 3: Run Verification Suite
* Execute `pytest` to verify that the core auth, database, workflows, and OCR pipelines continue to function normally without any import issues.
  ```bash
  python -m pytest tests/
  ```
