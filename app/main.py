"""
FastAPI Main Application Entry Point - ENHANCED
Added: Addresser router
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.models.database import db
from app.api.routes import grievance, health, auth, admin, citizen, addresser  # NEW: Added addresser
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Grievance Redressal System...")
    await db.connect_db()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await db.close_db()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI-Powered Grievance Redressal System",
    description="Backend API for intelligent grievance management with role-based access (Citizen, Admin, Addresser)",
    version="2.0.0",  # NEW: Version bump
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with CORRECT prefixes
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(citizen.router, prefix="/api/v1", tags=["Citizen"])
app.include_router(addresser.router, prefix="/api/v1/addresser", tags=["Addresser"])  # NEW
app.include_router(grievance.router, prefix="/api/v1", tags=["Grievance"])


@app.get("/")
async def root():
    """Root endpoint - ENHANCED"""
    return {
        "message": "AI-Powered Grievance Redressal System API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "features": {
            "authentication": True,
            "role_based_access": True,
            "admin_panel": True,
            "citizen_portal": True,
            "addresser_portal": True,  # NEW
            "document_understanding": True,  # NEW
            "assignment_management": True,  # NEW
            "department_updates": True  # NEW
        },
        "roles": {
            "citizen": "Submit and track grievances",
            "admin": "Manage all grievances, assign to departments",
            "addresser": "Handle department-specific grievances, submit updates"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )