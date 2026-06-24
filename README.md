# AI-Powered Grievance Redressal System

## Overview
An intelligent grievance management system for Andhra Pradesh government that leverages LLMs for automated classification, routing, and resolution suggestions. The system supports multi-modal inputs (text, audio, images, documents) with voice recognition capabilities and provides role-based access for Citizens, Admins, and Department Addressers through an enhanced Gradio interface.

## 🎯 Key Features

### Enhanced Multi-Modal Input Processing
- **Text Analysis**: Automatic classification and summarization using LLMs
- **Audio Transcription**: Groq Whisper API for Telugu & English speech-to-text
- **Voice Input**: Real-time voice recording with OpenAI Whisper and Google Speech Recognition fallback
- **Image OCR**: Tesseract-based text extraction from images (Telugu + English)
- **Document Understanding**: Entity extraction from PDFs, Word docs, and images

### Interactive Chatbot Interface (Citizens)
- **Conversational Grievance Submission**: Step-by-step guided chatbot for submitting grievances
- **Voice & Text Support**: Users can type or speak their complaints
- **Multi-language Support**: English and Telugu language options
- **Attachment Support**: Add images, audio files, and documents via chat
- **Smart Validation**: Real-time feedback and validation during submission

### Role-Based Access Control
- **Citizens**: Submit and track grievances, view dashboard, provide feedback via chatbot or forms
- **Admins**: Full system oversight, assignment management, analytics, department updates
- **Addressers**: Department-specific grievance handling, status updates, progress tracking

### Intelligent Classification
- Automatic category detection (11 categories)
- Department routing (13+ departments including PDS, Agriculture, Transport, etc.)
- Priority assignment (Low/Medium/High/Critical)
- Explainable AI - reasons for each classification

### RAG-Powered Suggestions
- Similar case retrieval from resolved grievances
- Context-aware action recommendations
- Resolution time estimates based on historical data

## 🏗️ Architecture

```
┌──────────────────────────┐
│  Enhanced Gradio UI      │ (Frontend with Chatbot, Voice Input)
│  - Chatbot Interface     │
│  - Voice Recording       │
│  - Multi-role Portals    │
└──────┬───────────────────┘
       │
┌──────▼───────────┐
│  FastAPI Backend │ (REST APIs)
└──────┬───────────┘
       │
┌──────▼──────────────────────────────┐
│  LangGraph Workflow Orchestration   │
│  ┌─────────────────────────────┐   │
│  │ 1. Multi-modal Processing   │   │
│  │ 2. LLM Understanding Chain  │   │
│  │ 3. RAG Redressal Chain     │   │
│  │ 4. Database Persistence    │   │
│  └─────────────────────────────┘   │
└──────┬──────────────────────────────┘
       │
┌──────▼────────┬────────────┐
│   MongoDB     │   Groq LLM │
│  (Metadata)   │  (Whisper) │
└───────────────┴────────────┘
```

## 📁 Project Structure

```
grievance-system/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration settings
│   │
│   ├── models/
│   │   ├── database.py            # MongoDB async connection
│   │   ├── schemas.py             # Pydantic models
│   │   └── user.py                # User models (3 roles)
│   │
│   ├── api/
│   │   ├── dependencies.py        # Auth & role dependencies
│   │   └── routes/
│   │       ├── auth.py            # Authentication
│   │       ├── admin.py           # Admin endpoints
│   │       ├── citizen.py         # Citizen endpoints
│   │       ├── official.py       # Addresser endpoints
│   │       ├── grievance.py       # Public APIs
│   │       └── health.py          # Health check
│   │
│   ├── services/
│   │   ├── llm_service.py         # LLM abstraction (Groq/Ollama)
│   │   ├── audio_service.py       # Audio transcription (Groq Whisper)
│   │   ├── image_service.py       # Image processing & OCR
│   │   ├── document_service.py    # Document understanding
│   │   ├── rag_service.py         # Similar case retrieval
│   │   └── auth_service.py        # Authentication logic
│   │
│   ├── chains/
│   │   ├── understanding_chain.py # Grievance analysis
│   │   ├── redressal_chain.py     # Action suggestions
│   │   └── prompts.py             # LLM prompt templates
│   │
│   ├── workflows/
│   │   └── langgraph_workflow.py  # LangGraph state machine
│   │
│   └── utils/
│       ├── security.py            # JWT & password hashing
│       └── logger.py              # Logging configuration
│
├── gradio_app.py                 # Enhanced Frontend UI with Chatbot & Voice
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker image
├── docker-compose.yml             # Multi-container setup
├── .env.example                   # Environment template
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MongoDB Atlas account (or local MongoDB)
- Groq API key (free tier available)
- Tesseract OCR (for image text extraction)
- Microphone (optional, for voice input)

### Installation

#### 1. Clone Repository
```bash
git clone <repository-url>
cd grievance-system
```

#### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Install System Dependencies

**For OCR (Tesseract):**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-tel tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

**For Voice Input (PyAudio):**

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**macOS:**
```bash
brew install portaudio
```

**Windows:**
PyAudio may require manual installation from wheel files.

#### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```env
# MongoDB
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/grievance_db
DATABASE_NAME=grievance_db

# LLM Provider (groq or ollama)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

#### 5. Run Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 6. Run Frontend (New Terminal)
```bash
python gradio_app.py
```

Access the application:
- Frontend UI: http://localhost:7863
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

## 🎨 Enhanced Gradio UI Features

### Citizen Portal
#### Interactive Chatbot Submission
- **Conversational Flow**: Step-by-step guided grievance submission
- **Voice Input**: Click microphone icon to record voice complaints
- **Multi-language**: Switch between English and Telugu
- **Smart Attachments**: Upload images, audio files, and documents through chat
- **Real-time Validation**: Instant feedback on input quality

#### Traditional Form Submission
- All fields in one form for quick submission
- Support for text, image, audio, and document uploads
- Language selection and location input

#### Other Citizen Features
- **Track Grievance**: Search by Grievance ID to view status and timeline
- **My Grievances**: View all submitted grievances with status filters
- **Dashboard**: Overview of grievance statistics and recent activity
- **Feedback**: Submit feedback and ratings on resolved grievances

### Admin Portal
- **Dashboard**: System-wide statistics and analytics
- **All Grievances**: Comprehensive list with advanced filters (status, department, priority)
- **Update Status**: Change grievance status with comments and resolution estimates
- **Assign Grievances**: Manual or AI-suggested department assignment
- **Department Updates**: Monitor all addresser updates across departments
- **Track Grievance**: Detailed tracking and history view

### Addresser Portal
- **Dashboard**: Department-specific statistics and workload overview
- **Department Grievances**: List of grievances assigned to your department with filters
- **Submit Updates**: Record work progress with public/internal visibility options
- **Track Grievance**: View complete grievance details and update history

### Voice Input Technology
The system supports two voice recognition methods:

1. **OpenAI Whisper** (Recommended)
   - High-accuracy offline transcription
   - Multi-language support (English, Telugu)
   - Automatic language detection
   - Uses `base` model for optimal speed/accuracy balance

2. **Google Speech Recognition** (Fallback)
   - Online API-based recognition
   - Works when Whisper is unavailable
   - Supports multiple languages

Users can simply click the microphone button and speak their grievance. The system automatically:
- Transcribes the audio
- Populates the text field
- Allows editing before submission

## 📡 API Endpoints

### Authentication
```
POST   /api/v1/auth/register      # Register new user (Citizen/Admin/Addresser)
POST   /api/v1/auth/login         # Login
GET    /api/v1/auth/me            # Get current user info
```

### Citizen Endpoints
```
POST   /api/v1/citizen/grievance/submit    # Submit grievance (multi-modal)
GET    /api/v1/citizen/my-grievances        # List my grievances
GET    /api/v1/citizen/grievance/{id}       # Get grievance details
POST   /api/v1/citizen/grievance/{id}/feedback  # Submit feedback
GET    /api/v1/citizen/dashboard             # Citizen dashboard stats
```

