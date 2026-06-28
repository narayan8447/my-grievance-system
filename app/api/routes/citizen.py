"""Citizen-specific routes - FIXED with proper image OCR handling"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import Optional
import logging
from datetime import datetime

from app.models.database import db
from app.models.user import User
from app.models.schemas import Language
from app.api.dependencies import require_citizen, verify_grievance_ownership
from app.workflows.langgraph_workflow import grievance_workflow
from app.services.image_service import image_service
from app.services.audio_service import audio_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/citizen/grievance/submit",
    status_code=status.HTTP_201_CREATED,
    summary="Submit Grievance (Citizen)"
)
async def citizen_submit_grievance(
    text: str = Form(..., description="Grievance text"),
    language: Optional[Language] = Form(Language.ENGLISH),
    location: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    document: Optional[UploadFile] = File(None),
    citizen: User = Depends(require_citizen)
):
    """
    Citizen submits a grievance (authenticated)
    Supports: text + optional image/audio/document
    """
    try:
        logger.info(f"Citizen {citizen.email} submitting grievance")
        
        # Initialize results for all media types
        audio_result = None
        image_result = None
        document_result = None
        
        # 1. PROCESS AUDIO if provided
        if audio is not None and audio.filename:
            logger.info(f"🎤 Processing audio: {audio.filename}")
            audio_data = await audio.read()
            
            if audio_data:
                if not audio_service.validate_audio(audio_data):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid audio file"
                    )
                
                transcription = await audio_service.transcribe_audio(
                    audio_data,
                    language="te" if language == Language.TELUGU else "en"
                )
                
                audio_result = {
                    "success": transcription.get("success", False),
                    "text": transcription.get("text"),
                    "language": "te" if language == Language.TELUGU else "en",
                    "confidence": 0.8 if transcription.get("success") else 0.0,
                    "error": transcription.get("error")
                }
                
                logger.info(f"✅ Audio transcription: {audio_result.get('success')}")
            else:
                logger.warning("⚠️ Audio file uploaded but no data received")
        
        # 2. PROCESS IMAGE if provided - FIXED VERSION
        if image is not None and image.filename:
            logger.info(f"🖼️ Processing image: {image.filename}")
            image_data = await image.read()
            
            if image_data:
                try:
                    # Step 1: Basic validation and processing
                    processed = await image_service.process_image(image_data)
                    
                    if not processed.get("success"):
                        logger.warning(f"⚠️ Image processing failed: {processed.get('error')}")
                        # Still continue to try OCR even if processing had issues
                    
                    # Step 2: Extract text using OCR
                    logger.info("🔍 Attempting OCR text extraction from image...")
                    ocr_text = await image_service.extract_text_from_image(image_data)
                    
                    # Create properly structured image_result
                    if ocr_text and len(ocr_text.strip()) > 5:
                        # SUCCESS: OCR extracted meaningful text
                        image_result = {
                            "success": True,
                            "text": ocr_text.strip(),
                            "confidence": 0.75,
                            "error": None
                        }
                        logger.info(f"✅ OCR SUCCESS: Extracted {len(ocr_text)} characters")
                        logger.info(f"📝 Preview: {ocr_text[:100]}...")
                    else:
                        # OCR ran but found no meaningful text
                        image_result = {
                            "success": False,
                            "text": "",
                            "confidence": 0.0,
                            "error": "No readable text found in image"
                        }
                        logger.warning("⚠️ OCR completed but no meaningful text extracted")
                
                except Exception as ocr_error:
                    # OCR completely failed
                    logger.error(f"❌ OCR Error: {ocr_error}", exc_info=True)
                    image_result = {
                        "success": False,
                        "text": "",
                        "confidence": 0.0,
                        "error": f"OCR processing error: {str(ocr_error)}"
                    }
            else:
                logger.warning("⚠️ Image file uploaded but no data received")
        else:
            logger.info("ℹ️ No image file provided")
        
        # 3. PROCESS DOCUMENT if provided
        if document is not None and document.filename:
            logger.info(f"📄 Processing document: {document.filename}")
            from app.services.document_service import document_service
            
            doc_data = await document.read()
            
            if doc_data:
                file_ext = document.filename.split('.')[-1].lower() if '.' in document.filename else 'pdf'
                
                # Analyze document for text extraction
                document_result = await document_service.analyze_document(
                    document_bytes=doc_data,
                    file_extension=file_ext,
                    context_text=text[:500]
                )
                
                logger.info(f"📄 Document analysis: {document_result.get('success')}")
                
                if not document_result.get('success'):
                    logger.warning(f"⚠️ Document analysis failed: {document_result.get('error')}")
            else:
                logger.warning("⚠️ Document file uploaded but no data received")
        
        # 4. LOG WHAT WE'RE SENDING TO WORKFLOW
        logger.info("=" * 60)
        logger.info("📤 SENDING TO WORKFLOW:")
        logger.info(f"   • Base text length: {len(text)}")
        logger.info(f"   • Audio result: {audio_result is not None} (success={audio_result.get('success') if audio_result else 'N/A'})")
        logger.info(f"   • Image result: {image_result is not None} (success={image_result.get('success') if image_result else 'N/A'})")
        if image_result and image_result.get('success'):
            logger.info(f"   • Image text length: {len(image_result.get('text', ''))}")
        logger.info(f"   • Document result: {document_result is not None} (success={document_result.get('success') if document_result else 'N/A'})")
        logger.info("=" * 60)
        
        # 5. CALL WORKFLOW with ALL results
        result = await grievance_workflow.process_grievance(
            grievance_text=text,
            language=language.value,
            user_name=citizen.full_name,
            user_contact=citizen.email,
            location=location or citizen.location,
            audio_transcription=audio_result,
            image_ocr=image_result,  # This is now properly structured
            document_analysis=document_result
        )
        
        if result.get("error"):
            logger.error(f"❌ Workflow error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing error: {result['error']}"
            )
        
        # Link grievance to citizen
        collection = db.get_collection("users")
        await collection.update_one(
            {"user_id": citizen.user_id},
            {"$push": {"grievances_submitted": result["grievance_id"]}}
        )
        
        logger.info(f"✅ Successfully created grievance: {result['grievance_id']}")
        
        return {
            "success": True,
            "grievance_id": result["grievance_id"],
            "message": "Grievance submitted successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting grievance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit grievance: {str(e)}"
        )


@router.get(
    "/citizen/my-grievances",
    summary="Get My Grievances (Citizen)"
)
async def get_my_grievances(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    citizen: User = Depends(require_citizen)
):
    """
    Get all grievances submitted by the logged-in citizen
    """
    try:
        collection = db.get_collection("grievances")
        
        # Build query - filter by user's email (primary) or phone (if exists)
        or_conditions = [{"user_contact": citizen.email}]
        
        if citizen.phone:
            or_conditions.append({"user_contact": citizen.phone})
        
        query = {"$or": or_conditions}
        
        if status:
            query["status"] = status
        
        logger.info(f"Query for citizen {citizen.email}: {query}")
        
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        grievances = await cursor.to_list(length=limit)
        from app.utils.helpers import clean_doc
        grievances = clean_doc(grievances)
        
        total = await collection.count_documents(query)
        
        for g in grievances:
            if "_id" in g:
                del g["_id"]
        
        logger.info(f"Found {total} grievances for citizen {citizen.email}")
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "grievances": grievances
        }
        
    except Exception as e:
        logger.error(f"Error fetching citizen grievances: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your grievances"
        )


@router.get(
    "/citizen/grievance/{grievance_id}",
    summary="Get My Grievance Details"
)
async def get_my_grievance(
    grievance_id: str,
    citizen: User = Depends(require_citizen)
):
    """
    Get specific grievance details (citizen can only see their own)
    """
    try:
        grievance = await verify_grievance_ownership(grievance_id, citizen)
        
        if "_id" in grievance:
            del grievance["_id"]
        
        return grievance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching grievance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch grievance"
        )


@router.post(
    "/citizen/grievance/{grievance_id}/feedback",
    summary="Submit Feedback on Grievance"
)
async def submit_feedback(
    grievance_id: str,
    feedback: str = Form(..., min_length=10),
    rating: int = Form(..., ge=1, le=5),
    citizen: User = Depends(require_citizen)
):
    """
    Citizen submits feedback and rating for resolved grievance
    """
    try:
        grievance = await verify_grievance_ownership(grievance_id, citizen)
        
        if grievance.get("status") != "Resolved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only provide feedback for resolved grievances"
            )
        
        collection = db.get_collection("grievances")
        result = await collection.update_one(
            {"grievance_id": grievance_id},
            {
                "$set": {
                    "citizen_feedback": {
                        "feedback": feedback,
                        "rating": rating,
                        "submitted_at": datetime.utcnow()
                    },
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit feedback"
            )
        
        logger.info(f"Citizen {citizen.email} submitted feedback for {grievance_id}")
        
        return {
            "success": True,
            "message": "Thank you for your feedback!",
            "grievance_id": grievance_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get(
    "/citizen/dashboard",
    summary="Citizen Dashboard"
)
async def get_citizen_dashboard(
    citizen: User = Depends(require_citizen)
):
    """
    Get dashboard statistics for citizen
    """
    try:
        collection = db.get_collection("grievances")
        
        or_conditions = [{"user_contact": citizen.email}]
        if citizen.phone:
            or_conditions.append({"user_contact": citizen.phone})
        
        query = {"$or": or_conditions}
        
        status_counts = {}
        for status_type in ["Open", "In Review", "Resolved", "Rejected"]:
            count = await collection.count_documents({**query, "status": status_type})
            status_counts[status_type] = count
        
        recent = await collection.find(query).sort("created_at", -1).limit(5).to_list(5)
        from app.utils.helpers import clean_doc
        recent = clean_doc(recent)
        for g in recent:
            if "_id" in g:
                del g["_id"]
        
        total = await collection.count_documents(query)
        
        return {
            "total_grievances": total,
            "status_breakdown": status_counts,
            "recent_grievances": recent
        }
        
    except Exception as e:
        logger.error(f"Error fetching citizen dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )