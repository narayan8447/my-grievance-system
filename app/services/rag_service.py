"""Simple RAG service using MongoDB for similar case retrieval"""
import logging
from typing import List, Dict, Any
from app.models.database import db

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieve similar past grievances from MongoDB"""
    
    async def find_similar_cases(
        self,
        category: str,
        department: str,
        keywords: List[str],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar resolved cases using MongoDB queries
        No vector DB needed - uses category + department matching
        
        Args:
            category: Grievance category
            department: Department name
            keywords: List of keywords (optional enhancement)
            limit: Max number of similar cases to return
            
        Returns:
            List of similar case summaries
        """
        try:
            collection = db.get_collection("grievances")
            
            # Query: same category + department + resolved status
            query = {
                "category": category,
                "department": department,
                "status": "Resolved"
            }
            
            # Find matching cases, sort by most recent
            cursor = collection.find(query).sort("resolved_at", -1).limit(limit)
            similar_cases = await cursor.to_list(length=limit)
            
            # Format results
            results = []
            for case in similar_cases:
                results.append({
                    "grievance_id": case.get("grievance_id", "N/A"),
                    "summary": case.get("summary", "")[:200],
                    "resolution_actions": case.get("recommended_actions", []),
                    "resolution_time": case.get("estimated_resolution_time", "Unknown"),
                    "resolved_at": case.get("resolved_at")
                })
            
            logger.info(f"Found {len(results)} similar cases for category={category}, dept={department}")
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar cases: {e}")
            return []


# Singleton instance
rag_service = RAGService()