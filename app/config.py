"""Configuration settings for the application"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # MongoDB
    MONGODB_URL: str = ""
    DATABASE_NAME: str = "grievance_db"
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # ollama, groq, huggingface
    
    # Ollama (Free, Local)
    OLLAMA_BASE_URL: str = ""
    OLLAMA_MODEL: str = "llama2"
    
    # Groq (Free API)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Hugging Face (Free)
    HUGGINGFACE_API_KEY: str = ""

    # JWT / Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Languages
    SUPPORTED_LANGUAGES: List[str] = ["telugu", "english"]
    
    # Departments (Andhra Pradesh specific)
    DEPARTMENTS: List[str] = [
        "Roads and Buildings",
        "Water Supply",
        "Electricity",
        "Revenue",
        "Health",
        "Education",
        "Police",
        "Municipal",
        "Agriculture",
        "Social Welfare"
    ]
    
    # Grievance Categories
    GRIEVANCE_CATEGORIES: List[str] = [
        "Infrastructure",
        "Public Services",
        "Corruption",
        "Land Issues",
        "Pension",
        "Welfare Schemes",
        "Law and Order",
        "Environmental",
        "Healthcare",
        "Education",
        "Others"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()