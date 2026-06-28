import os
import pytest
import requests
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set test environment settings BEFORE any imports
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["DATABASE_NAME"] = "test_grievance_db"
os.environ["SECRET_KEY"] = "super-secret-test-key-at-least-32-characters-long"
os.environ["LLM_PROVIDER"] = "ollama"

from app.config import settings
settings.MONGODB_URL = "mongodb://localhost:27017"
settings.DATABASE_NAME = "test_grievance_db"
settings.SECRET_KEY = "super-secret-test-key-at-least-32-characters-long"
settings.LLM_PROVIDER = "ollama"

from app.main import app
from app.models.database import db
from app.services.llm_service import llm_service
from app.services.image_service import image_service
from app.services.audio_service import audio_service
from app.services.document_service import document_service
from app.services.rag_service import rag_service
from gradio_app import CompleteGrievanceUI, create_complete_ui


# =========================================================
# Mock AI Response Content
# =========================================================
MOCK_UNDERSTANDING_JSON = """
{
    "summary": "The citizen is reporting a severe road cave-in and potholes on Main Street.",
    "category": "Infrastructure",
    "department": "Roads and Buildings",
    "priority": "High",
    "keywords": ["road", "cave-in", "potholes", "Main Street"],
    "confidence_score": 0.95,
    "explanation": {
        "category_reason": "Involves physical public infrastructure damage.",
        "department_reason": "Roads and Buildings manages public street maintenance.",
        "priority_reason": "Severe cave-ins present immediate traffic safety risks."
    }
}
"""

MOCK_REDRESSAL_JSON = """
{
    "recommended_actions": [
        "Deploy field inspection team to verify cave-in size",
        "Set up safety barriers and warning signs",
        "Initiate emergency repaving schedule"
    ],
    "escalation_needed": false,
    "estimated_resolution_time": "5 working days",
    "explanation": "Standard safety protocol for physical road damage."
}
"""


# =========================================================
# Pytest Fixtures
# =========================================================

@pytest.fixture(scope="module")
def setup_test_db():
    """Ensure clean test database on local MongoDB"""
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    # Clean database before testing
    client.drop_database("test_grievance_db")
    
    yield
    
    # Clean database after testing
    client.drop_database("test_grievance_db")


