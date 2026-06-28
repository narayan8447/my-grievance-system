"""
Addresser-specific routes - NEW
Department officers can view and update grievances assigned to their department
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import logging
from datetime import datetime

from app.models.database import db
from app.models.user import User, AddresserUpdate
from app.api.dependencies import require_addresser

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/dashboard",
    summary="Addresser Dashboard - Department Overview"
)
async def get_addresser_dashboard(
    addresser: User = Depends(require_addresser)
):
    """
    Get dashboard statistics for addresser's department
    Shows only grievances for the addresser's assigned department
    """
    try:
        collection = db.get_collection("grievances")
        department = addresser.department
        
        # Count grievances by status in this department
        status_counts = {}
        for status_type in ["Open", "In Review", "Resolved", "Rejected"]:
            count = await collection.count_documents({
                "assignment.assigned_to_department": department,
                "status": status_type
            })
            status_counts[status_type] = count
        
        # Count by priority in this department
        priority_counts = {}
        for priority in ["Low", "Medium", "High", "Critical"]:
            count = await collection.count_documents({
                "assignment.assigned_to_department": department,
                "priority": priority
            })
            priority_counts[priority] = count
        
        # Get pending action items (Open or In Review, High/Critical priority)
        pending = await collection.find({
            "assignment.assigned_to_department": department,
            "status": {"$in": ["Open", "In Review"]},
            "priority": {"$in": ["High", "Critical"]}
        }).sort("created_at", 1).limit(10).to_list(10)
        
        # Format pending items
        pending_items = []
        for g in pending:
            # Calculate days open
            days_open = (datetime.utcnow() - g.get("created_at")).days
            pending_items.append({
                "grievance_id": g.get("grievance_id"),
                "summary": g.get("summary", "N/A")[:100],
                "priority": g.get("priority"),
                "status": g.get("status"),
                "days_open": days_open,
                "category": g.get("category")
            })
        
        # Total grievances in department
        total = await collection.count_documents({
            "assignment.assigned_to_department": department
        })
        
        # Get my recent updates count
        my_updates_count = await collection.count_documents({
            f"addresser_updates.addresser_id": addresser.user_id
        })
        
        logger.info(f"Addresser {addresser.email} accessed dashboard for {department}")
        
        return {
            "department": department,
            "addresser_name": addresser.full_name,
            "total_grievances": total,
            "my_updates_count": my_updates_count,
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "pending_action": pending_items
        }
        
    except Exception as e:
        logger.error(f"Error fetching addresser dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get(
    "/grievances",
    summary="List Department Grievances"
)
async def list_department_grievances(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    addresser: User = Depends(require_addresser)
):
    """
    List all grievances assigned to addresser's department
    Includes AI analysis and recommendations
    """
    try:
        collection = db.get_collection("grievances")
        department = addresser.department
        
        # Build query - must be in addresser's department
        query = {"assignment.assigned_to_department": department}
        
        if status_filter:
            query["status"] = status_filter
        if priority:
            query["priority"] = priority
        if category:
            query["category"] = category
        
        # Get grievances
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        grievances = await cursor.to_list(length=limit)
        from app.utils.helpers import clean_doc
        grievances = clean_doc(grievances)
        
        # Count total
        total = await collection.count_documents(query)
        
        # Format response - include AI analysis
        formatted_grievances = []
        for g in grievances:
            # Remove MongoDB _id
            if "_id" in g:
                del g["_id"]
            
            # Add flag for whether this addresser has updated
            my_updates = [
                u for u in g.get("addresser_updates", [])
                if u.get("addresser_id") == addresser.user_id
            ]
            
            formatted_grievances.append({
                **g,
                "my_updates_count": len(my_updates),
                "has_my_update": len(my_updates) > 0
            })
        
        return {
            "department": department,
            "total": total,
            "skip": skip,
            "limit": limit,
            "grievances": formatted_grievances
        }
        
    except Exception as e:
        logger.error(f"Error listing department grievances: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch grievances"
        )


@router.get(
    "/grievance/{grievance_id}",
    summary="Get Grievance Details (Department Access)"
)
async def get_grievance_detail(
    grievance_id: str,
    addresser: User = Depends(require_addresser)
):
    """
    Get detailed grievance information
    Addresser can only access grievances in their department
    """
    try:
        collection = db.get_collection("grievances")
        
        grievance = await collection.find_one({
            "grievance_id": grievance_id,
            "assignment.assigned_to_department": addresser.department
        })
        
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grievance not found or not in your department"
            )
        
        # Remove MongoDB _id
        if "_id" in grievance:
            del grievance["_id"]
        
        # Highlight addresser's own updates
        if "addresser_updates" in grievance:
            for update in grievance["addresser_updates"]:
                update["is_mine"] = update.get("addresser_id") == addresser.user_id
        
        return grievance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching grievance details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch grievance"
        )


@router.post(
    "/grievance/{grievance_id}/update",
    summary="Submit Work Update"
)
async def submit_work_update(
    grievance_id: str,
    update_data: AddresserUpdate,
    addresser: User = Depends(require_addresser)
):
    """
    Addresser submits work update for a grievance
    Updates are visible to admin and optionally to citizen
    """
    try:
        collection = db.get_collection("grievances")
        
        # Verify grievance exists and is in addresser's department
        grievance = await collection.find_one({
            "grievance_id": grievance_id,
            "assignment.assigned_to_department": addresser.department
        })
        
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found or not in your department"
            )
        
        # Create update record
        update_record = {
            "addresser_id": addresser.user_id,
            "addresser_name": addresser.full_name,
            "department": addresser.department,
            "work_done": update_data.work_done,
            "remarks": update_data.remarks,
            "visibility": update_data.visibility,
            "timestamp": datetime.utcnow()
        }
        
        # If status is being changed, include it
        update_fields = {}
        if update_data.status:
            update_record["status_update"] = update_data.status
            update_fields["status"] = update_data.status
        
        # Add to processing logs
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "addresser_update",
            "actor": addresser.user_id,
            "details": f"Addresser update: {update_data.work_done[:50]}..."
        }
        
        # Update grievance
        result = await collection.update_one(
            {"grievance_id": grievance_id},
            {
                "$push": {
                    "addresser_updates": update_record,
                    "processing_logs": log_entry
                },
                "$set": {
                    "updated_at": datetime.utcnow(),
                    **update_fields
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit update"
            )
        
        logger.info(f"Addresser {addresser.email} updated grievance {grievance_id}")
        
        # TODO: Send notification to admin
        
        return {
            "success": True,
            "grievance_id": grievance_id,
            "update_timestamp": update_record["timestamp"].isoformat(),
            "status_updated": update_data.status is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting addresser update: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit update"
        )


@router.get(
    "/my-updates",
    summary="Get My Update History"
)
async def get_my_updates(
    limit: int = 50,
    addresser: User = Depends(require_addresser)
):
    """
    Get history of all updates submitted by this addresser
    """
    try:
        collection = db.get_collection("grievances")
        
        # Find all grievances where this addresser has submitted updates
        grievances = await collection.find({
            "addresser_updates.addresser_id": addresser.user_id
        }).sort("updated_at", -1).limit(limit).to_list(limit)
        
        # Extract relevant information
        updates_history = []
        for g in grievances:
            # Get only this addresser's updates
            my_updates = [
                u for u in g.get("addresser_updates", [])
                if u.get("addresser_id") == addresser.user_id
            ]
            
            for update in my_updates:
                updates_history.append({
                    "grievance_id": g.get("grievance_id"),
                    "grievance_summary": g.get("summary", "N/A")[:100],
                    "update": update,
                    "current_status": g.get("status")
                })
        
        return {
            "total_updates": len(updates_history),
            "updates": updates_history
        }
        
    except Exception as e:
        logger.error(f"Error fetching addresser updates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch update history"
        )


@router.get(
    "/statistics",
    summary="Get Addresser Statistics"
)
async def get_addresser_statistics(
    addresser: User = Depends(require_addresser)
):
    """
    Get performance statistics for this addresser
    """
    try:
        collection = db.get_collection("grievances")
        
        # Count updates submitted
        updates_count = await collection.count_documents({
            "addresser_updates.addresser_id": addresser.user_id
        })
        
        # Count resolved grievances where addresser participated
        resolved_count = await collection.count_documents({
            "addresser_updates.addresser_id": addresser.user_id,
            "status": "Resolved"
        })
        
        # Average resolution time for resolved grievances
        # (This would require aggregation pipeline for accurate calculation)
        
        return {
            "addresser_name": addresser.full_name,
            "department": addresser.department,
            "total_updates_submitted": updates_count,
            "grievances_resolved": resolved_count,
            "resolution_rate": f"{(resolved_count/updates_count*100):.1f}%" if updates_count > 0 else "N/A"
        }
        
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )