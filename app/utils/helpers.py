"""Helper utility functions"""
import re
from datetime import datetime
from typing import Optional


def generate_grievance_id() -> str:
    """
    Generate a unique grievance ID
    Format: GRV-YYYYMMDD-XXXXXXXX
    """
    date_str = datetime.now().strftime('%Y%m%d')
    import uuid
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"GRV-{date_str}-{unique_id}"


def sanitize_text(text: str) -> str:
    """
    Sanitize input text
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove potential XSS patterns (basic)
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text


def detect_language(text: str) -> str:
    """
    Simple language detection
    
    Args:
        text: Input text
        
    Returns:
        'telugu' or 'english'
    """
    # Check for Telugu characters (Unicode range)
    telugu_pattern = re.compile(r'[\u0C00-\u0C7F]')
    
    if telugu_pattern.search(text):
        return "telugu"
    return "english"


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format datetime for display
    
    Args:
        dt: Datetime object (defaults to now)
        
    Returns:
        Formatted string
    """
    if dt is None:
        dt = datetime.utcnow()
    
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to max length
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."