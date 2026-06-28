"""
Admin-specific routes - ENHANCED
Added: Assignment endpoint, Department updates endpoint
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import logging
from datetime import datetime

from app.models.database import db
from app.models.user import User, UpdateGrievanceStatus, AssignGrievance
from app.api.dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.put(
    "/grievance/{grievance_id}/assign",
    summary="Assign/Reassign Grievance to Department (NEW)"
)
async def assign_grievance_to_department(
    grievance_id: str,
    assignment: AssignGrievance,
    admin: User = Depends(require_admin)
):
    """
    NEW: Admin manually assigns or reassigns grievance to a department
    If department is None, uses the AI-suggested department
    """
    try:
        collection = db.get_collection("grievances")
        
        # Get grievance
        grievance = await collection.find_one({"grievance_id": grievance_id})
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grievance '{grievance_id}' not found"
            )
        
        # Determine department
        if assignment.department:
            # Manual assignment
            target_department = assignment.department
            assignment_type = "manual"
        else:
            # Use AI-suggested department
            target_department = grievance.get("department", "Municipal")
            assignment_type = "ai_confirmed"
        
        # Get current assignment
        current_assignment = grievance.get("assignment", {})
        old_department = current_assignment.get("assigned_to_department")
        
        # Create assignment history entry if reassigning
        history_entry = None
        if old_department and old_department != target_department:
            history_entry = {
                "from_dept": old_department,
                "to_dept": target_department,
                "changed_by": admin.user_id,
                "changed_by_name": admin.full_name,
                "reason": assignment.reason or "Manual reassignment",
                "timestamp": datetime.utcnow()
            }
        
        # Create new assignment data
        new_assignment = {
            "assigned_by": admin.user_id,
            "assigned_by_name": admin.full_name,
            "assigned_to_department": target_department,
            "assignment_type": assignment_type,
            "assigned_at": datetime.utcnow()
        }
        
        # Add history if reassigning
        if history_entry:
            old_assignment = grievance.get("assignment") or {}
            existing_history = old_assignment.get("assignment_history") or []
            new_assignment["assignment_history"] = existing_history + [history_entry]
        elif grievance.get("assignment") and isinstance(grievance["assignment"], dict) and "assignment_history" in grievance["assignment"]:
            new_assignment["assignment_history"] = grievance["assignment"]["assignment_history"]
        else:
            new_assignment["assignment_history"] = []
        
        # Update database
        update_data = {
            "assignment": new_assignment,
            "department": target_department,  # Also update top-level department
            "updated_at": datetime.utcnow()
        }
        
        # Add to processing logs
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "assigned" if not old_department else "reassigned",
            "actor": admin.user_id,
            "details": f"Assigned to {target_department}" + (f" (from {old_department})" if old_department else "")
        }
        
        update_operations = {
            "$set": update_data,
            "$push": {"processing_logs": log_entry}
        }
        
        result = await collection.update_one(
            {"grievance_id": grievance_id},
            update_operations
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign grievance"
            )
        
        logger.info(f"Admin {admin.email} assigned grievance {grievance_id} to {target_department}")
        
        # TODO: Send notification to addressers in that department
        
        return {
            "success": True,
            "grievance_id": grievance_id,
            "assigned_to_department": target_department,
            "assignment_type": assignment_type,
            "previous_department": old_department,
            "message": f"Grievance successfully {'assigned' if not old_department else 'reassigned'} to {target_department}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning grievance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign grievance: {str(e)}"
        )


@router.get(
    "/department-updates",
    summary="Get Department-Wise Addresser Updates (NEW)"
)
async def get_department_updates(
    department: Optional[str] = None,
    status_filter: Optional[str] = None,
    from_date: Optional[str] = None,
    limit: int = 50,
    admin: User = Depends(require_admin)
):
    """
    NEW: Get real-time updates submitted by addressers, filtered by department
    Helps admin track progress across departments
    """
    try:
        collection = db.get_collection("grievances")
        
        # Build query
        query = {"addresser_updates": {"$exists": True, "$ne": []}}
        
        if department:
            query["assignment.assigned_to_department"] = department
        
        if status_filter:
            query["status"] = status_filter
        
        if from_date:
            try:
                date_obj = datetime.fromisoformat(from_date)
                query["addresser_updates.timestamp"] = {"$gte": date_obj}
            except ValueError:
                pass  # Ignore invalid date format
        
        # Get grievances with updates
        cursor = collection.find(query).sort("updated_at", -1).limit(limit)
        grievances = await cursor.to_list(length=limit)
        
        # Format response
        department_updates = []
        for g in grievances:
            # Get latest addresser update
            updates = g.get("addresser_updates", [])
            if not updates:
                continue
            
            # Sort by timestamp descending
            updates_sorted = sorted(
                updates,
                key=lambda x: x.get("timestamp", datetime.min),
                reverse=True
            )
            
            latest_update = updates_sorted[0]
            
            department_updates.append({
                "grievance_id": g.get("grievance_id"),
                "summary": g.get("summary", "N/A")[:100],
                "category": g.get("category"),
                "priority": g.get("priority"),
                "status": g.get("status"),
                "department": g.get("assignment", {}).get("assigned_to_department"),
                "latest_update": {
                    "addresser_name": latest_update.get("addresser_name"),
                    "work_done": latest_update.get("work_done"),
                    "remarks": latest_update.get("remarks"),
                    "visibility": latest_update.get("visibility"),
                    "timestamp": latest_update.get("timestamp").isoformat() if latest_update.get("timestamp") else None
                },
                "total_updates": len(updates),
                "created_at": g.get("created_at").isoformat() if g.get("created_at") else None
            })
        
        # Count by department
        department_summary = {}
        if not department:
            for update in department_updates:
                dept = update.get("department", "Unassigned")
                if dept not in department_summary:
                    department_summary[dept] = 0
                department_summary[dept] += 1
        
        return {
            "total_updates": len(department_updates),
            "filters": {
                "department": department,
                "status": status_filter,
                "from_date": from_date
            },
            "department_summary": department_summary if not department else None,
            "updates": department_updates
        }
        
    except Exception as e:
        logger.error(f"Error fetching department updates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch department updates"
        )


@router.get(
    "/assignment-history/{grievance_id}",
    summary="Get Assignment History (NEW)"
)
async def get_assignment_history(
    grievance_id: str,
    admin: User = Depends(require_admin)
):
    """
    NEW: Get complete assignment/reassignment history for a grievance
    """
    try:
        collection = db.get_collection("grievances")
        
        grievance = await collection.find_one({"grievance_id": grievance_id})
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grievance '{grievance_id}' not found"
            )
        
        assignment = grievance.get("assignment", {})
        history = assignment.get("assignment_history", [])
        
        # Format history
        formatted_history = []
        for entry in history:
            formatted_history.append({
                "from_department": entry.get("from_dept"),
                "to_department": entry.get("to_dept"),
                "changed_by": entry.get("changed_by_name"),
                "reason": entry.get("reason"),
                "timestamp": entry.get("timestamp").isoformat() if entry.get("timestamp") else None
            })
        
        return {
            "grievance_id": grievance_id,
            "current_assignment": {
                "department": assignment.get("assigned_to_department"),
                "assigned_by": assignment.get("assigned_by_name"),
                "assignment_type": assignment.get("assignment_type"),
                "assigned_at": assignment.get("assigned_at").isoformat() if assignment.get("assigned_at") else None
            },
            "history": formatted_history,
            "total_reassignments": len(formatted_history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching assignment history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch assignment history"
        )


# ===== EXISTING ENDPOINTS (Keep these) =====

@router.put(
    "/grievance/{grievance_id}/status",
    summary="Update Grievance Status (Admin Only)"
)
async def update_grievance_status(
    grievance_id: str,
    update: UpdateGrievanceStatus,
    admin: User = Depends(require_admin)
):
    """Admin updates grievance status with comments"""
    try:
        collection = db.get_collection("grievances")
        
        grievance = await collection.find_one({"grievance_id": grievance_id})
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grievance '{grievance_id}' not found"
            )
        
        update_data = {
            "status": update.status,
            "updated_at": datetime.utcnow(),
            "admin_updates": {
                "admin_id": admin.user_id,
                "admin_name": admin.full_name,
                "comment": update.admin_comment,
                "estimated_resolution": update.estimated_resolution,
                "timestamp": datetime.utcnow()
            }
        }
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "status_updated",
            "admin": admin.full_name,
            "old_status": grievance.get("status"),
            "new_status": update.status,
            "comment": update.admin_comment
        }
        
        result = await collection.update_one(
            {"grievance_id": grievance_id},
            {
                "$set": update_data,
                "$push": {"processing_logs": log_entry}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update grievance"
            )
        
        logger.info(f"Admin {admin.email} updated grievance {grievance_id} status to {update.status}")
        
        return {
            "success": True,
            "message": "Grievance status updated successfully",
            "grievance_id": grievance_id,
            "new_status": update.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating grievance status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}"
        )


@router.get(
    "/dashboard",
    summary="Admin Dashboard Statistics"
)
async def get_admin_dashboard(
    admin: User = Depends(require_admin)
):
    """Get dashboard statistics for admin"""
    try:
        collection = db.get_collection("grievances")
        
        status_counts = {}
        for status_type in ["Open", "In Review", "Resolved", "Rejected"]:
            count = await collection.count_documents({"status": status_type})
            status_counts[status_type] = count
        
        priority_counts = {}
        for priority in ["Low", "Medium", "High", "Critical"]:
            count = await collection.count_documents({"priority": priority})
            priority_counts[priority] = count
        
        departments = await collection.distinct("assignment.assigned_to_department")
        department_counts = {}
        for dept in departments:
            if dept:
                count = await collection.count_documents({"assignment.assigned_to_department": dept})
                department_counts[dept] = count
        
        from app.utils.helpers import clean_doc
        recent = await collection.find().sort("created_at", -1).limit(10).to_list(10)
        recent = clean_doc(recent)
        for g in recent:
            if "_id" in g:
                del g["_id"]
        
        total = await collection.count_documents({})
        
        return {
            "total_grievances": total,
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "department_breakdown": department_counts,
            "recent_grievances": recent
        }
        
    except Exception as e:
        logger.error(f"Error fetching admin dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get(
    "/grievances",
    summary="List All Grievances (Admin View)"
)
async def admin_list_grievances(
    status: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    admin: User = Depends(require_admin)
):
    """Admin can view all grievances with filters"""
    try:
        collection = db.get_collection("grievances")
        
        query = {}
        if status:
            query["status"] = status
        if department:
            query["assignment.assigned_to_department"] = department
        if category:
            query["category"] = category
        if priority:
            query["priority"] = priority
        
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        from app.utils.helpers import clean_doc
        grievances = await cursor.to_list(length=limit)
        grievances = clean_doc(grievances)
        total = await collection.count_documents(query)
        for g in grievances:
            if "_id" in g:
                del g["_id"]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "grievances": grievances
        }
        
    except Exception as e:
        logger.error(f"Error listing grievances: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch grievances"
        )