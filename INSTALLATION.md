# Installation Guide

This guide will help you set up and run the AI-Powered Grievance Redressal System on your local machine after cloning the repository.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.10 or higher**
- **Git**
- **MongoDB Atlas account** (free tier available) OR **local MongoDB installation**
- **Groq API key** (free tier available at https://console.groq.com)
- **Microphone** (optional, for voice input feature)
- **Internet connection** (for initial setup and API calls)

---

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd grievance-system
```

---

## Step 2: Set Up Python Virtual Environment (Recommended)

### On Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

---

## Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: This may take several minutes as it installs multiple packages including FastAPI, LangChain, Gradio, and machine learning libraries.

---

## Step 4: Install System Dependencies

### For OCR Support (Tesseract)

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-tel tesseract-ocr-eng
```

#### macOS:
```bash
brew install tesseract tesseract-lang
```

#### Windows:
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and follow the setup wizard
3. Add Tesseract to your system PATH:
   - Default path: `C:\Program Files\Tesseract-OCR`
   - Add to Environment Variables → System Variables → Path

4. in app/services/image_service.py file # Configure Tesseract path for Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

**Verify Installation:**
```bash
tesseract --version
```

### For Voice Input Support (PyAudio)

#### Ubuntu/Debian:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

#### macOS:
```bash
brew install portaudio
```

#### Windows:
PyAudio installation on Windows can be tricky. Try one of these methods:

**Method 1 - Using pip (Windows 10+):**
```bash
pip install pyaudio
```

**Method 2 - Using wheel file:**
1. Download the appropriate `.whl` file from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Install using: `pip install path/to/downloaded/PyAudio.whl`

---

## Step 5: Configure Environment Variables

### 1. Create `.env` file:
```bash
cp .env.example .env
```

### 2. Edit the `.env` file with your credentials:

```env
# MongoDB Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/grievance_db
DATABASE_NAME=grievance_db

# LLM Provider Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Alternative: Ollama (for local LLM)
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=llama2
# OLLAMA_BASE_URL=http://localhost:11434

# Security Settings
SECRET_KEY=your-secret-key-here-change-this-to-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Optional: API Settings
API_BASE_URL=http://localhost:8000
```

### How to Obtain Required Credentials:

#### **MongoDB Atlas URL:**
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up for a free account
3. Create a new cluster (M0 free tier is sufficient)
4. Click "Connect" → "Connect your application"
5. Copy the connection string
6. Replace `<username>`, `<password>`, and database name

#### **Groq API Key:**
1. Go to https://console.groq.com
2. Sign up or log in
3. Navigate to "API Keys" section
4. Click "Create API Key"
5. Copy the key and paste it in `.env` file

#### **Secret Key:**
Generate a secure random string:
```bash
# On Linux/macOS:
openssl rand -hex 32

# On Windows (PowerShell):
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

---

## Step 6: MongoDB Setup

### Option A: Using MongoDB Atlas (Recommended)

1. After creating your cluster, click "Database Access"
2. Add a database user with username and password
3. Click "Network Access"
4. Add your IP address (or use `0.0.0.0/0` for testing - not recommended for production)
5. Go back to "Database" → "Connect" and copy your connection string

### Option B: Using Local MongoDB

1. Install MongoDB Community Edition from: https://www.mongodb.com/try/download/community
2. Start MongoDB service:
   ```bash
   # Linux
   sudo systemctl start mongod
   
   # macOS
   brew services start mongodb-community
   
   # Windows
   net start MongoDB
   ```
3. Update `.env` file:
   ```env
   MONGODB_URL=mongodb://localhost:27017/grievance_db
   ```

---

## Step 7: Download Whisper Model (First Run)

The first time you run the application with voice input, Whisper will download the model (~150MB):

```bash
python -c "import whisper; whisper.load_model('base')"
```

**Note**: The model will be cached at `~/.cache/whisper/` for future use.

---

## Step 8: Run the Application

### Terminal 1 - Start Backend (FastAPI):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2 - Start Frontend (Gradio):

Open a **new terminal** window, activate the virtual environment, and run:

```bash
# Activate virtual environment again
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Start Gradio
python gradio_app.py
```

**Expected Output:**
```
Running on local URL:  http://127.0.0.1:7863
Running on public URL: https://xxxxxxxxxxxx.gradio.live

To create a public link, set `share=True` in `launch()`.
```

---

## Step 9: Access the Application

Open your web browser and navigate to:

- **Frontend UI (Gradio)**: http://localhost:7863
- **Health Check**: http://localhost:8000/api/v1/health

---

## Step 10: Create Initial Admin User (Optional)

You can create users through the registration API or use the default test users:

### Default Test Credentials:

**Admin:**
- Username: `admin`
- Password: `admin123`

**Citizen:**
- Username: `citizen`
- Password: `citizen123`

**Addresser:**
- Username: `addresser`
- Password: `addresser123`

**Note**: Change these credentials in production!

---

## Verification Checklist

Ensure the following are working correctly:

- [ ] Backend API is running on port 8000
- [ ] Frontend Gradio UI is accessible on port 7863
- [ ] MongoDB connection is successful (check terminal logs)
- [ ] You can access the API documentation at `/docs`
- [ ] Health check endpoint returns `{"status": "healthy"}`
- [ ] You can log in through the Gradio interface
- [ ] Tesseract OCR is installed (`tesseract --version`)
- [ ] Voice input button appears (if PyAudio is installed)

---

## Troubleshooting

### Issue 1: `ModuleNotFoundError`

**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue 2: MongoDB Connection Error

**Symptoms**: `ServerSelectionTimeoutError` or connection timeout

**Solutions**:
1. Check your MongoDB Atlas IP whitelist
2. Verify connection string in `.env` file
3. Ensure username and password are correct
4. Test connection string using MongoDB Compass

### Issue 3: Tesseract Not Found

**Symptoms**: `TesseractNotFoundError`

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# Verify
tesseract --version

# If still not found, check PATH
which tesseract
```

### Issue 4: PyAudio Installation Failed

**Symptoms**: Build errors during `pip install pyaudio`

**Solutions** (Windows):
1. Install Microsoft C++ Build Tools
2. Use pre-compiled wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
3. Or disable voice input feature (application will still work)

### Issue 5: Port Already in Use

**Symptoms**: `Address already in use` error

**Solutions**:
```bash
# Linux/macOS - Find and kill process
lsof -ti:8000 | xargs kill -9  # For backend
lsof -ti:7863 | xargs kill -9  # For frontend

# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue 6: Groq API Key Invalid

**Symptoms**: 401 Unauthorized errors in logs

**Solutions**:
1. Verify API key at https://console.groq.com
2. Check for extra spaces in `.env` file
3. Ensure `GROQ_API_KEY` variable is set correctly

### Issue 7: Whisper Model Download Fails

**Solutions**:
1. Ensure stable internet connection
2. Download manually:
   ```bash
   python -c "import whisper; whisper.load_model('base')"
   ```
3. Check available disk space (~500MB needed)

### Issue 8: Gradio Not Loading

**Symptoms**: Blank page or connection refused

**Solutions**:
1. Check if backend is running on port 8000
2. Verify `API_BASE_URL` in `gradio_app.py`
3. Clear browser cache
4. Try different browser
5. Check browser console for JavaScript errors

---

## Docker Installation (Alternative)

If you prefer using Docker:

### Prerequisites:
- Docker Desktop installed
- Docker Compose installed

### Steps:

1. **Build and start containers:**
```bash
docker-compose up --build
```

2. **Access the application:**
- Frontend: http://localhost:7863
- Backend: http://localhost:8000

3. **Stop containers:**
```bash
docker-compose down
```

**Note**: Update `.env` file with MongoDB Atlas URL (Docker can't use localhost MongoDB).

---

## Performance Optimization Tips

1. **Use Groq** instead of Ollama for faster LLM responses
2. **Use base Whisper model** instead of large for faster transcription
3. **Enable MongoDB indexes** for faster queries
4. **Use connection pooling** for database connections
5. **Implement caching** for frequently accessed data

---

## Browser Requirements

### Recommended Browsers:
- Chrome/Edge 90+ (Best voice support)
- Firefox 88+
- Safari 14+

### Required Permissions:
- **Microphone access** (for voice input)
- **File upload** (for attachments)

---

## Next Steps

After successful installation:

1. **Explore the Application**:
   - Try submitting a grievance through the chatbot
   - Test voice input feature
   - Upload images and documents
   - Track grievance status

2. **Customize Configuration**:
   - Modify categories in `app/config.py`
   - Adjust departments list
   - Update prompts in `app/chains/prompts.py`

3. **Set Up for Production**:
   - Change default passwords
   - Use strong SECRET_KEY
   - Enable HTTPS
   - Set up proper logging
   - Configure backups

---

## Getting Help

If you encounter issues not covered here:

1. Check the logs in the terminal for error messages
2. Review the [README.md](README.md) for detailed documentation
3. Email: roychoudhuryswastik@gmail.com

---

