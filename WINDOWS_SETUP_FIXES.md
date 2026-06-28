# Windows Setup Fixes — Grievance Redressal System

This document outlines common installation and startup issues encountered when running the Grievance Redressal System on Windows, along with step-by-step resolution commands.

---

## 🚨 1. Windows Terminal Encoding Crash (CP1252)

### The Issue:
Windows PowerShell and command prompt sessions default to ANSI/CP1252 character sets. Emojis and non-ASCII warning logs in `gradio_app.py` trigger a `UnicodeEncodeError`, crashing the server immediately on start:
```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-1: character maps to <undefined>
```

### The Fix:
Force Python to operate in UTF-8 mode. Run the server using these commands:
* **PowerShell**:
  ```powershell
  $env:PYTHONUTF8="1"
  python gradio_app.py
  ```
* **Command Prompt (CMD)**:
  ```cmd
  set PYTHONUTF8=1
  python gradio_app.py
  ```

---

## 🎙️ 2. PyAudio Installation Compilation Failure

### The Issue:
Standard compilation of PyAudio on Windows requires C++ headers for `portaudio` and the MSVC compiler link, causing `pip install pyaudio` to fail.

### The Fix:
1. Ensure you are on Python 3.10, 3.11, or 3.12 (as precompiled wheels are available on PyPI for these versions).
2. Upgrade `pip` to check for prebuilt wheels:
   ```powershell
   python -m pip install --upgrade pip
   pip install pyaudio
   ```
3. If still failing, install precompiled wheels manually using `pipwin` or by downloading `.whl` files:
   ```powershell
   pip install pipwin
   pipwin install pyaudio
   ```

---

## 🖼️ 3. Tesseract OCR Windows Configuration

### The Issue:
Windows does not automatically expose Tesseract globally. The path `C:\Program Files\Tesseract-OCR` must be explicitly registered.

### The Fix:
1. Run the [UB-Mannheim Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki) and enable **Telugu** and **English** languages.
2. Register the path by executing the following in PowerShell:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\Tesseract-OCR", "Machine")
   ```
3. Verify path setup:
   ```powershell
   tesseract --version
   ```

---

## 🎵 4. FFmpeg Audio Converter Setup

### The Issue:
The `pydub` and Whisper local fallback systems require FFmpeg to read audio uploads, otherwise raising `RuntimeWarning: Advanced audio operations not found`.

### The Fix:
1. Download full build from: [FFmpeg Windows Builds (gyan.dev)](https://www.gyan.dev/ffmpeg/builds/).
2. Extract to `C:\ffmpeg` and add `C:\ffmpeg\bin` to PATH:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\ffmpeg\bin", "Machine")
   ```
3. Verify PATH:
   ```powershell
   ffmpeg -version
   ```
