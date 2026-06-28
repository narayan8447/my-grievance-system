"""
Complete Integrated Gradio UI - FULLY ENHANCED
All tabs included: Citizen (Submit, Track, My Grievances, Dashboard, Feedback)
Admin (Dashboard, All Grievances, Update Status, Assign, Department Updates, Track)
Addresser (Dashboard, Department Grievances, Submit Update, Track)
"""
import os
import gradio as gr
import requests
from typing import Tuple
from app.config import settings

# Speech-to-Text imports
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️ speech_recognition not installed. Voice input will use fallback.")

try:
    import whisper
    WHISPER_AVAILABLE = True
    # Load Whisper model (using 'base' for balance of speed and accuracy)
    whisper_model = whisper.load_model("base")
    print("✅ Whisper model loaded successfully")
except ImportError:
    WHISPER_AVAILABLE = False
    whisper_model = None
    print("⚠️ whisper not installed. Voice input will use Google Speech Recognition fallback.")

# Centralized API Base URL from Settings
API_BASE_URL = settings.API_BASE_URL

CUSTOM_CSS = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.submit-btn {
    background: linear-gradient(90deg, #4CAF50, #45a049) !important;
    color: white !important;
    font-weight: bold !important;
}
.track-btn {
    background: linear-gradient(90deg, #2196F3, #0b7dda) !important;
    color: white !important;
}
.logout-btn {
    background: linear-gradient(90deg, #f44336, #da190b) !important;
    color: white !important;
}
.primary-btn {
    background: linear-gradient(90deg, #2196F3, #0b7dda) !important;
    color: white !important;
    font-weight: bold !important;
}
"""

DEPARTMENTS = settings.DEPARTMENTS


class CompleteGrievanceUI:
    """Complete UI supporting Citizen, Admin, and Addresser roles"""
    
    def __init__(self):
        self.api_base = API_BASE_URL
        self.access_token = None
        self.current_user = None
    
    def get_headers(self):
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    # ===== AUTHENTICATION =====
    
    def register_user(self, email, phone, password, confirm, full_name, role, department, location) -> Tuple[str, bool, str]:
        try:
            if not email or not password or not full_name:
                return "❌ Email, password, and full name are required", False, ""
            if password != confirm:
                return "❌ Passwords do not match", False, ""
            if role == "Addresser" and not department:
                return "❌ Department is required for Addresser role", False, ""
            
            data = {
                "email": email,
                "phone": phone if phone else None,
                "password": password,
                "full_name": full_name,
                "role": role.lower(),
                "department": department if role == "Addresser" else None,
                "location": location if location else None
            }
            
            response = requests.post(f"{self.api_base}/auth/register", json=data, timeout=10)
            
            if response.status_code == 201:
                result = response.json()
                self.access_token = result.get("access_token")
                self.current_user = result.get("user")
                return f"✅ Welcome, {full_name}!\n\n🎉 Registration successful!\nRole: {role}\n\n👉 You are now logged in.", True, role
            else:
                error = response.json().get("detail", "Unknown error")
                return f"❌ Registration failed: {error}", False, ""
        except Exception as e:
            return f"❌ Error: {str(e)}", False, ""
    
    def login_user(self, email_or_phone, password) -> Tuple[str, bool, str]:
        try:
            if not email_or_phone or not password:
                return "❌ Email/Phone and password are required", False, ""
            
            data = {"email_or_phone": email_or_phone, "password": password}
            response = requests.post(f"{self.api_base}/auth/login", json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                self.current_user = result.get("user")
                role = self.current_user.get("role", "").capitalize()
                return f"✅ Welcome back, {self.current_user.get('full_name')}!\n\nRole: {role}\n\n👉 Access your portal now.", True, role
            else:
                error = response.json().get("detail", "Invalid credentials")
                return f"❌ Login failed: {error}", False, ""
        except Exception as e:
            return f"❌ Error: {str(e)}", False, ""
    
    def logout_user(self) -> str:
        self.access_token = None
        self.current_user = None
        return "✅ Logged out successfully"
    
    # ===== CITIZEN METHODS =====
    
    def citizen_submit_grievance(self, text, language, location, image_file=None, audio_file=None, document_file=None) -> str:
        try:
            if not text:
                return "❌ Please enter your grievance"
            
            files = {}
            data = {
                "text": text,
                "language": language.lower(),
                "location": location if location else ""
            }
            
            # Add files if provided - FIXED: Proper None/empty checks
            if image_file is not None and isinstance(image_file, str) and len(image_file.strip()) > 0:
                try:
                    files["image"] = open(image_file, "rb")
                except Exception as e:
                    print(f"⚠️ Warning: Could not open image file: {e}")
            
            if audio_file is not None and isinstance(audio_file, str) and len(audio_file.strip()) > 0:
                try:
                    files["audio"] = open(audio_file, "rb")
                except Exception as e:
                    print(f"⚠️ Warning: Could not open audio file: {e}")
            
            if document_file is not None and isinstance(document_file, str) and len(document_file.strip()) > 0:
                try:
                    files["document"] = open(document_file, "rb")
                except Exception as e:
                    print(f"⚠️ Warning: Could not open document file: {e}")
            
            response = requests.post(
                f"{self.api_base}/citizen/grievance/submit",
                data=data,
                files=files if files else None,
                headers=self.get_headers(),
                timeout=60  # Increased timeout for file processing
            )
            
            # Close files safely
            if files:
                for f in files.values():
                    try:
                        f.close()
                    except:
                        pass
            
            if response.status_code == 201:
                result = response.json()
                gid = result.get("grievance_id", "")
                data = result.get("data", {})
                
                output = f"✅ **Grievance Submitted Successfully!**\n\n"
                output += f"**Grievance ID:** `{gid}`\n"
                output += f"**Status:** {data.get('status', 'Submitted')}\n"
                output += f"**Category:** {data.get('category')}\n"
                output += f"**Department:** {data.get('department')}\n"
                output += f"**Priority:** {data.get('priority')}\n\n"
                
                # Show what was processed - FIXED: Handle None values
                processed = []
                if (data.get('audio_transcription') or {}).get('success'):
                    processed.append("🎤 Audio transcribed")
                if (data.get('image_ocr') or {}).get('success'):
                    processed.append("📷 Image text extracted")
                if (data.get('document_analysis') or {}).get('success'):
                    processed.append("📄 Document analyzed")
                
                if processed:
                    output += "**Processed:**\n" + "\n".join([f"- {p}" for p in processed]) + "\n\n"
                
                output += f"💡 **Save this ID to track your grievance.**"
                return output
            else:
                error = response.json().get("detail", "Submission failed")
                return f"❌ Error: {error}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def citizen_track_grievance(self, grievance_id) -> str:
        try:
            if not grievance_id:
                return "❌ Please enter a Grievance ID"
            
            response = requests.get(
                f"{self.api_base}/citizen/grievance/{grievance_id}",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                g = response.json()
                output = f"# 📋 Grievance Details\n\n"
                output += f"**ID:** `{g.get('grievance_id')}`\n"
                output += f"**Status:** {g.get('status')} 🔴\n"
                output += f"**Priority:** {g.get('priority')}\n"
                output += f"**Category:** {g.get('category')}\n"
                output += f"**Department:** {g.get('department')}\n\n"
                
                output += f"## Summary\n{g.get('summary', 'N/A')}\n\n"
                
                # NEW: Show audio transcription if available
                audio = g.get('audio_transcription', {})
                if audio and audio.get('success'):
                    output += f"## 🎤 Audio Transcription\n"
                    output += f"{audio.get('text', 'N/A')}\n\n"
                
                # NEW: Show image OCR if available
                image_ocr = g.get('image_ocr', {})
                if image_ocr and image_ocr.get('success'):
                    output += f"## 📷 Text from Image (OCR)\n"
                    output += f"**Confidence:** {image_ocr.get('confidence', 0):.1%}\n\n"
                    output += f"```\n{image_ocr.get('text', 'N/A')}\n```\n\n"
                
                # NEW: Show document analysis if available
                doc_analysis = g.get('document_analysis', {})
                if doc_analysis and doc_analysis.get('success'):
                    output += f"## 📄 Document Analysis\n"
                    output += f"**Type:** {doc_analysis.get('document_type', 'N/A')}\n"
                    
                    extracted = doc_analysis.get('extracted_text', '')
                    if extracted:
                        output += f"**Extracted Text:** {extracted[:200]}...\n"
                    
                    entities = doc_analysis.get('key_entities', {})
                    if entities:
                        if entities.get('dates'):
                            output += f"**Dates:** {', '.join(entities['dates'][:3])}\n"
                        if entities.get('amounts'):
                            output += f"**Amounts:** {', '.join(entities['amounts'][:3])}\n"
                        if entities.get('locations'):
                            output += f"**Locations:** {', '.join(entities['locations'][:3])}\n"
                    output += "\n"
                
                # Show recommended actions
                actions = g.get('recommended_actions', [])
                if actions:
                    output += "## 📝 Recommended Actions\n"
                    for i, action in enumerate(actions, 1):
                        output += f"{i}. {action}\n"
                    output += "\n"
                
                # NEW: Show explainability
                explanation = g.get('explanation', {})
                if explanation and any(explanation.values()):
                    output += "## 💡 AI Analysis Explanation\n"
                    if explanation.get('category_reason'):
                        output += f"**Category:** {explanation.get('category_reason')}\n\n"
                    if explanation.get('department_reason'):
                        output += f"**Department:** {explanation.get('department_reason')}\n\n"
                
                # NEW: Show similar cases
                similar_cases = g.get('similar_cases', [])
                if similar_cases:
                    output += "## 🔗 Similar Cases\n"
                    output += ", ".join([f"`{c}`" for c in similar_cases]) + "\n\n"
                
                # Show public updates
                updates = g.get('addresser_updates', [])
                public_updates = [u for u in updates if u.get('visibility') == 'public']
                if public_updates:
                    output += "## 📢 Department Updates\n"
                    for update in public_updates:
                        output += f"**{update.get('addresser_name')}** - {update.get('timestamp', '')}\n"
                        output += f"{update.get('work_done')}\n\n"
                
                output += f"**Created:** {g.get('created_at', 'N/A')}\n"
                
                return output
            else:
                return f"❌ {response.json().get('detail', 'Not found')}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def citizen_my_grievances(self, status_filter) -> str:
        try:
            params = {"limit": 20}
            if status_filter != "All":
                params["status"] = status_filter
            
            response = requests.get(
                f"{self.api_base}/citizen/my-grievances",
                params=params,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grievances = data.get("grievances", [])
                
                if not grievances:
                    return "📭 No grievances found"
                
                output = f"# 📋 My Grievances ({data.get('total', 0)} total)\n\n"
                
                for g in grievances:
                    output += f"## {g.get('grievance_id')}\n"
                    output += f"**Status:** {g.get('status')} | **Priority:** {g.get('priority')}\n"
                    output += f"**Category:** {g.get('category')} | **Dept:** {g.get('department')}\n"
                    output += f"**Summary:** {g.get('summary', 'N/A')[:150]}...\n"
                    # NEW: Show if document was analyzed
                    doc_analysis = g.get('document_analysis', {})
                    if doc_analysis and doc_analysis.get('success'):
                        output += f"📄 **Document attached** ({doc_analysis.get('document_type', 'Unknown')})\n"
                    output += f"**Created:** {g.get('created_at', 'N/A')}\n"
                    output += "---\n\n"
                
                return output
            else:
                return f"❌ Error fetching grievances"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def citizen_dashboard(self) -> str:
        try:
            response = requests.get(
                f"{self.api_base}/citizen/dashboard",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                output = f"# 👤 My Dashboard\n\n"
                output += f"**Total Grievances:** {data.get('total_grievances', 0)}\n\n"
                
                output += "## Status Breakdown\n"
                for status, count in data.get('status_breakdown', {}).items():
                    output += f"- **{status}:** {count}\n"
                
                output += "\n## Recent Grievances\n"
                for g in data.get('recent_grievances', [])[:5]:
                    output += f"- **{g.get('grievance_id')}** - {g.get('status')} ({g.get('category')})\n"
                
                return output
            else:
                return "❌ Error loading dashboard"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def citizen_submit_feedback(self, grievance_id, feedback, rating, attachment_file) -> str:
        try:
            if not grievance_id or not feedback:
                return "❌ Grievance ID and feedback are required"
            
            files = {}
            data = {
                "feedback": feedback,
                "rating": int(rating)
            }
            
            if attachment_file:
                files["attachment"] = open(attachment_file, "rb")
            
            response = requests.post(
                f"{self.api_base}/citizen/grievance/{grievance_id}/feedback",
                data=data,
                files=files if files else None,
                headers=self.get_headers(),
                timeout=10
            )
            
            if files:
                for f in files.values():
                    f.close()
            
            if response.status_code == 200:
                return "✅ Thank you for your feedback!"
            else:
                error = response.json().get("detail", "Failed to submit")
                return f"❌ {error}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # ===== ADDRESSER METHODS =====

    def get_addresser_department_info(self) -> Tuple[str, str]:
        """Get addresser's department name for portal heading"""
        try:
            response = requests.get(
                f"{self.api_base}/addresser/dashboard",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                department = data.get('department', 'Department')
                heading = f"## 🏢 Addresser Portal - {department}\n\n---"
                return heading, department
            else:
                return "## 🏢 Addresser Portal\n\n---", "Department"
        except Exception as e:
            return "## 🏢 Addresser Portal\n\n---", "Department"

    def get_addresser_department_heading(self) -> str:
        """Get department name for addresser portal heading"""
        try:
            response = requests.get(
                f"{self.api_base}/addresser/dashboard",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                department = data.get('department', 'Department')
                return f"## 🏢 Addresser Portal - {department}\n\n---"
            else:
                return "## 🏢 Addresser Portal\n\n---"
        except Exception as e:
            return "## 🏢 Addresser Portal\n\n---"
    
    def addresser_dashboard(self) -> str:
        try:
            response = requests.get(f"{self.api_base}/addresser/dashboard", headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                output = f"# 🏢 {data.get('department')} Department Dashboard\n\n"
                output += f"**Addresser:** {data.get('addresser_name')}\n"
                output += f"**Total Grievances:** {data.get('total_grievances', 0)}\n"
                output += f"**My Updates:** {data.get('my_updates_count', 0)}\n\n"
                
                output += "## Status Breakdown\n"
                for status, count in data.get('status_breakdown', {}).items():
                    output += f"- **{status}:** {count}\n"
                
                output += "\n## Priority Breakdown\n"
                for priority, count in data.get('priority_breakdown', {}).items():
                    output += f"- **{priority}:** {count}\n"
                
                output += "\n## ⚠️ Pending Action Items\n"
                pending = data.get('pending_action', [])
                if pending:
                    for item in pending:
                        output += f"\n**{item['grievance_id']}** ({item['priority']} - {item['days_open']} days)\n"
                        output += f"  {item['summary'][:100]}...\n"
                else:
                    output += "No urgent items\n"
                
                return output
            else:
                return f"❌ Error: {response.json().get('detail', 'Unknown error')}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def addresser_list_grievances(self, status_filter, priority_filter) -> str:
        try:
            params = {"limit": 20}
            if status_filter != "All":
                params["status_filter"] = status_filter
            if priority_filter != "All":
                params["priority"] = priority_filter
            
            response = requests.get(
                f"{self.api_base}/addresser/grievances",
                params=params,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grievances = data.get("grievances", [])
                
                if not grievances:
                    return "📭 No grievances found for your department"
                
                output = f"# 📋 Department Grievances ({data.get('total', 0)} total)\n\n"
                
                for g in grievances:
                    output += f"## {g.get('grievance_id')}\n"
                    output += f"**Status:** {g.get('status')} | **Priority:** {g.get('priority')}\n"
                    output += f"**Category:** {g.get('category')}\n"
                    output += f"**Summary:** {g.get('summary', 'N/A')[:150]}...\n"
                    
                    if g.get('has_my_update'):
                        output += f"✅ **You have updated this ({g.get('my_updates_count')} times)**\n"
                    
                    output += f"**Created:** {g.get('created_at', 'N/A')}\n"
                    output += "---\n\n"
                
                return output
            else:
                return f"❌ Error: {response.json().get('detail', 'Unknown error')}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def addresser_submit_update(self, grievance_id, work_done, remarks, visibility, status_change) -> str:
        try:
            if not grievance_id or not work_done or not remarks:
                return "❌ All fields are required"
            
            data = {
                "work_done": work_done,
                "remarks": remarks,
                "visibility": "admin_only" if visibility == "Admin Only" else "public",
                "status": status_change if status_change != "No Change" else None
            }
            
            response = requests.post(
                f"{self.api_base}/addresser/grievance/{grievance_id}/update",
                json=data,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return f"✅ **Update Submitted Successfully!**\n\nGrievance: {result.get('grievance_id')}\nTimestamp: {result.get('update_timestamp')}\n\n{'Status updated!' if result.get('status_updated') else ''}"
            else:
                error = response.json().get("detail", "Failed to submit")
                return f"❌ {error}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
        
    def addresser_track_grievance(self, grievance_id) -> str:
        """Track grievance from addresser perspective"""
        try:
            if not grievance_id:
                return "❌ Please enter a Grievance ID"
            
            # Get grievance from addresser's department list
            response = requests.get(
                f"{self.api_base}/addresser/grievances",
                params={"limit": 1000},
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                grievances = response.json().get("grievances", [])
                g = next((item for item in grievances if item.get("grievance_id") == grievance_id), None)
                
                if not g:
                    return f"❌ Grievance {grievance_id} not found in your department"
                
                # Format output with department perspective
                output = f"# 📋 Grievance Details (Department View)\n\n"
                output += f"**ID:** `{g.get('grievance_id')}`\n"
                output += f"**Status:** {g.get('status')} 🔴\n"
                output += f"**Priority:** {g.get('priority')}\n"
                output += f"**Category:** {g.get('category')}\n"
                output += f"**Department:** {g.get('department')}\n"
                output += f"**User:** {g.get('user_name', 'Anonymous')} ({g.get('user_contact', 'N/A')})\n"
                output += f"**Location:** {g.get('location', 'N/A')}\n\n"
                
                output += f"## Summary\n{g.get('summary', 'N/A')}\n\n"
                
                output += f"## Original Grievance Text\n{g.get('grievance_text', 'N/A')[:500]}...\n\n"
                
                # NEW: Show audio transcription if available
                audio = g.get('audio_transcription', {})
                if audio and audio.get('success'):
                    output += f"## 🎤 Audio Transcription\n"
                    output += f"**Language:** {audio.get('language', 'N/A')}\n"
                    output += f"**Confidence:** {audio.get('confidence', 0):.1%}\n\n"
                    output += f"```\n{audio.get('text', 'N/A')[:500]}\n```\n\n"
                elif audio and not audio.get('success'):
                    output += f"## 🎤 Audio Processing\n"
                    output += f"❌ Failed: {audio.get('error', 'Unknown error')}\n\n"
                
                # NEW: Show image OCR if available
                image_ocr = g.get('image_ocr', {})
                if image_ocr and image_ocr.get('success'):
                    output += f"## 📷 Text Extracted from Image (OCR)\n"
                    output += f"**Confidence:** {image_ocr.get('confidence', 0):.1%}\n\n"
                    output += f"```\n{image_ocr.get('text', 'N/A')}\n```\n\n"
                elif image_ocr and not image_ocr.get('success'):
                    output += f"## 📷 Image Processing\n"
                    output += f"❌ Failed: {image_ocr.get('error', 'No text found')}\n\n"
                
                # NEW: Show document analysis if available
                doc_analysis = g.get('document_analysis', {})
                if doc_analysis and doc_analysis.get('success'):
                    output += f"## 📄 Attached Document Analysis\n"
                    output += f"**Document Type:** {doc_analysis.get('document_type', 'Unknown')}\n"
                    output += f"**Confidence:** {doc_analysis.get('confidence', 0):.1%}\n\n"
                    
                    extracted = doc_analysis.get('extracted_text', '')
                    if extracted:
                        output += f"### Extracted Text ({len(extracted)} characters)\n"
                        output += f"```\n{extracted[:500]}\n```\n\n"
                    
                    entities = doc_analysis.get('key_entities', {})
                    if entities and any(entities.values()):
                        output += f"### 🔍 Key Information Extracted\n"
                        
                        dates = entities.get('dates', [])
                        if dates:
                            output += f"**📅 Dates:** {', '.join(dates[:5])}\n"
                        
                        amounts = entities.get('amounts', [])
                        if amounts:
                            output += f"**💰 Amounts:** {', '.join(amounts[:5])}\n"
                        
                        locations = entities.get('locations', [])
                        if locations:
                            output += f"**📍 Locations:** {', '.join(locations[:5])}\n"
                        
                        people = entities.get('people', [])
                        if people:
                            output += f"**👤 People:** {', '.join(people[:5])}\n"
                        
                        orgs = entities.get('organizations', [])
                        if orgs:
                            output += f"**🏢 Organizations:** {', '.join(orgs[:5])}\n"
                        
                        output += "\n"
                elif doc_analysis and not doc_analysis.get('success'):
                    output += f"## 📄 Document Processing\n"
                    output += f"❌ Failed: {doc_analysis.get('error', 'Could not extract text')}\n\n"
                
                # Show recommended actions (helpful for addressers)
                actions = g.get('recommended_actions', [])
                if actions:
                    output += "## 📝 AI Recommended Actions\n"
                    for i, action in enumerate(actions, 1):
                        output += f"{i}. {action}\n"
                    output += "\n"
                
                # NEW: Show explainability (helps addressers understand classification)
                explanation = g.get('explanation', {})
                if explanation and any(explanation.values()):
                    output += "## 💡 Why This Classification?\n"
                    if explanation.get('category_reason'):
                        output += f"**Category Reason:** {explanation.get('category_reason')}\n\n"
                    if explanation.get('department_reason'):
                        output += f"**Department Reason:** {explanation.get('department_reason')}\n\n"
                    if explanation.get('priority_reason'):
                        output += f"**Priority Reason:** {explanation.get('priority_reason')}\n\n"
                
                # NEW: Show similar cases
                similar_cases = g.get('similar_cases', [])
                if similar_cases:
                    output += "## 🔗 Similar Resolved Cases (For Reference)\n"
                    output += f"The AI found {len(similar_cases)} similar cases:\n"
                    output += ", ".join([f"`{c}`" for c in similar_cases]) + "\n\n"
                    output += "*💡 Tip: You can reference how these cases were resolved*\n\n"
                
                # NEW: Show confidence score
                confidence = g.get('confidence_score')
                if confidence:
                    output += f"**🎯 AI Classification Confidence:** {confidence:.1%}\n\n"
                
                # Show ALL department updates (including from other addressers)
                updates = g.get('addresser_updates', [])
                if updates:
                    output += "## 📝 Department Updates History\n"
                    for update in updates:
                        # Highlight if this update is from current user
                        is_mine = update.get('addresser_name') == self.current_user.get('full_name')
                        marker = "✅ **YOU**" if is_mine else ""
                        
                        output += f"### {update.get('addresser_name')} {marker}\n"
                        output += f"**Time:** {update.get('timestamp', 'N/A')}\n"
                        output += f"**Work Done:** {update.get('work_done')}\n"
                        output += f"**Remarks:** {update.get('remarks')}\n"
                        output += f"**Visibility:** {update.get('visibility')}\n"
                        if update.get('status_update'):
                            output += f"**Status Changed To:** {update.get('status_update')}\n"
                        output += "\n"
                
                # Highlight if addresser has updated this
                if g.get('has_my_update'):
                    output += f"✅ **You have submitted {g.get('my_updates_count', 0)} update(s) for this grievance**\n\n"
                
                output += f"**Created:** {g.get('created_at', 'N/A')}\n"
                output += f"**Last Updated:** {g.get('updated_at', 'N/A')}\n"
                
                return output
                
            else:
                error = response.json().get("detail", "Error fetching grievances")
                return f"❌ {error}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # ===== ADMIN METHODS =====
    
    def admin_dashboard(self) -> str:
        try:
            response = requests.get(f"{self.api_base}/admin/dashboard", headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                output = f"# 👨‍💼 Admin Dashboard\n\n"
                output += f"**Total Grievances:** {data.get('total_grievances', 0)}\n\n"
                
                output += "## Status Breakdown\n"
                for status, count in data.get('status_breakdown', {}).items():
                    output += f"- **{status}:** {count}\n"
                
                output += "\n## Priority Breakdown\n"
                for priority, count in data.get('priority_breakdown', {}).items():
                    output += f"- **{priority}:** {count}\n"
                
                output += "\n## Department Distribution\n"
                for dept, count in data.get('department_breakdown', {}).items():
                    output += f"- **{dept}:** {count}\n"
                
                return output
            else:
                return "❌ Error loading dashboard"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def admin_list_grievances(self, status_filter, dept_filter, priority_filter) -> str:
        try:
            params = {"limit": 20}
            if status_filter != "All":
                params["status"] = status_filter
            if dept_filter != "All":
                params["department"] = dept_filter
            if priority_filter != "All":
                params["priority"] = priority_filter
            
            response = requests.get(
                f"{self.api_base}/admin/grievances",
                params=params,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grievances = data.get("grievances", [])
                
                if not grievances:
                    return "📭 No grievances found"
                
                output = f"# 📋 All Grievances ({data.get('total', 0)} total)\n\n"
                
                for g in grievances:
                    output += f"## {g.get('grievance_id')}\n"
                    output += f"**Status:** {g.get('status')} | **Priority:** {g.get('priority')}\n"
                    output += f"**Category:** {g.get('category')} | **Dept:** {g.get('department')}\n"
                    output += f"**User:** {g.get('user_name', 'Anonymous')}\n"
                    output += f"**Summary:** {g.get('summary', 'N/A')[:150]}...\n"
                    
                    # Show assignment info
                    assignment = g.get('assignment', {})
                    if assignment:
                        output += f"**Assigned to:** {assignment.get('assigned_to_department')} ({assignment.get('assignment_type')})\n"
                    
                    # NEW: Show confidence and similar cases count
                    confidence = g.get('confidence_score')
                    if confidence:
                        output += f"**AI Confidence:** {confidence:.1%} | "
                    
                    similar_count = len(g.get('similar_cases', []))
                    if similar_count > 0:
                        output += f"**Similar Cases:** {similar_count}\n"
                    else:
                        output += "\n"
                    output += f"**Created:** {g.get('created_at', 'N/A')}\n"
                    output += "---\n\n"
                
                return output
            else:
                return "❌ Error fetching grievances"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def admin_update_status(self, grievance_id, new_status, comment, estimated_resolution) -> str:
        try:
            if not grievance_id or not new_status or not comment:
                return "❌ Grievance ID, status, and comment are required"
            
            data = {
                "status": new_status,
                "admin_comment": comment,
                "estimated_resolution": estimated_resolution if estimated_resolution else None
            }
            
            response = requests.put(
                f"{self.api_base}/admin/grievance/{grievance_id}/status",
                json=data,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return f"✅ Status updated to **{new_status}** successfully!"
            else:
                error = response.json().get("detail", "Update failed")
                return f"❌ {error}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def admin_assign_grievance(self, grievance_id, department, reason) -> str:
        try:
            if not grievance_id:
                return "❌ Grievance ID is required"
            
            data = {
                "department": None if department == "Use AI Suggestion" else department,
                "reason": reason if reason else None
            }
            
            response = requests.put(
                f"{self.api_base}/admin/grievance/{grievance_id}/assign",
                json=data,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                output = f"✅ **{result.get('message')}**\n\n"
                output += f"**Grievance:** {result.get('grievance_id')}\n"
                output += f"**Department:** {result.get('assigned_to_department')}\n"
                output += f"**Assignment Type:** {result.get('assignment_type')}\n"
                if result.get('previous_department'):
                    output += f"**Previous Dept:** {result.get('previous_department')}\n"
                return output
            else:
                error = response.json().get("detail", "Assignment failed")
                return f"❌ {error}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def admin_department_updates(self, dept_filter, status_filter) -> str:
        try:
            params = {"limit": 50}
            if dept_filter != "All":
                params["department"] = dept_filter
            if status_filter != "All":
                params["status_filter"] = status_filter
            
            response = requests.get(
                f"{self.api_base}/admin/department-updates",
                params=params,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                updates = data.get("updates", [])
                
                if not updates:
                    return "📭 No updates found"
                
                output = f"# 📢 Department Updates ({data.get('total_updates', 0)} total)\n\n"
                
                # Show summary
                summary = data.get('department_summary', {})
                if summary:
                    output += "## Department Summary\n"
                    for dept, count in summary.items():
                        output += f"- **{dept}:** {count} updates\n"
                    output += "\n"
                
                output += "## Recent Updates\n\n"
                for item in updates:
                    output += f"### {item.get('grievance_id')} - {item.get('department')}\n"
                    output += f"**Status:** {item.get('status')} | **Priority:** {item.get('priority')}\n"
                    output += f"**Category:** {item.get('category')}\n"
                    output += f"**Summary:** {item.get('summary')}\n\n"
                    
                    latest = item.get('latest_update', {})
                    output += f"**Latest Update by {latest.get('addresser_name')}:**\n"
                    output += f"- Work Done: {latest.get('work_done')}\n"
                    output += f"- Remarks: {latest.get('remarks')}\n"
                    output += f"- Visibility: {latest.get('visibility')}\n"
                    output += f"- Time: {latest.get('timestamp', 'N/A')}\n"
                    
                    output += f"\n**Total Updates:** {item.get('total_updates')}\n"
                    output += "---\n\n"
                
                return output
            else:
                return "❌ Error fetching updates"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def admin_track_grievance(self, grievance_id) -> str:
        try:
            if not grievance_id:
                return "❌ Please enter a Grievance ID"
            
            # Get grievance details from admin list
            response = requests.get(
                f"{self.api_base}/admin/grievances",
                params={"limit": 1000},
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                grievances = response.json().get("grievances", [])
                g = next((item for item in grievances if item.get("grievance_id") == grievance_id), None)
                
                if not g:
                    return f"❌ Grievance {grievance_id} not found"
                
                output = f"# 📋 Grievance Details (Admin View)\n\n"
                output += f"**ID:** `{g.get('grievance_id')}`\n"
                output += f"**Status:** {g.get('status')} 🔴\n"
                output += f"**Priority:** {g.get('priority')}\n"
                output += f"**Category:** {g.get('category')}\n"
                output += f"**Department:** {g.get('department')}\n"
                output += f"**User:** {g.get('user_name', 'Anonymous')} ({g.get('user_contact', 'N/A')})\n"
                output += f"**Location:** {g.get('location', 'N/A')}\n\n"
                
                output += f"## Summary\n{g.get('summary', 'N/A')}\n\n"
                
                output += f"## Original Grievance Text\n{g.get('grievance_text', 'N/A')}\n\n"
                
                # NEW: Show ALL multi-modal inputs (Admin has full access)
                
                # 1. AUDIO TRANSCRIPTION
                audio = g.get('audio_transcription', {})
                if audio and audio.get('success'):
                    output += f"## 🎤 Audio Transcription\n"
                    output += f"**Language:** {audio.get('language', 'N/A')}\n"
                    output += f"**Confidence:** {audio.get('confidence', 0):.1%}\n\n"
                    output += f"### Transcribed Text\n"
                    output += f"```\n{audio.get('text', 'N/A')}\n```\n\n"
                elif audio:
                    output += f"## 🎤 Audio Processing\n"
                    output += f"❌ **Failed:** {audio.get('error', 'Audio transcription not successful')}\n\n"
                
                # 2. IMAGE OCR
                image_ocr = g.get('image_ocr', {})
                if image_ocr and image_ocr.get('success'):
                    output += f"## 📷 Image OCR Analysis\n"
                    output += f"**Confidence:** {image_ocr.get('confidence', 0):.1%}\n\n"
                    output += f"### Extracted Text from Image\n"
                    output += f"```\n{image_ocr.get('text', 'N/A')}\n```\n\n"
                elif image_ocr:
                    output += f"## 📷 Image Processing\n"
                    output += f"❌ **Failed:** {image_ocr.get('error', 'No text extracted from image')}\n\n"
                
                # 3. DOCUMENT ANALYSIS (Most detailed for admin)
                doc_analysis = g.get('document_analysis', {})
                if doc_analysis and doc_analysis.get('success'):
                    output += f"## 📄 Document Understanding Analysis\n"
                    output += f"**Document Type:** {doc_analysis.get('document_type', 'Unknown')}\n"
                    output += f"**Confidence:** {doc_analysis.get('confidence', 0):.1%}\n\n"
                    
                    extracted_text = doc_analysis.get('extracted_text', '')
                    if extracted_text:
                        output += f"### Extracted Text ({len(extracted_text)} characters)\n"
                        output += f"```\n{extracted_text[:1000]}\n```\n"
                        if len(extracted_text) > 1000:
                            output += f"*... and {len(extracted_text) - 1000} more characters*\n"
                        output += "\n"
                    
                    entities = doc_analysis.get('key_entities', {})
                    if entities:
                        output += f"### 🔍 Extracted Entities\n"
                        
                        dates = entities.get('dates', [])
                        if dates:
                            output += f"**📅 Dates:** {', '.join(dates)}\n"
                        
                        amounts = entities.get('amounts', [])
                        if amounts:
                            output += f"**💰 Monetary Amounts:** {', '.join(amounts)}\n"
                        
                        locations = entities.get('locations', [])
                        if locations:
                            output += f"**📍 Locations:** {', '.join(locations)}\n"
                        
                        people = entities.get('people', [])
                        if people:
                            output += f"**👤 People Mentioned:** {', '.join(people)}\n"
                        
                        orgs = entities.get('organizations', [])
                        if orgs:
                            output += f"**🏢 Organizations:** {', '.join(orgs)}\n"
                        
                        output += "\n"
                elif doc_analysis:
                    output += f"## 📄 Document Processing\n"
                    output += f"❌ **Failed:** {doc_analysis.get('error', 'Document analysis unsuccessful')}\n"
                    debug_info = doc_analysis.get('debug_info', {})
                    if debug_info:
                        output += f"**Debug Info:** Type: {debug_info.get('file_type')}, Size: {debug_info.get('file_size')} bytes\n"
                    output += "\n"
                
                # Show assignment
                assignment = g.get('assignment', {})
                if assignment:
                    output += "## 🎯 Assignment Information\n"
                    output += f"- **Department:** {assignment.get('assigned_to_department')}\n"
                    output += f"- **Assigned By:** {assignment.get('assigned_by_name')}\n"
                    output += f"- **Type:** {assignment.get('assignment_type')}\n"
                    output += f"- **Date:** {assignment.get('assigned_at', 'N/A')}\n\n"
                
                # Show recommended actions
                actions = g.get('recommended_actions', [])
                if actions:
                    output += "## 📝 AI Recommended Actions\n"
                    for i, action in enumerate(actions, 1):
                        output += f"{i}. {action}\n"
                    output += "\n"
                
                # NEW: Show explainability (Admin can see full AI reasoning)
                explanation = g.get('explanation', {})
                if explanation and any(explanation.values()):
                    output += "## 💡 AI Classification Reasoning\n"
                    if explanation.get('category_reason'):
                        output += f"**Why this Category?**\n{explanation.get('category_reason')}\n\n"
                    if explanation.get('department_reason'):
                        output += f"**Why this Department?**\n{explanation.get('department_reason')}\n\n"
                    if explanation.get('priority_reason'):
                        output += f"**Why this Priority?**\n{explanation.get('priority_reason')}\n\n"
                
                # NEW: Show similar cases (Admin can investigate patterns)
                similar_cases = g.get('similar_cases', [])
                if similar_cases:
                    output += "## 🔗 Similar Resolved Cases Found\n"
                    output += f"The AI identified {len(similar_cases)} similar cases:\n\n"
                    for case_id in similar_cases:
                        output += f"- `{case_id}`\n"
                    output += "\n*💡 These cases can provide insights for resolution strategies*\n\n"
                
                # NEW: Show confidence score (Important for admin to assess AI accuracy)
                confidence = g.get('confidence_score')
                if confidence:
                    confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                    output += f"**🎯 AI Classification Confidence:** {confidence:.1%} {confidence_emoji}\n"
                    if confidence < 0.7:
                        output += f"*⚠️ Low confidence - manual review recommended*\n"
                    output += "\n"
                
                # Show addresser updates (all, including admin_only)
                updates = g.get('addresser_updates', [])
                if updates:
                    output += "## 📢 Addresser Updates (All)\n"
                    for update in updates:
                        visibility_badge = "🔒 ADMIN ONLY" if update.get('visibility') == 'admin_only' else "👁️ PUBLIC"
                        output += f"### {update.get('addresser_name')} ({update.get('department')}) {visibility_badge}\n"
                        output += f"**Time:** {update.get('timestamp', 'N/A')}\n"
                        output += f"**Work Done:** {update.get('work_done')}\n"
                        output += f"**Remarks:** {update.get('remarks')}\n"
                        if update.get('status_update'):
                            output += f"**Status Updated To:** {update.get('status_update')}\n"
                        output += "\n"
                
                # Show processing logs
                logs = g.get('processing_logs', [])
                if logs:
                    output += "## 📊 Processing History\n"
                    for log in logs[-3:]:  # Show last 3 logs
                        output += f"- **{log.get('action')}** by {log.get('actor')} - {log.get('timestamp', 'N/A')}\n"
                        output += f"  _{log.get('details', 'N/A')}_\n"
                    output += "\n"
                
                output += f"**Created:** {g.get('created_at', 'N/A')}\n"
                output += f"**Last Updated:** {g.get('updated_at', 'N/A')}\n"
                
                return output
            else:
                return "❌ Error fetching grievance"
        except Exception as e:
            return f"❌ Error: {str(e)}"


def create_complete_ui():
    """Create the complete Gradio interface"""
    ui = CompleteGrievanceUI()
    
    with gr.Blocks(title="Grievance Redressal System") as demo:
        gr.Markdown("# 🏛️ AI-Powered Grievance Redressal System")
        
        # Hidden state variables
        is_logged_in = gr.State(False)
        user_role = gr.State("")
        
        # ===== AUTHENTICATION SECTION =====
        with gr.Group(visible=True) as auth_section:
            gr.Markdown("## 🔐 Authentication")
            
            with gr.Tabs():
                with gr.Tab("🔑 Login"):
                    login_email = gr.Textbox(label="📧 Email or Phone")
                    login_password = gr.Textbox(label="🔒 Password", type="password")
                    login_btn = gr.Button("🔑 Login", variant="primary", elem_classes="submit-btn")
                    login_status = gr.Markdown()
                
                with gr.Tab("📝 Register"):
                    reg_email = gr.Textbox(label="📧 Email*")
                    reg_phone = gr.Textbox(label="📱 Phone (Optional)", placeholder="+91XXXXXXXXXX")
                    reg_password = gr.Textbox(label="🔒 Password*", type="password")
                    reg_confirm = gr.Textbox(label="🔒 Confirm Password*", type="password")
                    reg_name = gr.Textbox(label="👤 Full Name*")
                    reg_role = gr.Radio(choices=["Citizen", "Admin", "Addresser"], value="Citizen", label="Role")
                    reg_department = gr.Dropdown(choices=DEPARTMENTS, label="🏢 Department (Required for Addresser)", visible=False)
                    reg_location = gr.Textbox(label="📍 Location")
                    register_btn = gr.Button("📝 Register", variant="primary", elem_classes="submit-btn")
                    register_status = gr.Markdown()
                    
                    # Show/hide department based on role
                    def toggle_department(role):
                        return gr.update(visible=role=="Addresser")
                    reg_role.change(toggle_department, reg_role, reg_department)
        
        # ===== LOGGED IN SECTION =====
        with gr.Group(visible=False) as logged_in_section:
            with gr.Row():
                gr.Markdown("### ✅ Logged In")
                logout_btn = gr.Button("🚪 Logout", elem_classes="logout-btn")
            logout_status = gr.Markdown()
            
            # ===== CITIZEN PORTAL =====
            # ===== CHATBOT-STYLE CITIZEN PORTAL =====
            with gr.Group(visible=False) as citizen_portal:
                gr.Markdown("## 👤 Citizen Portal - AI Assistant\n\n---")
                
                with gr.Tabs():
                    # TAB 1: Chatbot Grievance Submission
                    with gr.Tab("💬 Submit New Grievance"):
                        # Chatbot Interface
                        chatbot = gr.Chatbot(
                            label="Grievance Assistant",
                            height=400,
                            show_label=True,
                            avatar_images=(None, "🤖")
                        )
                        
                        # Conversation State Management
                        chat_state = gr.State({
                            "step": 0,
                            "grievance_text": "",
                            "language": "English",
                            "location": "",
                            "has_attachment": False
                        })
                        
                        # Hidden storage for form data (reusing existing variables)
                        cit_text = gr.Textbox(visible=False)
                        cit_language = gr.Radio(choices=["English", "Telugu"], value="English", visible=False)
                        cit_location = gr.Textbox(visible=False)
                        cit_image = gr.State(None)
                        cit_audio = gr.State(None)
                        cit_document = gr.State(None)
                        
                        # Step-based Input Areas (dynamically shown)
                        with gr.Group(visible=True) as step_0_group:
                            gr.Markdown("### 📝 Describe Your Grievance")
                            with gr.Row():
                                user_text_input = gr.Textbox(
                                    label="Type your grievance here",
                                    placeholder="Explain your issue in detail...",
                                    lines=4,
                                    scale=4
                                )
                                with gr.Column(scale=1):
                                    gr.Markdown("**OR**")
                                    voice_input_btn = gr.Button("🎙️ Voice Input", size="sm")
                            
                            # Voice recording interface (initially hidden)
                            with gr.Group(visible=False) as voice_recording_group:
                                gr.Markdown("🎤 **Recording...**")
                                audio_input = gr.Audio(
                                    type="filepath",
                                    label="Speak your grievance"
                                )
                                with gr.Row():
                                    convert_voice_btn = gr.Button("✅ Convert to Text", variant="primary")
                                    cancel_voice_btn = gr.Button("❌ Cancel")
                            
                            next_step_0_btn = gr.Button("Next ➡️", variant="primary")
                        
                        with gr.Group(visible=False) as step_1_group:
                            gr.Markdown("### 🌐 Select Language")
                            language_radio = gr.Radio(
                                choices=["English", "Telugu"],
                                value="English",
                                label="Preferred Language"
                            )
                            with gr.Row():
                                back_step_1_btn = gr.Button("⬅️ Back")
                                next_step_1_btn = gr.Button("Next ➡️", variant="primary")
                        
                        with gr.Group(visible=False) as step_2_group:
                            gr.Markdown("### 📍 Location (Optional)")
                            location_input = gr.Textbox(
                                label="Enter your location",
                                placeholder="Ward/District/Area",
                                lines=1
                            )
                            with gr.Row():
                                back_step_2_btn = gr.Button("⬅️ Back")
                                next_step_2_btn = gr.Button("Next ➡️", variant="primary")
                        
                        with gr.Group(visible=False) as step_3_group:
                            gr.Markdown("### 📎 Attachments (Optional)")
                            gr.Markdown("Upload supporting evidence if needed:")
                            
                            attachment_type = gr.Radio(
                                choices=["None", "Image 📷", "Audio 🎤", "Document 📄"],
                                value="None",
                                label="Select attachment type"
                            )
                            
                            # File upload interfaces (shown based on selection)
                            image_upload = gr.File(
                                label="Upload Image",
                                file_types=["image"],
                                visible=False
                            )
                            audio_upload = gr.File(
                                label="Upload Audio",
                                file_types=["audio"],
                                visible=False
                            )
                            document_upload = gr.File(
                                label="Upload Document (PDF, Word, etc.)",
                                file_types=[".pdf", ".doc", ".docx"],
                                visible=False
                            )
                            
                            with gr.Row():
                                back_step_3_btn = gr.Button("⬅️ Back")
                                next_step_3_btn = gr.Button("Next ➡️", variant="primary")
                        
                        with gr.Group(visible=False) as step_4_group:
                            gr.Markdown("### ✅ Review & Submit")
                            review_output = gr.Markdown()
                            
                            with gr.Row():
                                back_step_4_btn = gr.Button("⬅️ Back")
                                cit_submit_btn = gr.Button("📤 Submit Grievance", variant="primary")
                                reset_chat_btn = gr.Button("🔄 Start New Grievance", variant="stop")
                        
                        cit_submit_output = gr.Markdown()
                        
                        # ===== CHATBOT LOGIC FUNCTIONS =====
                        
                        def initialize_chat():
                            """Start chatbot conversation"""
                            return [
                                {"role": "assistant", "content": "Hello 👋 Welcome to the Grievance Redressal System.\n\n**Let's submit your grievance step by step.**\n\nPlease describe your grievance below. You can type it or use voice input."}
                            ], {"step": 0, "grievance_text": "", "language": "English", "location": "", "has_attachment": False}
                        
                        def toggle_voice_interface(voice_visible):
                            """Show/hide voice recording interface"""
                            return gr.update(visible=not voice_visible), gr.update(visible=voice_visible)
                        
                        def convert_speech_to_text(audio_file, current_text):
                            """Convert audio to text and populate textbox"""
                            if audio_file is None:
                                return current_text, gr.update(visible=True), gr.update(visible=False), "⚠️ No audio recorded"
                            
                            try:
                                # Method 1: Use OpenAI Whisper (most accurate, works offline)
                                if WHISPER_AVAILABLE:
                                    try:
                                        result = whisper_model.transcribe(audio_file, language="en")
                                        converted_text = result["text"].strip()
                                        
                                        if converted_text:
                                            return (
                                                converted_text,
                                                gr.update(visible=True),
                                                gr.update(visible=False),
                                                "✅ Voice converted to text using Whisper! You can edit it before proceeding."
                                            )
                                    except Exception as e:
                                        print(f"Whisper failed: {e}")
                                
                                # Method 2: Use Google Speech Recognition (requires internet)
                                if SPEECH_RECOGNITION_AVAILABLE:
                                    try:
                                        recognizer = sr.Recognizer()
                                        
                                        # Load audio file
                                        with sr.AudioFile(audio_file) as source:
                                            audio_data = recognizer.record(source)
                                        
                                        # Try Google Speech Recognition
                                        try:
                                            converted_text = recognizer.recognize_google(audio_data)
                                            return (
                                                converted_text,
                                                gr.update(visible=True),
                                                gr.update(visible=False),
                                                "✅ Voice converted to text using Google Speech Recognition! You can edit it before proceeding."
                                            )
                                        except sr.UnknownValueError:
                                            return (
                                                current_text,
                                                gr.update(visible=True),
                                                gr.update(visible=False),
                                                "⚠️ Could not understand audio. Please try speaking more clearly."
                                            )
                                        except sr.RequestError:
                                            return (
                                                current_text,
                                                gr.update(visible=True),
                                                gr.update(visible=False),
                                                "⚠️ Could not connect to speech recognition service. Please check your internet connection."
                                            )
                                    except Exception as e:
                                        print(f"Speech Recognition failed: {e}")
                                
                                # Fallback: Show error if no methods available
                                return (
                                    current_text,
                                    gr.update(visible=True),
                                    gr.update(visible=False),
                                    "❌ Speech-to-text not configured. Please install: pip install openai-whisper OR pip install SpeechRecognition"
                                )
                                
                            except Exception as e:
                                return (
                                    current_text,
                                    gr.update(visible=True),
                                    gr.update(visible=False),
                                    f"❌ Error converting voice: {str(e)}"
                                )
                        
                        def cancel_voice_input():
                            """Cancel voice recording"""
                            return gr.update(visible=True), gr.update(visible=False), ""
                        
                        def step_0_next(text, chat_history, state):
                            """Move from grievance input to language selection"""
                            if not text or text.strip() == "":
                                return (
                                    chat_history,
                                    state,
                                    gr.update(visible=True),
                                    gr.update(visible=False),
                                    "⚠️ Please enter your grievance before proceeding."
                                )
                            
                            state["grievance_text"] = text.strip()
                            state["step"] = 1
                            
                            chat_history.append({"role": "user", "content": text[:100] + "..." if len(text) > 100 else text})
                            chat_history.append({"role": "assistant", "content": "✅ Grievance recorded.\n\n**Step 2:** Please select your preferred language."})
                            
                            return (
                                chat_history,
                                state,
                                gr.update(visible=False),
                                gr.update(visible=True),
                                ""
                            )
                        
                        def step_1_next(language, chat_history, state):
                            """Move from language to location"""
                            state["language"] = language
                            state["step"] = 2
                            
                            chat_history.append({"role": "user", "content": f"Language: {language}"})
                            chat_history.append({"role": "assistant", "content": "✅ Language selected.\n\n**Step 3:** Please enter your location (optional)."})
                            
                            return (
                                chat_history,
                                state,
                                gr.update(visible=False),
                                gr.update(visible=True)
                            )
                        
                        def step_1_back(chat_history, state):
                            """Go back to grievance input"""
                            state["step"] = 0
                            return (
                                chat_history,
                                state,
                                gr.update(visible=True),
                                gr.update(visible=False)
                            )
                        
                        def step_2_next(location, chat_history, state):
                            """Move from location to attachments"""
                            state["location"] = location.strip() if location else ""
                            state["step"] = 3
                            
                            location_msg = location if location else "Not specified"
                            chat_history.append({"role": "user", "content": f"Location: {location_msg}"})
                            chat_history.append({"role": "assistant", "content": "✅ Location recorded.\n\n**Step 4:** Would you like to upload any supporting files? (Optional)"})
                            
                            return (
                                chat_history,
                                state,
                                gr.update(visible=False),
                                gr.update(visible=True)
                            )
                        
                        def step_2_back(chat_history, state):
                            """Go back to language selection"""
                            state["step"] = 1
                            return (
                                chat_history,
                                state,
                                gr.update(visible=True),
                                gr.update(visible=False)
                            )
                        
                        def toggle_attachment_upload(attachment_type):
                            """Show appropriate file upload based on selection"""
                            return (
                                gr.update(visible=attachment_type == "Image 📷"),
                                gr.update(visible=attachment_type == "Audio 🎤"),
                                gr.update(visible=attachment_type == "Document 📄")
                            )
                        
                        def step_3_next(attachment_type, img_file, aud_file, doc_file, chat_history, state):
                            """Move from attachments to review"""
                            state["step"] = 4
                            state["has_attachment"] = attachment_type != "None"
                            
                            # Store files
                            files_uploaded = []
                            if attachment_type == "Image 📷" and img_file:
                                files_uploaded.append("📷 Image")
                            elif attachment_type == "Audio 🎤" and aud_file:
                                files_uploaded.append("🎤 Audio")
                            elif attachment_type == "Document 📄" and doc_file:
                                files_uploaded.append("📄 Document")
                            
                            attachment_msg = ", ".join(files_uploaded) if files_uploaded else "None"
                            chat_history.append({"role": "user", "content": f"Attachments: {attachment_msg}"})
                            chat_history.append({"role": "assistant", "content": "✅ Attachments recorded.\n\n**Step 5:** Please review your submission."})
                            
                            # Generate review
                            review = f"""
            ### 📋 Review Your Submission

            **Grievance:**  
            {state['grievance_text'][:200]}{'...' if len(state['grievance_text']) > 200 else ''}

            **Language:** {state['language']}  
            **Location:** {state['location'] if state['location'] else 'Not specified'}  
            **Attachments:** {attachment_msg}

            ---

            **Click "Submit Grievance" to proceed or go back to make changes.**
            """
                            
                            return (
                                chat_history,
                                state,
                                gr.update(visible=False),
                                gr.update(visible=True),
                                review,
                                img_file,
                                aud_file,
                                doc_file
                            )
                        
                        def step_3_back(chat_history, state):
                            """Go back to location"""
                            state["step"] = 2
                            return (
                                chat_history,
                                state,
                                gr.update(visible=True),
                                gr.update(visible=False)
                            )
                        
                        def step_4_back(chat_history, state):
                            """Go back to attachments"""
                            state["step"] = 3
                            return (
                                chat_history,
                                state,
                                gr.update(visible=True),
                                gr.update(visible=False)
                            )
                        
                        def populate_hidden_fields(state, img, aud, doc):
                            """Populate hidden form fields before submission"""
                            return (
                                state["grievance_text"],
                                state["language"],
                                state["location"],
                                img,
                                aud,
                                doc
                            )
                        
                        def reset_chatbot():
                            """Reset entire chatbot to initial state"""
                            initial_chat, initial_state = initialize_chat()
                            return (
                                initial_chat,
                                initial_state,
                                "",  # user_text_input
                                "English",  # language_radio
                                "",  # location_input
                                "None",  # attachment_type
                                None,  # image_upload
                                None,  # audio_upload
                                None,  # document_upload
                                "",  # review_output
                                "",  # cit_submit_output
                                gr.update(visible=True),  # step_0_group
                                gr.update(visible=False),  # step_1_group
                                gr.update(visible=False),  # step_2_group
                                gr.update(visible=False),  # step_3_group
                                gr.update(visible=False),  # step_4_group
                                "",  # cit_text
                                "English",  # cit_language
                                "",  # cit_location
                                None,  # cit_image
                                None,  # cit_audio
                                None  # cit_document
                            )
                        
                        # ===== EVENT BINDINGS =====
                        
                        
                        # Voice input toggle
                        voice_input_btn.click(
                            lambda: (gr.update(visible=False), gr.update(visible=True)),
                            outputs=[step_0_group, voice_recording_group]
                        )
                        
                        convert_voice_btn.click(
                            convert_speech_to_text,
                            inputs=[audio_input, user_text_input],
                            outputs=[user_text_input, step_0_group, voice_recording_group, cit_submit_output]
                        )
                        
                        cancel_voice_btn.click(
                            cancel_voice_input,
                            outputs=[step_0_group, voice_recording_group, cit_submit_output]
                        )
                        
                        # Step 0: Grievance text → Language
                        next_step_0_btn.click(
                            step_0_next,
                            inputs=[user_text_input, chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_0_group, step_1_group, cit_submit_output]
                        )
                        
                        # Step 1: Language → Location
                        next_step_1_btn.click(
                            step_1_next,
                            inputs=[language_radio, chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_1_group, step_2_group]
                        )
                        
                        back_step_1_btn.click(
                            step_1_back,
                            inputs=[chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_0_group, step_1_group]
                        )
                        
                        # Step 2: Location → Attachments
                        next_step_2_btn.click(
                            step_2_next,
                            inputs=[location_input, chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_2_group, step_3_group]
                        )
                        
                        back_step_2_btn.click(
                            step_2_back,
                            inputs=[chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_1_group, step_2_group]
                        )
                        
                        # Attachment type selection
                        attachment_type.change(
                            toggle_attachment_upload,
                            inputs=[attachment_type],
                            outputs=[image_upload, audio_upload, document_upload]
                        )
                        
                        # Step 3: Attachments → Review
                        next_step_3_btn.click(
                            step_3_next,
                            inputs=[attachment_type, image_upload, audio_upload, document_upload, chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_3_group, step_4_group, review_output, cit_image, cit_audio, cit_document]
                        )
                        
                        back_step_3_btn.click(
                            step_3_back,
                            inputs=[chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_2_group, step_3_group]
                        )
                        
                        # Step 4: Review → Submit
                        back_step_4_btn.click(
                            step_4_back,
                            inputs=[chatbot, chat_state],
                            outputs=[chatbot, chat_state, step_3_group, step_4_group]
                        )
                        
                        # Populate hidden fields before submission
                        cit_submit_btn.click(
                            populate_hidden_fields,
                            inputs=[chat_state, cit_image, cit_audio, cit_document],
                            outputs=[cit_text, cit_language, cit_location, cit_image, cit_audio, cit_document]
                        ).then(
                            ui.citizen_submit_grievance,
                            inputs=[cit_text, cit_language, cit_location, cit_image, cit_audio, cit_document],
                            outputs=[cit_submit_output]
                        )
                        
                        # Reset chatbot
                        reset_chat_btn.click(
                            reset_chatbot,
                            outputs=[
                                chatbot, chat_state, user_text_input, language_radio, location_input,
                                attachment_type, image_upload, audio_upload, document_upload,
                                review_output, cit_submit_output,
                                step_0_group, step_1_group, step_2_group, step_3_group, step_4_group,
                                cit_text, cit_language, cit_location, cit_image, cit_audio, cit_document
                            ]
                        )
                    
                    # TAB 1b: Traditional Form Submission
                    with gr.Tab("📝 Traditional Form Submission"):
                        gr.Markdown("### 📝 Submit Grievance via Form\n\nIf you prefer to submit all information at once, please fill out the form below.")
                        with gr.Column():
                            form_text = gr.Textbox(
                                label="Describe Your Grievance*",
                                placeholder="Explain your issue in detail...",
                                lines=5
                            )
                            with gr.Row():
                                form_language = gr.Dropdown(
                                    choices=["English", "Telugu"],
                                    value="English",
                                    label="Preferred Language"
                                )
                                form_location = gr.Textbox(
                                    label="Location (Optional)",
                                    placeholder="Ward/District/Area"
                                )
                            with gr.Row():
                                form_image = gr.File(
                                    label="📎 Upload Image (Optional)",
                                    file_types=["image"]
                                )
                                form_audio = gr.File(
                                    label="📎 Upload Audio (Optional)",
                                    file_types=["audio"]
                                )
                                form_document = gr.File(
                                    label="📎 Upload Document (Optional - PDF, Word)",
                                    file_types=[".pdf", ".doc", ".docx"]
                                )
                            form_submit_btn = gr.Button("📤 Submit Grievance", variant="primary", elem_classes="submit-btn")
                            form_submit_output = gr.Markdown()
                    
                    # TAB 2-5: Keep existing tabs unchanged
                    with gr.Tab("🔍 Track Grievance"):
                        cit_track_id = gr.Textbox(label="Grievance ID")
                        cit_track_btn = gr.Button("🔍 Track", variant="primary", elem_classes="track-btn")
                        cit_track_output = gr.Markdown()
                    
                    with gr.Tab("📋 My Grievances"):
                        cit_status_filter = gr.Dropdown(
                            choices=["All", "Open", "In Review", "Resolved", "Rejected"],
                            value="All",
                            label="Filter by Status"
                        )
                        cit_load_btn = gr.Button("📋 Load My Grievances", variant="primary")
                        cit_my_grievances_output = gr.Markdown()
                    
                    with gr.Tab("📊 Dashboard"):
                        cit_dashboard_btn = gr.Button("🔄 Refresh Dashboard", variant="primary")
                        cit_dashboard_output = gr.Markdown()
                    
                    with gr.Tab("⭐ Submit Feedback"):
                        gr.Markdown("**Note:** Only Grievance ID and feedback text are required. Attachment is optional.")
                        cit_feedback_id = gr.Textbox(label="Grievance ID*")
                        cit_feedback_text = gr.Textbox(label="Your Feedback*", lines=4, placeholder="Share your experience...")
                        cit_rating = gr.Slider(minimum=1, maximum=5, value=5, step=1, label="Rating (1-5)")
                        gr.Markdown("### Optional Attachment")
                        cit_feedback_attachment = gr.File(label="📎 Attach Document (Optional - e.g., photos, receipts)", file_types=[".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"])
                        cit_feedback_btn = gr.Button("📤 Submit Feedback", variant="primary", elem_classes="submit-btn")
                        cit_feedback_output = gr.Markdown()
            
            # ===== ADDRESSER PORTAL =====
            with gr.Group(visible=False) as addresser_portal:
                addresser_heading = gr.Markdown("## 🏢 Addresser Portal\n\n---")
                
                with gr.Tabs():
                    with gr.Tab("📊 Dashboard"):
                        addresser_dashboard_btn = gr.Button("🔄 Refresh", variant="primary")
                        addresser_dashboard_output = gr.Markdown()
                        
                        # Update heading when dashboard loads
                        addresser_dashboard_btn.click(
                            ui.get_addresser_department_heading,
                            outputs=addresser_heading
                        )

                    
                    with gr.Tab("📋 Department Grievances"):
                        with gr.Row():
                            addr_status_filter = gr.Dropdown(
                                choices=["All", "Open", "In Review", "Resolved"],
                                value="All",
                                label="Status"
                            )
                            addr_priority_filter = gr.Dropdown(
                                choices=["All", "Low", "Medium", "High", "Critical"],
                                value="All",
                                label="Priority"
                            )
                        addr_load_btn = gr.Button("📋 Load Grievances", variant="primary")
                        addr_grievances_output = gr.Markdown()
                    
                    with gr.Tab("✏️ Submit Update"):
                        addr_update_id = gr.Textbox(label="Grievance ID*")
                        addr_work_done = gr.Textbox(label="Work Done*", lines=4, placeholder="Describe what work has been completed...")
                        addr_remarks = gr.Textbox(label="Remarks*", lines=3, placeholder="Additional comments or next steps...")
                        addr_visibility = gr.Radio(choices=["Admin Only", "Public"], value="Admin Only", label="Visibility")
                        addr_status_change = gr.Dropdown(
                            choices=["No Change", "In Review", "Resolved"],
                            value="No Change",
                            label="Update Status (Optional)"
                        )
                        addr_submit_btn = gr.Button("📤 Submit Update", variant="primary", elem_classes="submit-btn")
                        addr_update_output = gr.Markdown()
                    
                    with gr.Tab("🔍 Track Grievance"):
                        addr_track_id = gr.Textbox(label="Grievance ID")
                        addr_track_btn = gr.Button("🔍 Track", variant="primary", elem_classes="track-btn")
                        addr_track_output = gr.Markdown()
            
            # ===== ADMIN PORTAL =====
            with gr.Group(visible=False) as admin_portal:
                gr.Markdown("## 👨‍💼 Admin Panel\n\n---")
                with gr.Tabs():
                    with gr.Tab("📊 Dashboard"):
                        admin_dashboard_btn = gr.Button("🔄 Refresh Dashboard", variant="primary")
                        admin_dashboard_output = gr.Markdown()
                    
                    with gr.Tab("📋 All Grievances"):
                        with gr.Row():
                            admin_status_filter = gr.Dropdown(choices=["All", "Open", "In Review", "Resolved", "Rejected"], value="All", label="Status")
                            admin_dept_filter = gr.Dropdown(choices=["All"] + DEPARTMENTS, value="All", label="Department")
                            admin_priority_filter = gr.Dropdown(choices=["All", "Low", "Medium", "High", "Critical"], value="All", label="Priority")
                        admin_load_btn = gr.Button("📋 Load All Grievances", variant="primary")
                        admin_grievances_output = gr.Markdown()
                    
                    with gr.Tab("✏️ Update Status"):
                        admin_update_id = gr.Textbox(label="Grievance ID*")
                        admin_new_status = gr.Dropdown(choices=["Open", "In Review", "Resolved", "Rejected"], label="New Status*")
                        admin_comment = gr.Textbox(label="Admin Comment*", lines=3, placeholder="Explain the status update...")
                        admin_resolution = gr.Textbox(label="Estimated Resolution (Optional)", placeholder="e.g., 7-10 days")
                        admin_update_btn = gr.Button("✅ Update Status", variant="primary", elem_classes="submit-btn")
                        admin_update_output = gr.Markdown()
                    
                    with gr.Tab("🎯 Assign Grievance"):
                        assign_grievance_id = gr.Textbox(label="Grievance ID*")
                        assign_department = gr.Dropdown(
                            choices=["Use AI Suggestion"] + DEPARTMENTS,
                            value="Use AI Suggestion",
                            label="Assign To Department"
                        )
                        assign_reason = gr.Textbox(label="Reason (Optional)", placeholder="Why are you assigning/reassigning?")
                        assign_btn = gr.Button("🎯 Assign", variant="primary", elem_classes="submit-btn")
                        assign_output = gr.Markdown()
                    
                    with gr.Tab("📢 Department Updates"):
                        with gr.Row():
                            dept_update_filter = gr.Dropdown(choices=["All"] + DEPARTMENTS, value="All", label="Department")
                            dept_status_filter = gr.Dropdown(choices=["All", "Open", "In Review", "Resolved"], value="All", label="Status")
                        dept_updates_btn = gr.Button("🔄 Load Updates", variant="primary")
                        dept_updates_output = gr.Markdown()
                    
                    with gr.Tab("🔍 Track Grievance"):
                        admin_track_id = gr.Textbox(label="Grievance ID")
                        admin_track_btn = gr.Button("🔍 Track", variant="primary", elem_classes="track-btn")
                        admin_track_output = gr.Markdown()
        
        # ===== EVENT HANDLERS =====
        
        def handle_login(email, password):
            status, logged_in, role = ui.login_user(email, password)
            show_citizen = role == "Citizen"
            show_admin = role == "Admin"
            show_addresser = role == "Addresser"
            
            # Initialize chatbot for citizens - Gradio 6.0 format
            if show_citizen:
                chatbot_history = [{"role": "assistant", "content": "Hello 👋 Welcome to the Grievance Redressal System.\n\n**Let's submit your grievance step by step.**\n\nPlease describe your grievance below. You can type it or use voice input."}]
                chat_state_init = {"step": 0, "grievance_text": "", "language": "English", "location": "", "has_attachment": False}
            else:
                chatbot_history = []
                chat_state_init = {}
            
            return (
                status, logged_in, role,
                gr.update(visible=not logged_in),
                gr.update(visible=logged_in),
                gr.update(visible=show_citizen),
                gr.update(visible=show_admin),
                gr.update(visible=show_addresser),
                chatbot_history,
                chat_state_init
            )
        
        def handle_register(email, phone, password, confirm, name, role, department, location):
            status, logged_in, role_out = ui.register_user(email, phone, password, confirm, name, role, department, location)
            show_citizen = role_out == "Citizen"
            show_admin = role_out == "Admin"
            show_addresser = role_out == "Addresser"
            
            # Initialize chatbot for citizens - Gradio 6.0 format
            if show_citizen:
                chatbot_history = [{"role": "assistant", "content": "Hello 👋 Welcome to the Grievance Redressal System.\n\n**Let's submit your grievance step by step.**\n\nPlease describe your grievance below. You can type it or use voice input."}]
                chat_state_init = {"step": 0, "grievance_text": "", "language": "English", "location": "", "has_attachment": False}
            else:
                chatbot_history = []
                chat_state_init = {}
            
            return (
                status, logged_in, role_out,
                gr.update(visible=not logged_in),
                gr.update(visible=logged_in),
                gr.update(visible=show_citizen),
                gr.update(visible=show_admin),
                gr.update(visible=show_addresser),
                chatbot_history,
                chat_state_init
            )
        
        def handle_logout():
            status = ui.logout_user()
            return (
                status, False, "",
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            )
        
        # Auth event handlers
        login_btn.click(
            handle_login,
            [login_email, login_password],
            [login_status, is_logged_in, user_role, auth_section, logged_in_section, citizen_portal, admin_portal, addresser_portal, chatbot, chat_state]
        )
        
        register_btn.click(
            handle_register,
            [reg_email, reg_phone, reg_password, reg_confirm, reg_name, reg_role, reg_department, reg_location],
            [register_status, is_logged_in, user_role, auth_section, logged_in_section, citizen_portal, admin_portal, addresser_portal, chatbot, chat_state]
        )
        
        logout_btn.click(
            handle_logout,
            outputs=[logout_status, is_logged_in, user_role, auth_section, logged_in_section, citizen_portal, admin_portal, addresser_portal]
        )
        
        # Citizen event handlers
        form_submit_btn.click(
            ui.citizen_submit_grievance,
            inputs=[form_text, form_language, form_location, form_image, form_audio, form_document],
            outputs=[form_submit_output]
        )
        cit_track_btn.click(ui.citizen_track_grievance, cit_track_id, cit_track_output)
        cit_load_btn.click(ui.citizen_my_grievances, cit_status_filter, cit_my_grievances_output)
        cit_dashboard_btn.click(ui.citizen_dashboard, outputs=cit_dashboard_output)
        cit_feedback_btn.click(ui.citizen_submit_feedback, [cit_feedback_id, cit_feedback_text, cit_rating, cit_feedback_attachment], cit_feedback_output)
        
        # Addresser event handlers
        addresser_dashboard_btn.click(ui.addresser_dashboard, outputs=addresser_dashboard_output)
        addr_load_btn.click(ui.addresser_list_grievances, [addr_status_filter, addr_priority_filter], addr_grievances_output)
        addr_submit_btn.click(ui.addresser_submit_update, [addr_update_id, addr_work_done, addr_remarks, addr_visibility, addr_status_change], addr_update_output)
        addr_track_btn.click(ui.addresser_track_grievance, addr_track_id, addr_track_output)
        
        # Admin event handlers
        admin_dashboard_btn.click(ui.admin_dashboard, outputs=admin_dashboard_output)
        admin_load_btn.click(ui.admin_list_grievances, [admin_status_filter, admin_dept_filter, admin_priority_filter], admin_grievances_output)
        admin_update_btn.click(ui.admin_update_status, [admin_update_id, admin_new_status, admin_comment, admin_resolution], admin_update_output)
        assign_btn.click(ui.admin_assign_grievance, [assign_grievance_id, assign_department, assign_reason], assign_output)
        dept_updates_btn.click(ui.admin_department_updates, [dept_update_filter, dept_status_filter], dept_updates_output)
        admin_track_btn.click(ui.admin_track_grievance, admin_track_id, admin_track_output)
    
    return demo


if __name__ == "__main__":
    print("🚀 Starting Complete Grievance System...")
    print("   Roles: Citizen | Admin | Addresser")
    print("   Features: Submit, Track, Dashboard, Feedback, Assignment, Updates")
    print(f"   API: {API_BASE_URL}")
    demo = create_complete_ui()
    demo.launch(server_name="0.0.0.0", server_port=7863, share=False, show_error=True)