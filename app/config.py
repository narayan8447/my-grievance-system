"""Configuration settings for the application"""
from pydantic_settings import BaseSettings
from pydantic import model_validator, Field, AliasChoices
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""
    
    ENVIRONMENT: str = "production"
    
    # MongoDB
    MONGODB_URL: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("MONGO_URL", "MONGO_PUBLIC_URL", "MONGODB_URL")
    )
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
    def validate_environment(self) -> "Settings":
        """Validate LLM credentials and MongoDB connection strings based on environment"""
        # MongoDB Validation
        if not self.MONGODB_URL:
            if self.ENVIRONMENT == "development":
                self.MONGODB_URL = "mongodb://localhost:27017"
            else:
                raise ValueError("MONGODB_URL (or MONGO_URL) is required in production environment.")
        elif self.ENVIRONMENT == "production" and "localhost" in self.MONGODB_URL:
            raise ValueError(
                "Cannot use localhost MongoDB in production environment. "
                "Please configure a valid external MONGODB_URL (or MONGO_URL)."
            )

        # LLM Validation
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY.strip():
            raise ValueError("GROQ_API_KEY must be configured when LLM_PROVIDER is set to 'groq'")
        if self.LLM_PROVIDER == "huggingface" and not self.HUGGINGFACE_API_KEY.strip():
            raise ValueError("HUGGINGFACE_API_KEY must be configured when LLM_PROVIDER is set to 'huggingface'")
        
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()