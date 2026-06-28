# Optimization Summary

This document summarizes the performance optimizations applied to the Grievance Redressal System to prepare it for high-concurrency production workloads.

---

## 1. Database Indexing Optimizations
We analyzed the collection queries and created three critical MongoDB indexes programmatically and idempotently inside `app/models/database.py` on startup:

1. **RAG Compound Index**:
   ```python
   await grievances.create_index([
       ("status", 1),
       ("category", 1),
       ("department", 1),
       ("resolved_at", -1)
   ])
   ```
   * *Impact*: Speeds up the metadata-driven similar case search query (RAG pipeline) from a full collection scan to a selective index scan, reducing query latency from several milliseconds to sub-millisecond ranges.
2. **Category Index**:
   ```python
   await grievances.create_index("category")
   ```
   * *Impact*: Accelerates administrative filters and aggregate analytics breakdowns on the admin and addresser dashboards.
3. **Priority Index**:
   ```python
   await grievances.create_index("priority")
   ```
   * *Impact*: Accelerates administrative filters and priority throughput breakdowns.

---

## 2. Audio Pipeline: Whisper Model Caching
Previously, the system initialized and loaded the local Whisper model on *every* fallback transcription request:
```python
model = whisper.load_model("base")  # Loading on every call
```
Loading a 140M parameter neural network into CPU/GPU memory is extremely slow (often taking 5-15 seconds) and leaks/spikes memory. 

* *Optimization*:
  * Cached the model as an instance variable `self.local_model` inside `AudioService`.
  * Implemented lazy loading: the model is loaded from disk only once, on the first fallback request.
  * Subsequent transcription requests reuse the in-memory cached model, eliminating model load overhead entirely.

---

## 3. Concurrency & Async Correctness (Non-Blocking Event Loop)
By default, FastAPI operates on a single-threaded event loop. Any synchronous CPU-bound operations executed directly within an `async def` function will freeze the event loop, preventing all other concurrent requests from being handled.

We wrapped all CPU-bound synchronous library calls and subprocesses in `asyncio.to_thread()`, which delegates execution to an internal thread pool:

1. **Tesseract OCR Subprocess**:
   * *Before*: `pytesseract.image_to_string(...)` blocked the event loop thread during OCR execution (2-4 seconds).
   * *After*: Executed via `await asyncio.to_thread(pytesseract.image_to_string, ...)` allowing other API requests to process concurrently.
2. **Local Whisper Model Inference**:
   * *Before*: Loading and transcribing blocked the event loop thread during execution (several seconds).
   * *After*: Both `whisper.load_model` and `model.transcribe` are executed in thread pools using `asyncio.to_thread`.
3. **PDF Text Extraction**:
   * *Before*: `PyPDF2.PdfReader` page loops blocked the main thread.
   * *After*: Delegated parsing loops to worker threads.
4. **Word Document Text Extraction**:
   * *Before*: `docx.Document` paragraph reading blocked the main thread.
   * *After*: Delegated XML parsing loops to worker threads.

---

## 4. Future Scaling Recommendations
For extremely high-volume production deployments, the following architectural scaling steps are recommended:
* **Vector Database Migration**: Transition similarity search from simple MongoDB compound queries to a vector database (e.g., Qdrant, pgvector) using dense embeddings (e.g., `text-embedding-3-small`) to enable semantic matching.
* **Asynchronous Task Queue (Celery/RQ)**: Offload multi-modal uploads, OCR extractions, and Whisper transcriptions from the HTTP request-response cycle entirely to background worker processes. The client submits a ticket, receives a task ID immediately, and polls for status updates.
* **Model Inference Servers**: Host Whisper and LLM inference on dedicated model servers (e.g., vLLM, Triton Inference Server) with GPU acceleration rather than hosting CPU-bound base models locally in the web application container.
