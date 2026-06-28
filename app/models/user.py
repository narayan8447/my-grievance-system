"""
User models for authentication - UPDATED with Addresser role
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles - ENHANCED"""
    ADMIN = "admin"
    CITIZEN = "citizen"
    ADDRESSER = "addresser"  # NEW


class UserRegister(BaseModel):
    """User registration model - ENHANCED"""
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=50)
    full_name: str = Field(..., min_length=2)
    role: UserRole = UserRole.CITIZEN
    department: Optional[str] = None  # NEW: Required if role=addresser
    location: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v:
            import re
            cleaned = re.sub(r'[\s\-]', '', v)
            if not re.match(r'^(\+91|91)?[6-9]\d{9}$', cleaned):
                raise ValueError('Invalid phone number format. Use +91XXXXXXXXXX')
        return v
    
    @field_validator('department')
    @classmethod
    def validate_department(cls, v, info):
        """NEW: Validate department requirement for addresser"""
        role = info.data.get('role')
        if role == UserRole.ADDRESSER and not v:
            raise ValueError('Department is required for addresser role')
        if role != UserRole.ADDRESSER and v:
            raise ValueError('Department can only be set for addresser role')
        return v


class UserLogin(BaseModel):
    """User login model"""
    email_or_phone: str
    password: str


class User(BaseModel):
    """User database model - ENHANCED"""
    user_id: str
    email: str
    phone: Optional[str] = None
    password_hash: str
    full_name: str
    role: str  # "admin" | "citizen" | "addresser"
    department: Optional[str] = None  # NEW: Required for addresser
    location: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    grievances_submitted: List[str] = []  # For citizens
    # grievances_handled: List[str] = []  # TODO: For addressers


class UserResponse(BaseModel):
    """User response (without password) - ENHANCED"""
    user_id: str
    email: str
    phone: Optional[str] = None
    full_name: str
    role: str
    department: Optional[str] = None  # NEW
    location: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Token response after login/register"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    """Request schema to refresh expired tokens"""
    refresh_token: str



class UpdateGrievanceStatus(BaseModel):
    """Admin updates grievance status"""
    status: str
    admin_comment: str
    estimated_resolution: Optional[str] = None


# NEW: Addresser-specific models
class AddresserUpdate(BaseModel):
    """Addresser submits work update"""
    status: Optional[str] = None  # Optional status change
    work_done: str = Field(..., min_length=10, description="Description of work completed")
    remarks: str = Field(..., min_length=10, description="Additional remarks or next steps")
    visibility: str = Field("admin_only", description="admin_only or public")
    
    @field_validator('visibility')
    @classmethod
    def validate_visibility(cls, v):
        if v not in ["admin_only", "public"]:
            raise ValueError('Visibility must be admin_only or public')
        return v


class AssignGrievance(BaseModel):
    """Admin assigns/reassigns grievance - NEW"""
    department: Optional[str] = None  # If None, use AI-suggested department
    reason: Optional[str] = Field(None, description="Reason for manual assignment/reassignment")