### Admin Endpoints
```
GET    /api/v1/admin/dashboard               # Admin dashboard
GET    /api/v1/admin/grievances              # List all grievances (with filters)
GET    /api/v1/admin/grievance/{id}          # Get grievance details
POST   /api/v1/admin/grievance/{id}/assign   # Assign to department
POST   /api/v1/admin/grievance/{id}/status   # Update status
GET    /api/v1/admin/department-updates      # Get department updates
GET    /api/v1/admin/analytics               # System analytics
```

### Addresser Endpoints
```
GET    /api/v1/addresser/dashboard           # Department dashboard
GET    /api/v1/addresser/grievances          # List department grievances
GET    /api/v1/addresser/grievance/{id}      # Get grievance details
POST   /api/v1/addresser/grievance/{id}/update  # Submit work update
GET    /api/v1/addresser/my-updates          # My update history
GET    /api/v1/addresser/statistics          # Addresser performance stats
```

### Public Endpoints
```
POST   /api/v1/grievance/submit     # Submit grievance (no auth)
GET    /api/v1/grievance/{id}       # Track grievance (no auth)
GET    /api/v1/grievances           # List grievances (with filters)
```

## 🧠 LLM Integration

### Supported Providers
1. **Groq** (Recommended - Free Tier)
   - Model: llama-3.3-70b-versatile
   - Fast inference
   - Whisper API for audio transcription
   
2. **Ollama** (Local)
   - Model: llama2, mistral, etc.
   - Fully offline
   - Requires local installation

3. **Hugging Face** (Free API)
   - Model: Mistral-7B-Instruct
   - API-based inference

### LLM Workflow

**1. Understanding Chain**
```python
Input: Grievance text (from text/audio/image/document/voice)
Process:
  - Language detection (Telugu/English)
  - Categorization (11 categories)
  - Department routing (13+ departments)
  - Priority assessment (Low/Medium/High/Critical)
  - Keyword extraction
  - Explainability generation
Output: Structured classification with reasoning
```

**2. Redressal Chain**
```python
Input: Classified grievance + similar past cases (RAG)
Process:
  - Retrieve 3 similar resolved cases
  - Generate action recommendations
  - Estimate resolution time
  - Determine escalation need
Output: Actionable resolution steps with explanation
```

### Prompt Engineering
Located in `app/chains/prompts.py`:
- **UNDERSTANDING_SYSTEM_PROMPT**: Classification instructions
- **REDRESSAL_SYSTEM_PROMPT**: Resolution suggestion instructions
- Temperature: 0.3 (understanding), 0.5 (redressal)
- Max tokens: 2000

## 🔊 Multi-Modal Processing

### Voice Input (New Feature)
**Implementation**: `gradio_app.py` - Chatbot interface
**Primary Engine**: OpenAI Whisper (base model)
**Fallback Engine**: Google Speech Recognition API
**Supported Formats**: Real-time microphone recording
**Languages**: English, Telugu, Auto-detect
**Features**:
- One-click voice recording
- Automatic transcription
- Editable transcribed text
- Seamless integration with chatbot flow

**User Experience**:
1. Click microphone icon in chatbot
2. Speak your grievance
3. System transcribes automatically
4. Review and edit if needed
5. Continue with submission flow

### Audio Transcription
**Service**: `app/services/audio_service.py`
**Provider**: Groq Whisper Large V3
**Supported Formats**: MP3, WAV, M4A, OGG, WebM, FLAC
**Languages**: Telugu (te), English (en), Auto-detect
**Max File Size**: 25 MB
**Processing Time**: ~2-5 seconds

**Features**:
- Automatic format detection
- Language-specific transcription
- Confidence scoring
- Fallback to local Whisper (optional)

### Image OCR
**Service**: `app/services/image_service.py`
**Engine**: Tesseract OCR
**Languages**: Telugu (tel), English (eng)
**Supported Formats**: JPG, PNG, WEBP, BMP, TIFF
**Max File Size**: 10 MB
**Processing Time**: ~2-4 seconds

