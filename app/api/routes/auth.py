"""Authentication routes"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.models.user import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    User
)
from app.services.auth_service import get_auth_service
from app.utils.security import decode_access_token

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    
    - **email**: Valid email address
    - **phone**: Optional Indian phone number (+91XXXXXXXXXX)
    - **password**: 8-72 characters, must contain uppercase, lowercase, and digit
    - **full_name**: User's full name
    - **role**: Either 'admin' or 'citizen' (default: citizen)
    - **location**: Optional location
    """
    try:
        # Register user
        user = await get_auth_service().register_user(user_data)
        
        # Create access token
        access_token = get_auth_service().create_token_for_user(user)
        refresh_token = get_auth_service().create_refresh_token_for_user(user)
        
        # Create response
        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            department=user.department,
            location=user.location,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )
        
    except ValueError as e:
        # Validation errors
        logger.warning(f"Registration validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """
    Login with email/phone and password
    
    - **email_or_phone**: Email address or phone number
    - **password**: Your password
    """
    try:
        # Authenticate user
        user = await get_auth_service().authenticate_user(login_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/phone or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support."
            )
        
        # Create access token
        access_token = get_auth_service().create_token_for_user(user)
        refresh_token = get_auth_service().create_refresh_token_for_user(user)
        
        # Create response
        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            department=user.department,
            location=user.location,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(refresh_data: TokenRefresh):
    """
    Refresh access and refresh tokens using a valid refresh token
    """
    try:
        access_token, new_refresh_token, user = await get_auth_service().refresh_user_tokens(
            refresh_data.refresh_token
        )
        
        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            department=user.department,
            location=user.location,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user=user_response
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Token refresh validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current logged-in user info"""
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = await get_auth_service().get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            department=user.department,
            location=user.location,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current active user
    Use this in protected routes
    """
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
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
        logger.error(f"Auth dependency error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def require_admin(
    user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to require admin role"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def require_citizen(
    user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to require citizen role"""
    if user.role != "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Citizen access required"
        )
    return user