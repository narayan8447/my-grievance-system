"""
Pydantic schemas for request/response models - ENHANCED
Added: Explainability, Document analysis models, Assignment models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class GrievanceStatus(str, Enum):
    """Grievance status enum"""
    OPEN = "Open"
    IN_REVIEW = "In Review"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"


class Priority(str, Enum):
    """Priority levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Language(str, Enum):
    """Supported languages"""
    TELUGU = "telugu"
    ENGLISH = "english"


# ===== NEW: Explainability Model =====

class Explainability(BaseModel):
    """Explainability for LLM classification decisions"""
    category_reason: str = Field("", description="Why this category was chosen")
    department_reason: str = Field("", description="Why this department was assigned")
    priority_reason: str = Field("", description="Why this priority level was set")


# ===== Document Analysis Models =====

class DocumentEntities(BaseModel):
    """Extracted entities from document"""
    dates: List[str] = Field(default_factory=list, description="Extracted dates")
    amounts: List[str] = Field(default_factory=list, description="Monetary amounts")
    locations: List[str] = Field(default_factory=list, description="Places, addresses")
    people: List[str] = Field(default_factory=list, description="Names of people")
    organizations: List[str] = Field(default_factory=list, description="Departments, companies")


class DocumentAnalysisResult(BaseModel):
    """Result of document understanding analysis"""
    success: bool
    extracted_text: str = Field("", description="Full text extracted from document")
    key_entities: DocumentEntities = Field(default_factory=DocumentEntities)
    document_type: str = Field("other", description="Type: complaint_letter, application, etc.")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in analysis")
    error: Optional[str] = None


# ===== Assignment Models =====

class AssignmentHistory(BaseModel):
    """History entry for assignment changes"""
    from_dept: str
    to_dept: str
    changed_by: str
    changed_by_name: str
    reason: str
    timestamp: datetime


class Assignment(BaseModel):
    """Grievance assignment information"""
    assigned_by: str = Field(..., description="Admin user ID who assigned")
    assigned_by_name: str = Field(..., description="Admin name")
    assigned_to_department: str = Field(..., description="Department name")
    assigned_to_addresser: Optional[str] = Field(None, description="Specific addresser ID")
    assignment_type: str = Field(..., description="manual or auto")
    assigned_at: datetime
    assignment_history: List[AssignmentHistory] = Field(default_factory=list)


# ===== Addresser Update Models =====

class AddresserUpdateRecord(BaseModel):
    """Single update record from addresser"""
    addresser_id: str
    addresser_name: str
    department: str
    status_update: Optional[str] = None
    work_done: str
    remarks: str
    visibility: str = "admin_only"  # admin_only or public
    timestamp: datetime
    attachments: List[str] = Field(default_factory=list)


# ===== Core Models =====

class GrievanceInput(BaseModel):
    """Input model for grievance submission"""
    text: str = Field(..., description="Grievance text in Telugu or English")
    language: Optional[Language] = Field(Language.ENGLISH, description="Language of grievance")
    user_name: Optional[str] = Field(None, description="Name of the person submitting")
    user_contact: Optional[str] = Field(None, description="Contact number or email")
    location: Optional[str] = Field(None, description="Location/District")

class AudioTranscription(BaseModel):
    """Audio transcription result"""
    success: bool
    text: Optional[str] = None
    language: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None


class ImageOCR(BaseModel):
    """Image OCR result"""
    success: bool
    text: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None



class LLMAnalysis(BaseModel):
    """LLM analysis output - ENHANCED with explainability"""
    summary: str = Field(..., description="Brief summary of the grievance")
    category: str = Field(..., description="Classified category")
    department: str = Field(..., description="Suggested department")
    priority: Priority = Field(..., description="Urgency level")
    keywords: List[str] = Field(default_factory=list, description="Key topics")
    language_detected: Language = Field(..., description="Detected language")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in classification")
    explanation: Optional[Explainability] = Field(None, description="Why these classifications were made")


class RedressalSuggestion(BaseModel):
    """Redressal action suggestions"""
    recommended_actions: List[str] = Field(..., description="Step-by-step actions")
    escalation_needed: bool = Field(False, description="Whether escalation is required")
    estimated_resolution_time: str = Field(..., description="Expected time to resolve")
    similar_cases: List[str] = Field(default_factory=list, description="Similar past grievance IDs")
    explanation: str = Field(..., description="Why these actions are suggested")


class Grievance(BaseModel):
    """Complete grievance model - ENHANCED"""
    grievance_id: str = Field(..., description="Unique identifier")
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_contact: Optional[str] = None
    location: Optional[str] = None
    
    # Original input
    grievance_text: str
    language: Language

    # Analysis
    audio_transcription: Optional[AudioTranscription] = None
    image_ocr: Optional[ImageOCR] = None
    document_analysis: Optional[DocumentAnalysisResult] = None
    
    # LLM Analysis - ENHANCED
    summary: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[Priority] = None
    keywords: List[str] = Field(default_factory=list)
    explanation: Optional[Explainability] = None  # NEW
    
    
    
    # Redressal - ENHANCED
    recommended_actions: List[str] = Field(default_factory=list)
    escalation_needed: bool = False
    similar_cases: List[str] = Field(default_factory=list)  # NEW
    
    # Assignment
    assignment: Optional[Assignment] = None
    
    # Status tracking
    status: GrievanceStatus = GrievanceStatus.OPEN
    assigned_officer: Optional[str] = None
    
    # Admin updates
    admin_updates: Optional[Dict[str, Any]] = None
    
    # Addresser updates
    addresser_updates: List[AddresserUpdateRecord] = Field(default_factory=list)
    
    # Citizen feedback
    citizen_feedback: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    # Audit
    processing_logs: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class GrievanceResponse(BaseModel):
    """API response for grievance"""
    success: bool
    grievance_id: str
    message: str
    data: Optional[Grievance] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    llm_provider: str
    database_connected: bool


# ===== Analysis Request Models =====

class DocumentAnalysisRequest(BaseModel):
    """Request for document analysis"""
    grievance_text: Optional[str] = Field(None, description="Context text from grievance")
    file_type: str = Field(..., description="File extension: pdf, jpg, docx, etc.")


class EnhancedGrievanceAnalysisRequest(BaseModel):
    """Request for grievance analysis with document"""
    grievance_text: str
    language: Language = Language.ENGLISH
    document_analysis: Optional[DocumentAnalysisResult] = None