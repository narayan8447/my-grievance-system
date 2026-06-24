"""LLM chain for grievance understanding and classification"""
import json
import logging
from typing import Dict, Any
from app.config import settings
from app.chains.prompts import (
    UNDERSTANDING_SYSTEM_PROMPT,
    UNDERSTANDING_USER_PROMPT
)

logger = logging.getLogger(__name__)


class UnderstandingChain:
    """Chain for analyzing and classifying grievances"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    async def analyze(self, grievance_text: str) -> Dict[str, Any]:
        """
        Analyze grievance and extract structured information
        
        Args:
            grievance_text: The grievance text in Telugu or English
            
        Returns:
            Dictionary with analysis results including explanation
        """
        try:
            # Prepare prompts
            system_prompt = UNDERSTANDING_SYSTEM_PROMPT.format(
                departments=", ".join(settings.DEPARTMENTS),
                categories=", ".join(settings.GRIEVANCE_CATEGORIES)
            )
            
            user_prompt = UNDERSTANDING_USER_PROMPT.format(
                grievance_text=grievance_text
            )
            
            # Call LLM with timeout (handled by service layer)
            response = await self.llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower temperature for consistent classification
            )
            
            # Parse JSON response
            analysis = self._parse_response(response)
            
            logger.info(f"Successfully analyzed grievance: {analysis.get('category')}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in understanding chain: {e}")
            # Return fallback response
            return self._get_fallback_analysis(grievance_text)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON"""
        try:
            # Try to find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # If no JSON found, try parsing entire response
                return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError("LLM did not return valid JSON")
    
    def _get_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Provide fallback analysis if LLM fails"""
        return {
            "summary": text[:200] + "..." if len(text) > 200 else text,
            "category": "Others",
            "department": "General Administration",
            "priority": "Medium",
            "keywords": [],
            "language_detected": "english",
            "confidence_score": 0.3,
            "explanation": {
                "category_reason": "Fallback classification due to processing error. Defaulted to 'Others' category.",
                "department_reason": "Assigned to General Administration as a safe default for manual review.",
                "priority_reason": "Medium priority assigned as default until manual assessment."
            }
        }