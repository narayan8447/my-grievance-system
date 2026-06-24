"""Classification service for grievances"""
import logging
from typing import Dict, List, Optional
from app.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for classifying grievances into categories and departments"""
    
    def __init__(self):
        self.categories = settings.GRIEVANCE_CATEGORIES
        self.departments = settings.DEPARTMENTS
        
        # Category to Department mapping (default suggestions)
        self.category_department_mapping = {
            "Infrastructure": ["Roads and Buildings", "Municipal"],
            "Public Services": ["Water Supply", "Electricity", "Municipal"],
            "Corruption": ["Police", "Revenue"],
            "Land Issues": ["Revenue"],
            "Pension": ["Social Welfare"],
            "Welfare Schemes": ["Social Welfare"],
            "Law and Order": ["Police"],
            "Environmental": ["Municipal", "Agriculture"],
            "Healthcare": ["Health"],
            "Education": ["Education"],
            "Others": ["Municipal"]
        }
    
    async def classify_grievance(
        self,
        grievance_text: str,
        language: str = "english"
    ) -> Dict:
        """
        Classify grievance into category and suggest department
        
        Args:
            grievance_text: The grievance text
            language: Language of the text
            
        Returns:
            Dictionary with classification results
        """
        try:
            logger.info("Classifying grievance")
            
            # Prepare classification prompt
            system_prompt = self._get_classification_prompt()
            user_prompt = f"""Classify this grievance:

Text: {grievance_text}
Language: {language}

Provide classification in JSON format:
{{
    "category": "category name",
    "department": "department name",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}"""
            
            # Call LLM
            response = await llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2  # Low temperature for consistent classification
            )
            
            # Parse response
            import json
            classification = self._parse_json_response(response)
            
            # Validate and fallback
            if not self._validate_classification(classification):
                logger.warning("Invalid classification, using rule-based fallback")
                classification = self._rule_based_classification(grievance_text)
            
            logger.info(f"Classification: {classification['category']} -> {classification['department']}")
            return classification
            
        except Exception as e:
            logger.error(f"Error in classification: {e}")
            return self._rule_based_classification(grievance_text)
    
    def _get_classification_prompt(self) -> str:
        """Generate classification system prompt"""
        return f"""You are an expert at classifying citizen grievances for the Andhra Pradesh government.

Available Categories:
{', '.join(self.categories)}

Available Departments:
{', '.join(self.departments)}

Rules:
1. Choose the MOST SPECIFIC category that fits the grievance
2. Suggest the department best equipped to handle this issue
3. Provide confidence score (0.0 to 1.0)
4. Give brief reasoning

Examples:
- "రోడ్డు చెడిపోయింది" → Infrastructure, Roads and Buildings
- "Water not coming" → Public Services, Water Supply
- "Pension not received" → Pension, Social Welfare
- "Illegal construction" → Infrastructure, Municipal
- "Teacher absent" → Education, Education
"""
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        import json
        
        try:
            # Try to find JSON in response
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
    
    def _validate_classification(self, classification: Dict) -> bool:
        """Validate classification result"""
        if not classification:
            return False
        
        # Check required fields
        if "category" not in classification or "department" not in classification:
            return False
        
        # Check if category is valid
        if classification["category"] not in self.categories:
            logger.warning(f"Invalid category: {classification['category']}")
            return False
        
        # Check if department is valid
        if classification["department"] not in self.departments:
            logger.warning(f"Invalid department: {classification['department']}")
            return False
        
        return True
    
    def _rule_based_classification(self, grievance_text: str) -> Dict:
        """
        Fallback rule-based classification using keywords
        
        Args:
            grievance_text: The grievance text
            
        Returns:
            Classification dictionary
        """
        text_lower = grievance_text.lower()
        
        # Keyword-based rules
        rules = {
            "Infrastructure": ["road", "రోడ్డు", "bridge", "building", "construction", "drain"],
            "Public Services": ["water", "నీరు", "electricity", "విద్యుత్", "power cut", "supply"],
            "Corruption": ["bribe", "లంచం", "corrupt", "money", "illegal"],
            "Land Issues": ["land", "భూమి", "property", "dispute", "encroachment"],
            "Pension": ["pension", "పెన్షన్", "old age", "widow"],
            "Welfare Schemes": ["ration", "రేషన్", "scheme", "योजना", "subsidy"],
            "Law and Order": ["police", "పోలీస్", "theft", "crime", "safety"],
            "Environmental": ["garbage", "చెత్త", "pollution", "tree", "environment"],
            "Healthcare": ["hospital", "ఆసుపత్రి", "doctor", "డాక్టర్", "medicine", "health"],
            "Education": ["school", "పాఠశాల", "teacher", "teacher", "student", "education"]
        }
        
        # Find matching category
        category = "Others"
        max_matches = 0
        
        for cat, keywords in rules.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > max_matches:
                max_matches = matches
                category = cat
        
        # Get suggested department
        departments = self.category_department_mapping.get(category, ["Municipal"])
        department = departments[0]
        
        return {
            "category": category,
            "department": department,
            "confidence": 0.6 if max_matches > 0 else 0.3,
            "reasoning": "Rule-based classification using keyword matching"
        }
    
    def get_related_departments(self, category: str) -> List[str]:
        """
        Get departments that typically handle a category
        
        Args:
            category: Grievance category
            
        Returns:
            List of department names
        """
        return self.category_department_mapping.get(category, ["Municipal"])
    
    def suggest_priority(
        self,
        category: str,
        keywords: List[str]
    ) -> str:
        """
        Suggest priority level based on category and keywords
        
        Args:
            category: Grievance category
            keywords: Keywords extracted from grievance
            
        Returns:
            Priority level (Low, Medium, High, Critical)
        """
        # Critical keywords
        critical_keywords = [
            "emergency", "urgent", "death", "life", "danger", "critical",
            "అత్యవసరం", "ప్రమాదం", "మరణం"
        ]
        
        # High priority keywords
        high_keywords = [
            "severe", "serious", "immediate", "major", "broken",
            "తీవ్రమైన", "పెద్ద"
        ]
        
        # Check keywords
        keywords_lower = [k.lower() for k in keywords]
        
        if any(kw in " ".join(keywords_lower) for kw in critical_keywords):
            return "Critical"
        
        if any(kw in " ".join(keywords_lower) for kw in high_keywords):
            return "High"
        
        # Category-based priority
        high_priority_categories = ["Healthcare", "Law and Order", "Public Services"]
        if category in high_priority_categories:
            return "High"
        
        return "Medium"


# Singleton instance
classification_service = ClassificationService()