**Features**:
- Automatic language detection
- Multi-language text extraction
- Quality assessment
- Layout preservation

### Document Processing
**Service**: `app/services/document_service.py`
**Supported Formats**: PDF, DOCX
**Features**:
- Text extraction
- Entity recognition (dates, amounts, locations)
- Keyword extraction
- Document type classification

## 🎭 User Workflows

### Citizen Journey (With Chatbot)
1. **Login/Register** → Select "Citizen" role
2. **Chatbot Greeting** → Welcome message appears
3. **Describe Grievance** → Type or use voice input
4. **Select Language** → Choose English or Telugu
5. **Provide Location** → Enter your location
6. **Add Attachments** (Optional) → Upload images/documents
7. **Submit** → Get Grievance ID instantly
8. **Track Progress** → Monitor status updates
9. **Provide Feedback** → Rate service after resolution

### Admin Journey
1. **Login** → Admin credentials
2. **View Dashboard** → System overview
3. **Review Grievances** → Filter by status/department/priority
4. **Assign to Department** → Manual or AI-suggested
5. **Update Status** → Add comments and resolution estimates
6. **Monitor Updates** → Track addresser progress
7. **Analytics** → View system performance

### Addresser Journey
1. **Login** → Department-specific credentials
2. **View Department Dashboard** → Workload overview
3. **Access Assigned Grievances** → Filter by priority
4. **Submit Work Updates** → Record progress (public/internal)
5. **Track Completion** → Monitor resolution timeline
6. **View Statistics** → Personal performance metrics

## 📊 Data Models

### Grievance Schema
```json
{
  "grievance_id": "GRV-20260106-ABC123",
  "user_id": "user_123",
  "user_name": "John Doe",
  "user_contact": "john@example.com",
  "user_phone": "+91-9876543210",
  
  # Original input
  "text": "Original grievance text...",
  "language": "english",
  "location": "Vijayawada, Krishna District",
  
  # Multi-modal inputs
  "audio_transcript": {
    "success": true,
    "text": "Transcribed text...",
    "language": "en",
    "confidence": 0.95
  },
  "image_ocr": {
    "success": true,
    "text": "Extracted text...",
    "confidence": 0.75
  },
  "document_analysis": {
    "success": true,
    "extracted_text": "Document text...",
    "key_entities": {
      "dates": ["2024-01-15"],
      "amounts": ["₹5000"],
      "locations": ["Visakhapatnam"]
    },
    "document_type": "complaint_letter",
    "confidence": 0.8
  },
  
  # LLM Analysis
  "summary": "Brief summary...",
  "category": "Infrastructure",
  "department": "Roads and Buildings",
  "priority": "High",
  "keywords": ["road", "damage", "repair"],
  "explanation": {
    "category_reason": "Why this category...",
    "department_reason": "Why this department...",
    "priority_reason": "Why this priority..."
  },
  
  # Redressal
  "recommended_actions": [
    "Step 1: Verify complaint",
    "Step 2: Assign inspection team",
    "Step 3: Prepare cost estimate"
  ],
  "escalation_needed": false,
  "estimated_resolution_time": "7-10 days",
  "similar_cases": ["GRV-20250815-XYZ789"],
  
  # Assignment
  "assignment": {
    "assigned_by": "admin_user_id",
    "assigned_by_name": "Admin Name",
    "assigned_to_department": "Roads and Buildings",
    "assignment_type": "auto",
    "assigned_at": "2026-01-06T10:00:00Z"
  },
  
  # Status
  "status": "In Review",
  
  # Addresser updates
  "addresser_updates": [
    {
      "addresser_id": "addr_123",
      "addresser_name": "Officer Name",
      "department": "Roads and Buildings",
      "work_done": "Inspection completed...",
      "remarks": "Additional notes...",
      "visibility": "public",
      "timestamp": "2026-01-07T14:30:00Z"
    }
  ],
  
  # Feedback
  "feedback": {
    "rating": 4,
    "comments": "Good service",
    "submitted_at": "2026-01-10T10:00:00Z"
  },
  
  # Timestamps
  "created_at": "2026-01-06T10:00:00Z",
  "updated_at": "2026-01-07T14:30:00Z",
  "resolved_at": null
}
```

### User Roles
- **Citizen**: Submit grievances, track status, provide feedback
- **Admin**: System oversight, assignment, analytics
- **Addresser**: Department-specific handling, status updates

## 🧪 Testing

### Test User Accounts
Create test accounts via `/api/v1/auth/register` or Gradio UI:

**Citizen**:
```json
{
  "email": "citizen@test.com",
  "password": "Test@1234",
  "full_name": "Test Citizen",
  "role": "citizen",
  "location": "Vijayawada"
}
```

**Admin**:
```json
{
  "email": "admin@test.com",
  "password": "Admin@1234",
  "full_name": "Test Admin",
  "role": "admin"
}
```

**Addresser**:
```json
{
  "email": "addresser@test.com",
  "password": "Addr@1234",
  "full_name": "Test Addresser",
  "role": "addresser",
  "department": "Roads and Buildings"
}
```

### Testing Voice Input
1. Login as Citizen
2. Navigate to "Chatbot Submit" tab
3. Click microphone icon
4. Grant microphone permissions in browser
5. Speak your grievance clearly
6. Verify transcription appears in text field
7. Edit if needed and continue submission

### API Testing with cURL

**Submit Grievance (Public)**:
```bash
curl -X POST http://localhost:8000/api/v1/grievance/submit \
  -F "text=Road is damaged near my house" \
  -F "language=english" \
  -F "user_name=John Doe" \
  -F "user_contact=john@example.com" \
  -F "location=Vijayawada"
```

**With Audio**:
```bash
curl -X POST http://localhost:8000/api/v1/grievance/submit \
  -F "text=Water supply issue" \
  -F "audio=@complaint.m4a"
```

**With Image**:
```bash
curl -X POST http://localhost:8000/api/v1/grievance/submit \
  -F "text=Broken streetlight" \
  -F "image=@photo.jpg"
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Configuration
The Dockerfile includes:
- Python 3.10 base image
- Tesseract OCR installation
- Telugu language pack
- PyAudio for voice input
- All Python dependencies
- FastAPI + Gradio applications

## 📈 Performance & Scalability

### Processing Times
- Text-only grievance: ~2-5 seconds
- With voice input: ~3-6 seconds (transcription)
- With audio file (5 min): ~5-10 seconds
- With image OCR: ~3-7 seconds
- With document: ~5-12 seconds
- Chatbot interaction: Instant responses
- Total (all modalities): ~15-30 seconds

### Optimization Tips
1. Use Groq for faster LLM inference (vs Ollama)
2. Enable Redis caching for repeated queries
3. Implement background task processing (Celery)
4. Use connection pooling for MongoDB
5. Implement rate limiting for public endpoints
6. Use Whisper base model (not large) for faster voice transcription
7. Cache Whisper model in memory for repeated use

## 🐛 Troubleshooting

### Common Issues

**1. Voice Input Not Working**
```bash
# Install PyAudio dependencies
# Ubuntu
sudo apt-get install portaudio19-dev python3-pyaudio

# macOS
brew install portaudio

# Verify microphone permissions in browser
# Chrome: Settings → Privacy → Microphone
```

**2. Whisper Model Download**
```bash
# First run will download the model (~150MB for base)
# Ensure internet connectivity
# Model saved to: ~/.cache/whisper/

# Manual download if needed:
import whisper
whisper.load_model("base")
```

**3. Speech Recognition Falls Back to Google**
- This is expected if Whisper is not installed
- Google Speech Recognition requires internet
- For offline use, install Whisper: `pip install openai-whisper`

**4. Tesseract Not Found**
```bash
# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# Verify installation
tesseract --version
```

**5. Audio Transcription Fails**
```bash
# Install Groq library
pip install groq

