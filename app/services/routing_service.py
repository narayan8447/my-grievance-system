"""Routing service for assigning grievances to appropriate departments and officers"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from app.config import settings
from app.models.database import db

logger = logging.getLogger(__name__)


class RoutingService:
    """Service for routing grievances to appropriate departments and officers"""
    
    def __init__(self):
        self.departments = settings.DEPARTMENTS
        
        # Department hierarchies and escalation paths
        self.department_hierarchy = {
            "Roads and Buildings": {
                "levels": ["Junior Engineer", "Assistant Engineer", "Executive Engineer", "Superintendent Engineer"],
                "escalation_threshold_days": 7
            },
            "Water Supply": {
                "levels": ["Field Officer", "Assistant Engineer", "Executive Engineer", "Chief Engineer"],
                "escalation_threshold_days": 5
            },
            "Electricity": {
                "levels": ["Lineman", "Assistant Engineer", "Sub-Divisional Engineer", "Divisional Engineer"],
                "escalation_threshold_days": 3
            },
            "Revenue": {
                "levels": ["Revenue Inspector", "Tahsildar", "Revenue Divisional Officer", "District Collector"],
                "escalation_threshold_days": 10
            },
            "Health": {
                "levels": ["Health Inspector", "Medical Officer", "District Medical Officer", "District Health Officer"],
                "escalation_threshold_days": 2
            },
            "Education": {
                "levels": ["Headmaster", "MEO", "DEO", "Regional Director"],
                "escalation_threshold_days": 7
            },
            "Police": {
                "levels": ["Constable", "Sub-Inspector", "Circle Inspector", "Deputy Superintendent"],
                "escalation_threshold_days": 1
            },
            "Municipal": {
                "levels": ["Sanitary Inspector", "Health Officer", "Municipal Commissioner"],
                "escalation_threshold_days": 5
            },
            "Agriculture": {
                "levels": ["Agricultural Officer", "Deputy Director", "Joint Director"],
                "escalation_threshold_days": 7
            },
            "Social Welfare": {
                "levels": ["Welfare Officer", "Project Director", "Commissioner"],
                "escalation_threshold_days": 10
            }
        }
    
    async def route_grievance(
        self,
        grievance_id: str,
        category: str,
        department: str,
        priority: str,
        location: Optional[str] = None
    ) -> Dict:
        """
        Route grievance to appropriate officer
        
        Args:
            grievance_id: Unique grievance ID
            category: Grievance category
            department: Assigned department
            priority: Priority level (Low, Medium, High, Critical)
            location: Location/district if available
            
        Returns:
            Routing information including assigned officer
        """
        try:
            logger.info(f"Routing grievance {grievance_id} to {department}")
            
            # Determine officer level based on priority
            officer_level = self._get_officer_level(department, priority)
            
            # Find available officer (in real system, this would query officer database)
            assigned_officer = self._assign_officer(department, officer_level, location)
            
            # Determine escalation timeline
            escalation_info = self._get_escalation_info(department, priority)
            
            # Create routing record
            routing_data = {
                "grievance_id": grievance_id,
                "department": department,
                "assigned_officer": assigned_officer,
                "officer_level": officer_level,
                "assigned_at": datetime.utcnow(),
                "expected_resolution_date": escalation_info["expected_resolution_date"],
                "escalation_date": escalation_info["escalation_date"],
                "routing_reason": f"Routed based on category: {category}, priority: {priority}",
                "location": location
            }
            
            # Save routing information to database
            await self._save_routing(routing_data)
            
            logger.info(f"Grievance routed to {assigned_officer['name']} ({officer_level})")
            return routing_data
            
        except Exception as e:
            logger.error(f"Error routing grievance: {e}")
            return self._fallback_routing(grievance_id, department)
    
    def _get_officer_level(self, department: str, priority: str) -> str:
        """
        Determine appropriate officer level based on priority
        
        Args:
            department: Department name
            priority: Priority level
            
        Returns:
            Officer level/designation
        """
        hierarchy = self.department_hierarchy.get(department, {})
        levels = hierarchy.get("levels", ["Officer", "Senior Officer", "Head"])
        
        # Map priority to level
        priority_mapping = {
            "Critical": -1,  # Highest level
            "High": -2,
            "Medium": 0,     # Lowest level
            "Low": 0
        }
        
        level_index = priority_mapping.get(priority, 0)
        
        # Ensure valid index
        if level_index < 0:
            level_index = max(0, len(levels) + level_index)
        else:
            level_index = 0
        
        return levels[level_index] if level_index < len(levels) else levels[0]
    
    def _assign_officer(
        self,
        department: str,
        officer_level: str,
        location: Optional[str] = None
    ) -> Dict:
        """
        Assign specific officer (placeholder - would query real officer database)
        
        Args:
            department: Department name
            officer_level: Required officer level
            location: Location/district
            
        Returns:
            Officer information
        """
        # In a real system, this would:
        # 1. Query officer database
        # 2. Check availability/workload
        # 3. Consider location proximity
        # 4. Implement round-robin or load balancing
        
        # For POC, return placeholder officer data
        officer_id = f"OFF-{department[:3].upper()}-{hash(officer_level) % 1000:03d}"
        
        return {
            "officer_id": officer_id,
            "name": f"{officer_level} - {department}",
            "designation": officer_level,
            "department": department,
            "contact": "0123456789",  # Placeholder
            "email": f"{officer_id.lower()}@ap.gov.in",
            "location": location or "General"
        }
    
    def _get_escalation_info(self, department: str, priority: str) -> Dict:
        """
        Get escalation timeline information
        
        Args:
            department: Department name
            priority: Priority level
            
        Returns:
            Escalation information with dates
        """
        from datetime import timedelta
        
        hierarchy = self.department_hierarchy.get(department, {})
        base_days = hierarchy.get("escalation_threshold_days", 7)
        
        # Adjust based on priority
        priority_multiplier = {
            "Critical": 0.5,
            "High": 0.75,
            "Medium": 1.0,
            "Low": 1.5
        }
        
        days_to_escalate = int(base_days * priority_multiplier.get(priority, 1.0))
        days_to_resolve = days_to_escalate * 2
        
        now = datetime.utcnow()
        
        return {
            "escalation_date": now + timedelta(days=days_to_escalate),
            "expected_resolution_date": now + timedelta(days=days_to_resolve),
            "escalation_threshold_days": days_to_escalate
        }
    
    async def _save_routing(self, routing_data: Dict) -> None:
        """
        Save routing information to database
        
        Args:
            routing_data: Routing information
        """
        try:
            collection = db.get_collection("routing")
            await collection.insert_one(routing_data)
            logger.info(f"Routing saved for grievance {routing_data['grievance_id']}")
        except Exception as e:
            logger.error(f"Error saving routing: {e}")
    
    def _fallback_routing(self, grievance_id: str, department: str) -> Dict:
        """
        Fallback routing if main routing fails
        
        Args:
            grievance_id: Grievance ID
            department: Department name
            
        Returns:
            Basic routing information
        """
        from datetime import timedelta
        
        return {
            "grievance_id": grievance_id,
            "department": department,
            "assigned_officer": {
                "officer_id": "DEFAULT-001",
                "name": f"Default Officer - {department}",
                "designation": "Officer",
                "department": department
            },
            "officer_level": "Officer",
            "assigned_at": datetime.utcnow(),
            "expected_resolution_date": datetime.utcnow() + timedelta(days=10),
            "routing_reason": "Default routing due to error"
        }
    
    async def check_escalation_needed(self, grievance_id: str) -> Dict:
        """
        Check if grievance needs escalation
        
        Args:
            grievance_id: Grievance ID
            
        Returns:
            Escalation recommendation
        """
        try:
            # Get routing info
            routing_collection = db.get_collection("routing")
            routing = await routing_collection.find_one({"grievance_id": grievance_id})
            
            if not routing:
                return {"escalation_needed": False, "reason": "No routing found"}
            
            # Check if escalation date has passed
            escalation_date = routing.get("escalation_date")
            if escalation_date and datetime.utcnow() > escalation_date:
                return {
                    "escalation_needed": True,
                    "reason": "Escalation deadline exceeded",
                    "current_level": routing.get("officer_level"),
                    "escalate_to": self._get_next_level(
                        routing.get("department"),
                        routing.get("officer_level")
                    )
                }
            
            return {"escalation_needed": False, "reason": "Within timeline"}
            
        except Exception as e:
            logger.error(f"Error checking escalation: {e}")
            return {"escalation_needed": False, "reason": f"Error: {str(e)}"}
    
    def _get_next_level(self, department: str, current_level: str) -> str:
        """
        Get next level in hierarchy for escalation
        
        Args:
            department: Department name
            current_level: Current officer level
            
        Returns:
            Next level designation
        """
        hierarchy = self.department_hierarchy.get(department, {})
        levels = hierarchy.get("levels", ["Officer"])
        
        try:
            current_index = levels.index(current_level)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
            else:
                return levels[-1]  # Already at top
        except ValueError:
            return levels[-1] if levels else "Senior Officer"
    
    async def get_department_workload(self, department: str) -> Dict:
        """
        Get current workload for a department
        
        Args:
            department: Department name
            
        Returns:
            Workload statistics
        """
        try:
            collection = db.get_collection("grievances")
            
            # Count grievances by status
            open_count = await collection.count_documents({
                "department": department,
                "status": "Open"
            })
            
            in_review_count = await collection.count_documents({
                "department": department,
                "status": "In Review"
            })
            
            resolved_count = await collection.count_documents({
                "department": department,
                "status": "Resolved"
            })
            
            return {
                "department": department,
                "open": open_count,
                "in_review": in_review_count,
                "resolved": resolved_count,
                "total": open_count + in_review_count + resolved_count
            }
            
        except Exception as e:
            logger.error(f"Error getting department workload: {e}")
            return {
                "department": department,
                "error": str(e)
            }


# Singleton instance
routing_service = RoutingService()