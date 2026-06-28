# Manual Actions Required — Grievance Redressal System

This document outlines the manual, non-automated steps required to configure, install, and initialize the Grievance Redressal System on a completely new Windows machine.

---

## 🛠️ Step 1: External System Binary Installations

### 1. Install Tesseract OCR (For Image/Document Scanning)
- **Why**: Required by `pytesseract` to extract Telugu and English text from grievance images and PDFs.
- **Action**:
  1. Download the latest 64-bit installer from the UB-Mannheim project: [Tesseract OCR Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Run the installer. In the **Additional language data** screen, scroll down and check **Telugu** (and verify **English** is selected).
  3. Complete the installation (default location: `C:\Program Files\Tesseract-OCR`).
  4. Add `C:\Program Files\Tesseract-OCR` to your Windows System environment variable `PATH`.
  5. Open PowerShell and verify:
     ```powershell
     tesseract --version
     ```

### 2. Install FFmpeg (For Audio Processing & Whisper)
- **Why**: Required by `pydub` and `whisper` to read and transcode audio uploads (WAV, MP3, WebM, M4A) before speech-to-text processing.
- **Action**:
  1. Download the latest release build from: [FFmpeg Windows Builds (gyan.dev)](https://www.gyan.dev/ffmpeg/builds/).
  2. Extract the downloaded zip file to a permanent folder (e.g., `C:\ffmpeg`).
  3. Add the `C:\ffmpeg\bin` folder to your Windows System environment variable `PATH`.
  4. Open PowerShell and verify:
     ```powershell
     ffmpeg -version
     ```

### 3. Install PyAudio (For Mic Recording / Client-side Voice)
- **Why**: PyAudio requires local portaudio bindings, which can cause compile-time failures on Windows.
- **Action**:
  1. If `pip install pyaudio` fails, download the matching PyAudio precompiled wheel `.whl` file from: [Unofficial Windows Binaries for Python Extension Packages](https://github.com/cgohlke/pyaudio-builds/releases) or use:
     ```powershell
     pip install pipwin
     pipwin install pyaudio
     ```
  2. Alternatively, install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) to compile the package locally.

---

## 🔒 Step 2: Account Creation & API Access Setup

### 1. Set Up MongoDB Database
Choose **either** Local MongoDB or Cloud MongoDB Atlas:
- **Option A: Local MongoDB (Recommended for Offline Dev)**
  1. Download and run the MongoDB Community Server Installer: [MongoDB Community Download](https://www.mongodb.com/try/download/community).
  2. Download and install [MongoDB Compass](https://www.mongodb.com/try/download/compass) to view the collections.
  3. Set `MONGODB_URL=mongodb://localhost:27017` in your `.env`.
- **Option B: MongoDB Atlas (Recommended for Production)**
  1. Sign up for a free cloud account at: [MongoDB Atlas Cloud](https://www.mongodb.com/cloud/atlas).
  2. Create a free shared cluster (M0).
  3. Under **Security** → **Database Access**, create a user (e.g., username `pgrs_user`) and password.
  4. Under **Security** → **Network Access**, whitelist your IP address or add `0.0.0.0/0` (allow all - not recommended for production but useful for setup testing).
  5. Click **Connect** → **Drivers** → Copy connection string. Replace user/password placeholders.

### 2. Create Groq API Credentials (For LLM and Audio Whisper)
- **Why**: Standard LLM provider for category routing, redressal suggestion, and Whisper transcription.
- **Action**:
  1. Create an account at the console: [Groq Console](https://console.groq.com/).
  2. Navigate to **API Keys** → Click **Create API Key**.
  3. Copy the key (e.g., `gsk_...`) and place it in the `.env` file as `GROQ_API_KEY`.

---

## 💾 Step 3: Local Configuration & Database Seeding

### 1. Create `.env` Configuration File
- **Action**:
  1. Copy `.env.example` to `.env` in the root folder:
     ```powershell
     copy .env.example .env
     ```
  2. Generate a 32-byte security key using Python:
     ```powershell
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
  3. Edit `.env` and fill in the `SECRET_KEY`, `MONGODB_URL`, and `GROQ_API_KEY`.

### 2. Seed Initial Database Collections
- **Why**: The application requires historical resolved cases for RAG retrieval and existing user database credentials to test role-based logins.
- **Action**:
  Open PowerShell and import the database dumps located in the `data/` directory using `mongoimport` (installed with MongoDB Database Tools):
  ```powershell
  mongoimport --db grievance_db --collection users --file data/ai_grievance_system.users.json --jsonArray
  mongoimport --db grievance_db --collection grievances --file data/ai_grievance_system.grievances.json --jsonArray
  ```
  *(Note: If MongoDB Atlas is used, append `--uri="your_mongodb_atlas_connection_string"` to the commands).*

---

## 🐋 Step 4: Docker Desktop Setup (If Deploying in Containers)
- **Why**: Required to orchestrate backend, frontend, and MongoDB services.
- **Action**:
  1. Download and install Docker Desktop: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
  2. During installation, enable the WSL 2 backend (recommended).
  3. Reboot Windows, launch **Docker Desktop**, and ensure the engine status changes to **Running**.
  4. Verify in PowerShell:
     ```powershell
     docker compose version
     ```
