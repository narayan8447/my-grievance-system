"""
Authentication service for user management - ENHANCED
Added: Department validation for addresser role
"""
import logging
from datetime import datetime
from typing import Optional
import uuid

from app.models.user import User, UserRegister, UserLogin, UserRole
from app.models.database import db
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    validate_email,
    validate_phone
)
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service - ENHANCED"""
    
    async def register_user(self, user_data: UserRegister) -> User:
        """
        Register a new user
        ENHANCED: Validates department for addresser role
        """
        collection = db.get_collection("users")
        
        # Check if email already exists
        existing = await collection.find_one({"email": user_data.email})
        if existing:
            raise ValueError("Email already registered")
        
        # Check if phone already exists (if provided)
        if user_data.phone:
            existing_phone = await collection.find_one({"phone": user_data.phone})
            if existing_phone:
                raise ValueError("Phone number already registered")
        
        # Validate email
        if not validate_email(user_data.email):
            raise ValueError("Invalid email format")
        
        # Validate phone if provided
        if user_data.phone and not validate_phone(user_data.phone):
            raise ValueError("Invalid phone number format")
        
        # NEW: Validate department for addresser role
        if user_data.role == UserRole.ADDRESSER:
            if not user_data.department:
                raise ValueError("Department is required for addresser role")
            
            # Validate department exists in system
            if not await self._validate_department(user_data.department):
                raise ValueError(f"Invalid department: {user_data.department}")
        
        # NEW: Ensure non-addressers don't have department
        if user_data.role != UserRole.ADDRESSER and user_data.department:
            raise ValueError("Department can only be set for addresser role")
        
        # Hash password (validation happens inside get_password_hash)
        try:
            password_hash = get_password_hash(user_data.password)
        except ValueError as e:
            raise ValueError(f"Password validation failed: {str(e)}")
        
        # Create user
        user = User(
            user_id=f"USR-{user_data.role.value[:3].upper()}-{uuid.uuid4().hex[:8].upper()}",
            email=user_data.email,
            phone=user_data.phone,
            password_hash=password_hash,
            full_name=user_data.full_name,
            role=user_data.role.value,
            department=user_data.department,  # NEW
            location=user_data.location,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=None,
            grievances_submitted=[]
        )
        
        # Insert into database
        await collection.insert_one(user.model_dump())
        
        logger.info(f"User registered: {user.email} (Role: {user.role}, Dept: {user.department})")
        
        return user
    
    async def _validate_department(self, department_name: str) -> bool:
        """
        NEW: Validate that department exists in system
        
        Args:
            department_name: Name of department to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check against configured departments
            if department_name in settings.DEPARTMENTS:
                return True
            
            # Optionally: Check departments collection if you created one
            # dept_collection = db.get_collection("departments")
            # dept = await dept_collection.find_one({"name": department_name, "is_active": True})
            # return dept is not None
            
            return False
            
        except Exception as e:
            logger.error(f"Department validation error: {e}")
            return False
    
    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """
        Authenticate user with email/phone and password
        """
        collection = db.get_collection("users")
        
        # Find user by email or phone
        query = {
            "$or": [
                {"email": login_data.email_or_phone},
                {"phone": login_data.email_or_phone}
            ]
        }
        
        user_dict = await collection.find_one(query)
        
        if not user_dict:
            logger.warning(f"Login attempt for non-existent user: {login_data.email_or_phone}")
            return None
        
        # Verify password
        if not verify_password(login_data.password, user_dict["password_hash"]):
            logger.warning(f"Invalid password for user: {login_data.email_or_phone}")
            return None
        
        # Update last login
        await collection.update_one(
            {"user_id": user_dict["user_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create User object
        user = User(**user_dict)
        
        logger.info(f"User logged in: {user.email} (Role: {user.role}, Dept: {user.department})")
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        collection = db.get_collection("users")
        user_dict = await collection.find_one({"user_id": user_id})
        
        if user_dict:
            return User(**user_dict)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        collection = db.get_collection("users")
        user_dict = await collection.find_one({"email": email})
        
        if user_dict:
            return User(**user_dict)
        return None
    
    def create_token_for_user(self, user: User) -> str:
        """
        Create JWT token for user
        ENHANCED: Include department in token claims
        """
        token_data = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role,
            "department": user.department  # NEW: Include department in JWT
        }
        return create_access_token(token_data)
    
    async def get_addressers_by_department(self, department: str) -> list:
        """
        NEW: Get all addressers for a specific department
        Useful for assignment notifications
        """
        try:
            collection = db.get_collection("users")
            
            addressers = await collection.find({
                "role": "addresser",
                "department": department,
                "is_active": True
            }).to_list(length=100)
            
            return [User(**addr) for addr in addressers]
            
        except Exception as e:
            logger.error(f"Error fetching addressers: {e}")
            return []
    
    async def get_all_departments(self) -> list:
        """
        NEW: Get list of all departments with addressers
        """
        try:
            collection = db.get_collection("users")
            
            # Get unique departments from addressers
            departments = await collection.distinct("department", {
                "role": "addresser",
                "is_active": True
            })
            
            return sorted([d for d in departments if d])
            
        except Exception as e:
            logger.error(f"Error fetching departments: {e}")
            return settings.DEPARTMENTS


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get auth service singleton"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service