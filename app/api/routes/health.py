"""Health check endpoint"""
from fastapi import APIRouter, status
from app.models.schemas import HealthResponse
from app.config import settings
from app.models.database import db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API and its dependencies are healthy"
)
async def health_check():
    """
    Health check endpoint
    
    Returns service status and configuration
    """
    # Check database connection
    db_connected = False
    try:
        await db.client.admin.command('ping')
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version="0.1.0",
        llm_provider=settings.LLM_PROVIDER,
        database_connected=db_connected
    )