@pytest.fixture(scope="module")
def client(setup_test_db):
    """FastAPI TestClient handling startup/shutdown lifespan events"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def mock_ai_services():
    """Mock external AI service dependencies to run offline and deterministically"""
    # 1. Mock LLM Service generate
    async def mock_generate(system_prompt, user_prompt, temperature=0.7, max_tokens=2000, timeout=30):
        if "understanding" in system_prompt.lower() or "classify" in system_prompt.lower() or "category" in system_prompt.lower():
            return MOCK_UNDERSTANDING_JSON
        if "redressal" in system_prompt.lower() or "suggest" in system_prompt.lower():
            return MOCK_REDRESSAL_JSON
        return "{}"

    # 2. Mock Image Processing & OCR
    async def mock_process_image(bytes_data):
        return {"success": True, "error": None}
        
    async def mock_extract_text(bytes_data):
        return "EXTRACTED TEXT FROM ROAD COMPLAINT IMAGE"

    # 3. Mock Audio Transcription
    async def mock_transcribe_audio(bytes_data, language="en"):
        return {"success": True, "text": "transcribed audio complaint regarding potholes"}

    # 4. Mock Document Analysis
    async def mock_analyze_document(document_bytes, file_extension, context_text=""):
        return {
            "success": True,
            "document_type": "PDF",
            "extracted_text": "OFFICIAL PETITION DOCUMENT FOR ROAD WORKS",
            "key_entities": {
                "dates": ["2026-06-25"],
                "amounts": ["50,000 INR"],
                "locations": ["Ward 4 Main Street"]
            },
            "confidence": 0.9
        }

    # Apply patches
    with patch.object(llm_service, "generate", side_effect=mock_generate), \
         patch.object(image_service, "process_image", side_effect=mock_process_image), \
         patch.object(image_service, "extract_text_from_image", side_effect=mock_extract_text), \
         patch.object(audio_service, "transcribe_audio", side_effect=mock_transcribe_audio), \
         patch.object(document_service, "analyze_document", side_effect=mock_analyze_document):
        yield


# =========================================================
# End-to-End Integration Tests
# =========================================================

def test_complete_workflow_integration(client):
    # -----------------------------------------------------
    # 1. GRADIO TO TESTCLIENT ADAPTER
    # -----------------------------------------------------
    # CompleteGrievanceUI connects via 'requests' library to http://localhost:8000/api/v1.
    # To run test E2E without starting a real port server, we patch requests methods
    # to redirect calls directly to FastAPI's TestClient.
    
    def mock_requests_post(url, data=None, json=None, files=None, headers=None, timeout=None):
        route = url.replace("http://localhost:8000", "")
        # Format files for TestClient if present
        tc_files = None
        if files:
            tc_files = {}
            for k, f in files.items():
                # requests files can be (name, fileobj) or just fileobj
                fileobj = f[1] if isinstance(f, tuple) else f
                tc_files[k] = (fileobj.name if hasattr(fileobj, 'name') else "file", fileobj, "application/octet-stream")
        
        resp = client.post(route, data=data, json=json, files=tc_files, headers=headers)
        return resp

    def mock_requests_get(url, params=None, headers=None, timeout=None):
        route = url.replace("http://localhost:8000", "")
        resp = client.get(route, params=params, headers=headers)
        return resp

    def mock_requests_put(url, json=None, headers=None, timeout=None):
        route = url.replace("http://localhost:8000", "")
        resp = client.put(route, json=json, headers=headers)
        return resp

    # -----------------------------------------------------
    # 2. RUN INTEGRATED E2E PORTAL OPERATIONS
    # -----------------------------------------------------
    with patch("requests.post", side_effect=mock_requests_post), \
         patch("requests.get", side_effect=mock_requests_get), \
         patch("requests.put", side_effect=mock_requests_put):
        
        ui = CompleteGrievanceUI()
        
        # A. Citizen Portal registration & login
        reg_msg, reg_success, reg_role = ui.register_user(
            email="citizen@test.com",
            phone="+919999999999",
            password="SecurePassword1",
            confirm="SecurePassword1",
            full_name="John Citizen",
            role="Citizen",
            department=None,
            location="Ward 4 Main Street"
        )
        assert reg_success is True
        assert reg_role == "Citizen"
        assert ui.access_token is not None
        
        # Verify login endpoint
        login_msg, login_success, login_role = ui.login_user(
            email_or_phone="citizen@test.com",
            password="SecurePassword1"
        )
        assert login_success is True
        assert login_role == "Citizen"
        
        # B. Register and verify Admin and Addresser Accounts
        admin_ui = CompleteGrievanceUI()
        _, admin_success, _ = admin_ui.register_user(
            email="admin@test.com",
            phone="+918888888888",
            password="SecurePassword1",
            confirm="SecurePassword1",
            full_name="Super Admin",
            role="Admin",
            department=None,
            location=None
        )
        assert admin_success is True
        
        addresser_ui = CompleteGrievanceUI()
        _, addresser_success, _ = addresser_ui.register_user(
            email="officer@test.com",
            phone="+917777777777",
            password="SecurePassword1",
            confirm="SecurePassword1",
            full_name="Officer Roads",
            role="Addresser",
            department="Roads and Buildings",
            location=None
        )
        assert addresser_success is True
        
        # C. Submit Multi-modal Grievance via Traditional Form
        # Prepare dummy files to pass as inputs
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_f, \
             tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as aud_f, \
             tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as doc_f:
             
            img_f.write(b"PNG_MOCK_IMAGE_DATA")
            img_f.flush()
            aud_f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00" + b"\x00" * 1050)  # Mock WAV header and data > 1KB
            aud_f.flush()
            doc_f.write(b"%PDF-1.4 Mock PDF Content")
            doc_f.flush()
            
            img_path = img_f.name
            aud_path = aud_f.name
            doc_path = doc_f.name
            
        try:
            # Submit grievance
            submit_result = ui.citizen_submit_grievance(
                text="The potholes on Main Street are causing traffic safety accidents.",
                language="English",
                location="Main Street, District 4",
                image_file=img_path,
                audio_file=aud_path,
                document_file=doc_path
            )
            
            assert "Grievance Submitted Successfully" in submit_result
            # Extract grievance ID from output markup e.g. **Grievance ID:** `GRV-XXXX`
            import re
            match = re.search(r"GRV-\d+-[0-9A-Z]+", submit_result)
            assert match is not None
            grievance_id = match.group(0)
            
            # D. Track grievance from Citizen view
            track_result = ui.citizen_track_grievance(grievance_id)
            assert grievance_id in track_result
            assert "Infrastructure" in track_result
            assert "Roads and Buildings" in track_result
            assert "High" in track_result
            assert "EXTRACTED TEXT FROM ROAD COMPLAINT IMAGE" in track_result
            assert "OFFICIAL PETITION DOCUMENT FOR ROAD WORKS" in track_result
            assert "transcribed audio" in track_result
            
            # E. Verify role permission separation (Citizen cannot assign)
            assign_fail = ui.admin_assign_grievance(grievance_id, "Revenue", "Reassign test")
            assert "❌" in assign_fail
            
            # F. Admin overrides Assignment to "Revenue"
            assign_success = admin_ui.admin_assign_grievance(
                grievance_id=grievance_id,
                department="Revenue",
                reason="Redirecting road project funding grievance to Revenue."
            )
            assert "successfully" in assign_success or "assigned" in assign_success.lower()
            
            # Verify update reflected in tracking
            track_admin_view = admin_ui.admin_track_grievance(grievance_id)
            assert "Revenue" in track_admin_view
            assert "AI Classification Reasoning" in track_admin_view
            
            # G. Register officer for Revenue department to verify departmental workload
            officer_revenue_ui = CompleteGrievanceUI()
            _, rev_success, _ = officer_revenue_ui.register_user(
                email="officer_rev@test.com",
                phone="+916666666666",
                password="SecurePassword1",
                confirm="SecurePassword1",
                full_name="Revenue Addresser",
                role="Addresser",
                department="Revenue",
                location=None
            )
            assert rev_success is True
            
            # H. Department Addresser submits progress updates
            update_res = officer_revenue_ui.addresser_submit_update(
                grievance_id=grievance_id,
                work_done="Inspected location, verified landowner funding issues.",
                remarks="Assigned surveyor to map boundaries.",
                visibility="Public",
                status_change="In Review"
            )
            assert "Successfully" in update_res
            
            # Resolve ticket
            resolve_res = officer_revenue_ui.addresser_submit_update(
                grievance_id=grievance_id,
                work_done="Resolved land ownership disputes and released funds.",
                remarks="Closed work ticket.",
                visibility="Public",
                status_change="Resolved"
            )
            assert "Successfully" in resolve_res
            
            # I. Citizen submits Feedback
            feedback_res = ui.citizen_submit_feedback(
                grievance_id=grievance_id,
                feedback="Quick resolution on land mapping! Great service.",
                rating=5,
                attachment_file=None
            )
            assert "Thank you" in feedback_res
            
            # Verify feedback logged in admin history
            admin_details = admin_ui.admin_track_grievance(grievance_id)
            assert "Resolved" in admin_details
            
        finally:
            # Cleanup temp files
            for p in [img_path, aud_path, doc_path]:
                if os.path.exists(p):
                    os.unlink(p)


def test_gradio_ui_compilation():
    """Verify that the Gradio blocks app compiles and constructs correctly without exceptions"""
    demo = create_complete_ui()
    assert demo is not None
    assert demo.title == "Grievance Redressal System"
