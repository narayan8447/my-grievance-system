"""
Public grievance routes (no authentication required)
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Optional
import logging

from app.models.database import db
from app.models.schemas import Language
from app.workflows.langgraph_workflow import grievance_workflow
from app.services.image_service import image_service
from app.services.audio_service import audio_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/grievance/submit",
    status_code=status.HTTP_201_CREATED,
    summary="Submit Grievance (Public - No Auth)"
)

async def submit_grievance_public(
    text: str = Form(..., description="Grievance text"),
    language: Optional[Language] = Form(Language.ENGLISH),
    user_name: Optional[str] = Form("Anonymous"),
    user_contact: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None)
):
    """
    Submit a grievance (public endpoint - no authentication required)
    """
    try:
        logger.info(f"Public grievance submission from: {user_name}")
        
        # Initialize variables
        grievance_text = text
        document_analysis = None  # Will be populated if document is uploaded
        
        # Process image if provided
        if image:
            logger.info(f"Processing image: {image.filename}")
            image_data = await image.read()
            
            # Step 1: Basic image processing (resize, format)
            image_result = await image_service.process_image(image_data)
            
            if not image_result.get("success"):
                logger.warning(f"Image processing failed: {image_result.get('error')}")
            
            # Step 2: Extract text from image using OCR via document_service
            try:
                from app.services.document_service import document_service
                
                # Determine file extension from filename
                file_ext = image.filename.split('.')[-1].lower() if image.filename else 'jpg'
                
                logger.info(f"🔍 Starting OCR for image with extension: {file_ext}")
                
                # Analyze image for text extraction
                document_analysis = await document_service.analyze_document(
                    document_bytes=image_data,
                    file_extension=file_ext,
                    context_text=text[:500]  # Provide grievance context
                )
                
                logger.info(f"📊 OCR Result: success={document_analysis.get('success')}")
                
                if document_analysis.get('success'):
                    extracted_text = document_analysis.get('extracted_text', '')
                    logger.info(f"✅ OCR extracted {len(extracted_text)} characters from image")
                    
                    # Append extracted text to grievance text
                    if extracted_text and len(extracted_text) > 10:
                        grievance_text = f"{text}\n\n[Text from image]: {extracted_text}"
                        logger.info("✅ Appended OCR text to grievance")
                else:
                    logger.warning(f"⚠️ Image OCR failed: {document_analysis.get('error')}")
                    # Keep the error result for debugging - don't set to None
            except Exception as e:
                logger.error(f"❌ Error during image OCR: {e}", exc_info=True)
                # Keep error information instead of setting to None
                document_analysis = {
                    "success": False,
                    "error": f"OCR processing error: {str(e)}",
                    "extracted_text": "",
                    "key_entities": {},
                    "document_type": "error",
                    "confidence": 0.0
                }
        
        # Process audio if provided
        if audio:
            logger.info(f"Processing audio: {audio.filename}")
            audio_data = await audio.read()
            
            if audio_service.validate_audio(audio_data):
                transcription = await audio_service.transcribe_audio(
                    audio_data,
                    language="te" if language == Language.TELUGU else "en"
                )
                
                if transcription.get("success") and transcription.get("text"):
                    grievance_text = f"{grievance_text}\n\n[Audio transcription]: {transcription['text']}"
                    logger.info("✅ Appended audio transcription to grievance")
        
        logger.info(f"📝 Final grievance_text length: {len(grievance_text)}")
        logger.info(f"📄 document_analysis type: {type(document_analysis)}")
        logger.info(f"📄 document_analysis is None: {document_analysis is None}")
        if document_analysis:
            logger.info(f"📄 document_analysis.success: {document_analysis.get('success')}")
            logger.info(f"📄 document_analysis keys: {list(document_analysis.keys())}")
        
        # Process through workflow
        result = await grievance_workflow.process_grievance(
            grievance_text=grievance_text,
            language=language.value,
            user_name=user_name or "Anonymous",
            user_contact=user_contact or "",
            location=location or "",
            document_analysis=document_analysis  # Pass OCR results
        )
        
        if result.get("error"):
            logger.error(f"Workflow error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing error: {result['error']}"
            )
        
        logger.info(f"Successfully created grievance: {result['grievance_id']}")
        
        return {
            "success": True,
            "grievance_id": result["grievance_id"],
            "message": "Grievance submitted successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting grievance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit grievance: {str(e)}"
        )


@router.get(
    "/grievance/{grievance_id}",
    summary="Track Grievance (Public)"
)
async def track_grievance_public(grievance_id: str):
    """
    Track a grievance by ID (public endpoint - no authentication required)
    """
    try:
        collection = db.get_collection("grievances")
        
        grievance = await collection.find_one({"grievance_id": grievance_id})
        
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grievance '{grievance_id}' not found"
            )
        
        # Remove MongoDB _id
        if "_id" in grievance:
            del grievance["_id"]
        
        return grievance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking grievance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track grievance"
        )


@router.get(
    "/grievances",
    summary="List Grievances (Public with Filters)"
)
async def list_grievances_public(
    status: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    List grievances with filters (public endpoint)
    """
    try:
        collection = db.get_collection("grievances")
        
        # Build query
        query = {}
        if status:
            query["status"] = status
        if department:
            query["department"] = department
        if category:
            query["category"] = category
        
        # Get grievances
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        grievances = await cursor.to_list(length=limit)
        
        # Count total
        total = await collection.count_documents(query)
        
        # Remove MongoDB _id from all grievances
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