# Check API key
echo $GROQ_API_KEY
```

**6. MongoDB Connection Error**
- Verify MongoDB Atlas IP whitelist
- Check connection string format
- Ensure network connectivity

**7. LLM Timeout**
- Increase timeout in `llm_service.py`
- Use faster model (Groq instead of Ollama)
- Reduce max_tokens parameter

**8. Chatbot Not Responding**
- Check backend is running on port 8000
- Verify API_BASE_URL in gradio_app.py
- Check browser console for errors
- Ensure proper authentication

## 📝 Configuration

### LLM Settings
```python
# config.py
LLM_PROVIDER = "groq"  # or "ollama"
GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_MODEL = "llama2"
```

### Voice Settings
```python
# gradio_app.py
SPEECH_RECOGNITION_AVAILABLE = True  # Google fallback
WHISPER_AVAILABLE = True             # Primary engine
whisper_model = whisper.load_model("base")  # base/small/medium/large
```

### Categories & Departments
Customize in `config.py` and `gradio_app.py`:
```python
DEPARTMENTS = [
    "Roads and Buildings",
    "Water Supply",
    "Electricity",
    "Revenue",
    "Health",
    "Education",
    "Police",
    "Municipal",
    "Agriculture",
    "Transport",
    "Social Welfare",
    "Housing",
    "Public Distribution System (PDS)"
]

GRIEVANCE_CATEGORIES = [
    "Infrastructure",
    "Public Services",
    "Corruption",
    "Healthcare",
    "Education",
    "Law & Order",
    "Revenue",
    "Agriculture",
    "Social Welfare",
    "Environment",
    "Other"
]
```

## 🔄 Workflow States

```
Open → In Review → Resolved/Rejected

Transitions:
- Open: Initial submission
- In Review: Admin assigns to department, addresser working
- Resolved: Addresser completes work, admin confirms
- Rejected: Invalid or duplicate grievance
```

## 📚 Key Dependencies

```
# Core Framework
fastapi==0.128.0           # Web framework
uvicorn==0.27.0            # ASGI server
motor==3.7.1               # Async MongoDB driver
pydantic==2.12.5           # Data validation

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
PyJWT==2.8.0

# LLM & AI
langchain==0.2.11          # LLM framework
langgraph==0.1.5           # Workflow orchestration
langchain-groq==0.1.6      # Groq integration
groq==0.37.1               # Groq client (Whisper)
openai==1.7.2              # OpenAI models

# Document Processing
pytesseract==0.3.13        # OCR engine
Pillow==10.2.0             # Image processing
PyPDF2==3.0.1              # PDF extraction
python-docx==1.2.0         # Word documents

# Audio & Voice
pydub==0.25.1              # Audio processing
SpeechRecognition==3.10.0  # Google Speech Recognition
openai-whisper==20231117   # Whisper transcription
pyaudio==0.2.14            # Microphone input

# UI
gradio==6.2.0              # Frontend framework
gradio_client==2.0.2       # Gradio client
```

## 🎯 Chatbot Features

### Conversation Flow
1. **Welcome** → Greet user and explain process
2. **Grievance Input** → Accept text or voice input
3. **Language Selection** → English or Telugu
4. **Location Input** → Where is the issue?
5. **Attachment Option** → Add supporting files
6. **Confirmation** → Review before submission
7. **Submission** → Get Grievance ID
8. **Next Steps** → Track or submit another

### Smart Features
- **Context Awareness**: Remembers conversation state
- **Validation**: Checks for complete information
- **Suggestions**: Helps users provide better details
- **Multi-turn**: Handles back-and-forth clarifications
- **Error Handling**: Graceful fallbacks for issues

## 🌐 Browser Compatibility

### Recommended Browsers
- Chrome/Edge 90+ (Best voice support)
- Firefox 88+
- Safari 14+

### Required Browser Permissions
- Microphone access (for voice input)
- File upload (for attachments)

**Last Updated**: January 2026  
