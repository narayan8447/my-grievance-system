"""Configuration settings for the application"""
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # MongoDB
    MONGODB_URL: str  # Required, no default fallback
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
    SECRET_KEY: str  # Required, no default fallback
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    
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
        "Transport",
        "Social Welfare",
        "Housing",
        "Public Distribution System (PDS)",
        "General Administration"
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

    @model_validator(mode="after")
    def validate_conditional_keys(self) -> "Settings":
        """Ensure conditional credentials exist depending on selected LLM provider"""
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY.strip():
            raise ValueError("GROQ_API_KEY must be configured when LLM_PROVIDER is set to 'groq'")
        if self.LLM_PROVIDER == "huggingface" and not self.HUGGINGFACE_API_KEY.strip():
            raise ValueError("HUGGINGFACE_API_KEY must be configured when LLM_PROVIDER is set to 'huggingface'")
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()