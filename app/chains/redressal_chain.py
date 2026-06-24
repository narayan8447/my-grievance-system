"""LLM chain for redressal suggestions"""
import json
import logging
from typing import Dict, Any, List
from app.chains.prompts import (
    REDRESSAL_SYSTEM_PROMPT,
    REDRESSAL_USER_PROMPT
)
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class RedressalChain:
    """Chain for generating redressal suggestions"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    async def suggest_actions(
        self,
        grievance_text: str,
        summary: str,
        category: str,
        department: str,
        priority: str,
        keywords: List[str] = []
    ) -> Dict[str, Any]:
        """
        Generate redressal action suggestions
        
        Args:
            grievance_text: Original grievance text
            summary: LLM-generated summary
            category: Classified category
            department: Assigned department
            priority: Priority level
            keywords: Extracted keywords (for future RAG enhancement)
            
        Returns:
            Dictionary with redressal suggestions and similar cases
        """
        try:
            # Find similar resolved cases
            similar_cases = await rag_service.find_similar_cases(
                category=category,
                department=department,
                keywords=keywords,
                limit=3
            )
            
            # Build context from similar cases
            similar_context = ""
            if similar_cases:
                similar_context = "\n\nSimilar Resolved Cases for Reference:\n"
                for i, case in enumerate(similar_cases, 1):
                    similar_context += f"{i}. ID: {case['grievance_id']}\n"
                    similar_context += f"   Summary: {case['summary']}\n"
                    similar_context += f"   Resolution Time: {case['resolution_time']}\n"
                    if case['resolution_actions']:
                        similar_context += f"   Actions Taken: {', '.join(case['resolution_actions'][:2])}\n"
                similar_context += "\nUse these as reference but provide specific actions for the current grievance.\n"
            
            # Prepare prompts
            user_prompt = REDRESSAL_USER_PROMPT.format(
                summary=summary,
                category=category,
                department=department,
                priority=priority,
                grievance_text=grievance_text,
                similar_cases_context=similar_context
            )
            
            # Call LLM
            response = await self.llm_service.generate(
                system_prompt=REDRESSAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.5  # Slightly higher for creative solutions
            )
            
            # Parse JSON response
            suggestions = self._parse_response(response)
            
            # Add similar case IDs to response
            suggestions["similar_cases"] = [case["grievance_id"] for case in similar_cases]
            
            logger.info(f"Successfully generated redressal suggestions with {len(similar_cases)} similar cases")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in redressal chain: {e}")
            return self._get_fallback_suggestions()
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError("LLM did not return valid JSON")
    
    def _get_fallback_suggestions(self) -> Dict[str, Any]:
        """Provide fallback suggestions if LLM fails"""
        return {
            "recommended_actions": [
                "Verify grievance details with citizen",
                "Assign to relevant officer for field inspection",
                "Update citizen on progress within 48 hours"
            ],
            "escalation_needed": False,
            "estimated_resolution_time": "7-10 working days",
            "explanation": "Standard grievance resolution procedure",
            "similar_cases": []
        }