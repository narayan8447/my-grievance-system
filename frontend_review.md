# Frontend Review - Gradio Portals & UX

This document reviews the complete Gradio frontend implementation in [gradio_app.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/gradio_app.py).

---

## 1. Portal Overviews & Layouts
The frontend is constructed using Gradio Blocks to establish a single-page, tabbed web application. Swapping between public authentication forms and role-specific dashboard views is handled reactively using state flags (`is_logged_in`, `user_role`).

### Citizen Portal
* **💬 Submit New Grievance**:
  * Guided chatbot assistant (`Grievance Assistant`) walking citizens through:
    1. Grievance description input (Text/Voice with Whisper/Google fallback).
    2. Preferred language selection (English/Telugu).
    3. Location tagging (text input).
    4. Optional file attachments (Image/Audio/Document).
    5. Review summary prior to submission.
* **📝 Traditional Form Submission**:
  * Added sub-tab layout allowing citizens to submit all parameters (description, language, location, and multiple file uploads) in a single page form instantly, providing a quick fallback to the step-based chatbot wizard.
* **🔍 Track Grievance**:
  * Citizen search dashboard by Grievance ID, printing AI-categorization metadata, priority tiers, assigned departments, Recommended Actions, explainability logs, and historical department officer remarks.
* **📋 My Grievances**:
  * List of all grievances submitted by the logged-in citizen, filterable by status (`All`, `Open`, `In Review`, `Resolved`, `Rejected`).
* **📊 Dashboard**:
  * Citizen metrics summarizing total tickets, open tickets, in-review tickets, and resolved tickets, along with a recent activity list.
* **⭐ Submit Feedback**:
  * Evaluation form for resolved grievances where citizens submit a numeric rating (1-5), description remarks, and optional validation documents/images.

### Addresser Portal (Department Queue)
* **📊 Dashboard**:
  * Displays department-specific KPI metrics (workload totals, open vs. resolved status breakdowns, priority distributions), and a list of urgent pending items with aging calculations.
* **📋 Department Grievances**:
  * Worklist filtering grievances assigned to the logged-in officer's department. Enables filtering by status and priority.
* **✏️ Submit Update**:
  * Allows department officers to log progress (`work_done`, `remarks`), control public/internal visibility settings, and update ticket status.
* **🔍 Track Grievance**:
  * Dedicated departmental details tracker displaying multi-modal extraction details, AI Recommended Actions, and full assignment history.

### Admin Portal
* **📊 Dashboard**:
  * Aggregated global analytics displaying total volume, status counts, priority metrics, and departmental workload distribution.
* **📋 All Grievances**:
  * Administrative dashboard listing all tickets in the system with multi-dimensional filters (status, department, priority) and AI metadata (confidence scores, similar case mappings).
* **✏️ Update Status**:
  * Override controller for admins to manually transition ticket statuses (Open/In Review/Resolved/Rejected) and log official estimates.
* **🎯 Assign Grievance**:
  * Reassignment console to transfer tickets manually or trigger the AI suggestion engine.
* **📢 Department Updates**:
  * Real-time monitoring log displaying all addresser activity updates and internal progress notes.
* **🔍 Track Grievance**:
  * Administrator audit page rendering comprehensive ticket logs, multi-modal ingestion details, execution steps, and similar cases.

---

## 2. Ingestion & Preprocessing UI
* **🎙️ Voice Input**:
  * Standard audio interface wrapper supporting audio file uploads and voice recording. Triggers client-side Speech-to-Text conversion:
    1. Attempts local `openai-whisper` base model transcription.
    2. Falls back to `SpeechRecognition` API (Google Web Speech service).
    3. Handles text insertion dynamically into the chatbot submission.
* **📎 Attachments**:
  * Dynamic file selectors restrict file input:
    * **Images**: Filters standard image inputs.
    * **Audio**: Limits upload selectors to audio formats.
    * **Documents**: Enforces validation for `.pdf`, `.doc`, and `.docx` extensions.

---

## 3. Session & Auth State Management
* **Token Management**:
  * In-memory authorization tokens managed via `gr.State()`.
* **Headers Injection**:
  * Tokens are parsed and injected dynamically into HTTP requests via `CompleteGrievanceUI.get_headers()`, ensuring stateless authentication against the FastAPI backend (`/api/v1`).
