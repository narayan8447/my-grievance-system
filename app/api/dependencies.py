"""
API dependencies for authentication and authorization - ENHANCED
Added: require_addresser dependency
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.models.user import User
from app.models.database import db
from app.services.auth_service import get_auth_service
from app.utils.security import decode_access_token

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    try:
        # Decode token
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user from database
        user = await get_auth_service().get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    """
    Require admin role
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def require_citizen(
    user: User = Depends(get_current_user)
) -> User:
    """
    Require citizen role
    """
    if user.role != "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Citizen access required"
        )
    return user


async def require_addresser(
    user: User = Depends(get_current_user)
) -> User:
    """
    NEW: Require addresser role
    Addresser must have a department assigned
    """
    if user.role != "addresser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Addresser access required"
        )
    
    # Verify addresser has department
    if not user.department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Addresser must have a department assigned"
        )
    
    logger.info(f"Addresser access granted: {user.email} (Department: {user.department})")
    return user


async def verify_grievance_ownership(
    grievance_id: str,
    user: User
) -> dict:
    """
    Verify that the grievance belongs to the user
    """
    collection = db.get_collection("grievances")
    
    grievance = await collection.find_one({"grievance_id": grievance_id})
    
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found"
        )
    
    # Check ownership (match email or phone)
    user_contact = grievance.get("user_contact", "")
    
    if user.email != user_contact and user.phone != user_contact:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own grievances"
        )
    
    return grievance


async def verify_grievance_exists(grievance_id: str) -> dict:
    """
    Verify that a grievance exists (for public endpoints)
    """
    collection = db.get_collection("grievances")
    
    grievance = await collection.find_one({"grievance_id": grievance_id})
    
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found"
        )
    
    return grievance


async def verify_department_access(
    grievance_id: str,
    user: User
) -> dict:
    """
    NEW: Verify that addresser has access to grievance in their department
    """
    if user.role != "addresser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only addressers can use department-scoped access"
        )
    
    collection = db.get_collection("grievances")
    
    grievance = await collection.find_one({
        "grievance_id": grievance_id,
        "assignment.assigned_to_department": user.department
    })
    
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance not found or not in your department ({user.department})"
        )
    
    return grievance