"""LLM service for interacting with different LLM providers - ENHANCED"""
import logging
import asyncio
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM operations supporting multiple providers"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "groq":
            self._init_groq()
        elif self.provider == "huggingface":
            self._init_huggingface()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _init_ollama(self):
        """Initialize Ollama client (Free, Local)"""
        try:
            from langchain_community.llms import Ollama
            self.client = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL
            )
            logger.info(f"Initialized Ollama with model: {settings.OLLAMA_MODEL}")
        except ImportError:
            logger.error("langchain-community not installed. Run: pip install langchain-community")
            raise
    
    def _init_groq(self):
        """Initialize Groq client (Free API)"""
        try:
            from langchain_groq import ChatGroq
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not set in environment")
            
            self.client = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
                temperature=0.7
            )
            logger.info(f"Initialized Groq with model: {settings.GROQ_MODEL}")
        except ImportError:
            logger.error("Install groq: pip install langchain-groq")
            raise
    
    def _init_huggingface(self):
        """Initialize Hugging Face client (Free)"""
        try:
            from langchain_community.llms import HuggingFaceHub
            if not settings.HUGGINGFACE_API_KEY:
                raise ValueError("HUGGINGFACE_API_KEY not set")
            
            self.client = HuggingFaceHub(
                huggingfacehub_api_token=settings.HUGGINGFACE_API_KEY,
                repo_id="mistralai/Mistral-7B-Instruct-v0.2"
            )
            logger.info("Initialized Hugging Face")
        except ImportError:
            logger.error("Install: pip install huggingface_hub")
            raise
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30
    ) -> str:
        """
        Generate response from LLM with timeout protection
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Timeout in seconds (default 30s)
            
        Returns:
            LLM response text
            
        Raises:
            asyncio.TimeoutError: If request exceeds timeout
            ValueError: If LLM request fails
        """
        try:
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate based on provider with timeout
            if self.provider == "ollama":
                response = await asyncio.wait_for(
                    self._generate_ollama(full_prompt, temperature),
                    timeout=timeout
                )
            elif self.provider == "groq":
                response = await asyncio.wait_for(
                    self._generate_groq(system_prompt, user_prompt, temperature),
                    timeout=timeout
                )
            else:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.client, full_prompt),
                    timeout=timeout
                )
            
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"LLM request timed out after {timeout}s")
            raise ValueError(f"LLM request timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_retries: int = 3,
        timeout: int = 30
    ) -> str:
        """
        Generate with automatic retry on failure using exponential backoff
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_retries: Maximum number of retry attempts
            timeout: Timeout per attempt in seconds
            
        Returns:
            LLM response text
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(max_retries):
            try:
                return await self.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} retry attempts failed")
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        raise Exception("Should not reach here")
    
    async def _generate_ollama(self, prompt: str, temperature: float) -> str:
        """Generate using Ollama"""
        try:
            response = self.client.invoke(
                prompt,
                temperature=temperature
            )
            return response
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def _generate_groq(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float
    ) -> str:
        """Generate using Groq"""
        from langchain.schema import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.client.invoke(messages, temperature=temperature)
        return response.content


# Singleton instance
llm_service = LLMService()