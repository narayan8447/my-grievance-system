"""Summary service for generating grievance summaries"""
import logging
from typing import Dict, List
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating summaries of grievances"""
    
    def __init__(self):
        self.max_summary_length = 200  # characters
    
    async def generate_summary(
        self,
        grievance_text: str,
        language: str = "english"
    ) -> Dict:
        """
        Generate a concise summary of the grievance
        
        Args:
            grievance_text: The full grievance text
            language: Language of the text (telugu/english)
            
        Returns:
            Dictionary with summary and metadata
        """
        try:
            logger.info("Generating summary for grievance")
            
            # Prepare prompt
            system_prompt = self._get_summary_prompt(language)
            user_prompt = f"""Summarize this grievance:

{grievance_text}

Provide response in JSON format:
{{
    "summary": "concise summary in English",
    "key_points": ["point 1", "point 2", "point 3"],
    "entities": {{
        "locations": ["location1", "location2"],
        "people": ["person1"],
        "issues": ["issue1", "issue2"]
    }}
}}"""
            
            # Call LLM
            response = await llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower temperature for factual summary
            )
            
            # Parse response
            import json
            summary_data = self._parse_json_response(response)
            
            # Validate summary length
            if len(summary_data.get("summary", "")) > self.max_summary_length:
                summary_data["summary"] = summary_data["summary"][:self.max_summary_length] + "..."
            
            logger.info("Summary generated successfully")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._fallback_summary(grievance_text)
    
    def _get_summary_prompt(self, language: str) -> str:
        """Generate system prompt for summarization"""
        language_instruction = ""
        if language == "telugu":
            language_instruction = """
Note: The input is in Telugu. Translate and summarize in English while preserving all important details.
"""
        
        return f"""You are an expert at summarizing citizen grievances for government officials.

Your task:
1. Create a concise, factual summary (max 200 characters)
2. Extract key points (main issues mentioned)
3. Identify entities (locations, people, specific issues)
4. Maintain objectivity and facts only
5. Use clear, professional language

{language_instruction}

Guidelines:
- Focus on the core issue/complaint
- Include relevant details (what, where, when if mentioned)
- Omit emotional language, keep it factual
- If multiple issues, list them separately
- Always respond in English
"""
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        import json
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise
    
    def _fallback_summary(self, grievance_text: str) -> Dict:
        """
        Generate basic summary using simple text processing
        
        Args:
            grievance_text: The grievance text
            
        Returns:
            Basic summary dictionary
        """
        # Simple truncation-based summary
        summary = grievance_text[:self.max_summary_length]
        if len(grievance_text) > self.max_summary_length:
            summary += "..."
        
        # Extract basic entities using simple rules
        words = grievance_text.split()
        
        return {
            "summary": summary,
            "key_points": [grievance_text[:100]],  # First sentence as key point
            "entities": {
                "locations": [],
                "people": [],
                "issues": ["General complaint"]
            }
        }
    
    async def extract_keywords(
        self,
        grievance_text: str,
        max_keywords: int = 10
    ) -> List[str]:
        """
        Extract important keywords from grievance
        
        Args:
            grievance_text: The grievance text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        try:
            logger.info("Extracting keywords")
            
            system_prompt = """You are an expert at extracting key terms from text.
Extract the most important keywords and phrases that describe the main issues.
Return only a JSON array of keywords, e.g., ["keyword1", "keyword2", "keyword3"]"""
            
            user_prompt = f"""Extract up to {max_keywords} important keywords from this text:

{grievance_text}

Return as JSON array only."""
            
            response = await llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            
            # Parse JSON array
            import json
            keywords = self._parse_keywords(response)
            
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return self._fallback_keywords(grievance_text, max_keywords)
    
    def _parse_keywords(self, response: str) -> List[str]:
        """Parse keywords from LLM response"""
        import json
        
        try:
            # Try to find array in response
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: split by comma
            keywords = [k.strip().strip('"\'') for k in response.split(',')]
            return [k for k in keywords if k]
    
    def _fallback_keywords(self, text: str, max_keywords: int) -> List[str]:
        """
        Extract keywords using simple frequency analysis
        
        Args:
            text: Input text
            max_keywords: Max number of keywords
            
        Returns:
            List of keywords
        """
        # Common stop words to ignore
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'as', 'by', 'this', 'that',
            'అని', 'ఇది', 'ఆ', 'ఈ', 'మరియు', 'లేదా'
        }
        
        # Tokenize and count
        words = text.lower().split()
        word_freq = {}
        
        for word in words:
            # Clean word
            word = word.strip('.,!?;:"\'()[]{}')
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Return top keywords
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def generate_quick_summary(self, grievance_text: str) -> str:
        """
        Generate a quick one-line summary (synchronous, no LLM)
        
        Args:
            grievance_text: The grievance text
            
        Returns:
            Quick summary string
        """
        # Get first sentence or first 150 chars
        sentences = grievance_text.split('.')
        if sentences:
            summary = sentences[0].strip()
            if len(summary) > 150:
                summary = summary[:150] + "..."
            return summary
        
        return grievance_text[:150] + ("..." if len(grievance_text) > 150 else "")


# Singleton instance
summary_service = SummaryService()