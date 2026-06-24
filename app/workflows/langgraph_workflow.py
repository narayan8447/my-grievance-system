"""
LangGraph workflow for grievance processing - FIXED
Added: Document understanding integration
"""
import logging
from typing import TypedDict, Optional, Dict, List, Any
from datetime import datetime
import uuid

# FIXED: Import StateGraph correctly
from langgraph.graph import StateGraph, END

from app.services.llm_service import llm_service
from app.chains.understanding_chain import UnderstandingChain
from app.chains.redressal_chain import RedressalChain
from app.models.database import db
from app.models.schemas import GrievanceStatus, Priority

logger = logging.getLogger(__name__)


class GrievanceState(TypedDict):
    """State for grievance processing workflow - ENHANCED"""
    # Input
    grievance_id: str
    grievance_text: str
    language: str
    user_name: str
    user_contact: str
    location: str
    
    # Analysis
    audio_transcription: Optional[Dict[str, Any]]
    image_ocr: Optional[Dict[str, Any]]
    document_analysis: Optional[Dict[str, Any]]
    
    # Processing
    summary: str
    category: str
    department: str
    priority: str
    keywords: List[str]
    confidence_score: float
    explanation: Optional[Dict[str, Any]]  # NEW: Explainability
    
    # Redressal
    recommended_actions: List[str]
    escalation_needed: bool
    estimated_resolution_time: str
    similar_cases: List[str]  # NEW: Similar case IDs
    
    # Assignment (auto-assigned by LLM)
    assignment: Optional[Dict[str, Any]]
    
    # Status
    status: str
    error: str


class GrievanceWorkflow:
    """LangGraph workflow for end-to-end grievance processing - ENHANCED"""
    
    def __init__(self):
        self.understanding_chain = UnderstandingChain(llm_service)
        self.redressal_chain = RedressalChain(llm_service)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Any:  # FIXED: Return type as Any instead of StateGraph
        """Build the state machine graph"""
        workflow = StateGraph(GrievanceState)
        
        # Add nodes
        workflow.add_node("analyze", self.analyze_grievance)
        workflow.add_node("suggest_redressal", self.suggest_redressal)
        workflow.add_node("save_to_db", self.save_to_database)
        
        # Define edges
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "suggest_redressal")
        workflow.add_edge("suggest_redressal", "save_to_db")
        workflow.add_edge("save_to_db", END)
        
        return workflow.compile()
    
    async def analyze_grievance(self, state: GrievanceState) -> GrievanceState:
        """
        Step 1: Analyze and classify the grievance
        ENHANCED: Combines text + audio + image + document analysis
        """
        try:
            logger.info(f"Analyzing grievance: {state['grievance_id']}")
            
            # Start with the base grievance text
            enhanced_text = state["grievance_text"]
            context_parts = []
            
            # 1. ADD AUDIO TRANSCRIPTION
            audio_transcription = state.get("audio_transcription")
            if audio_transcription and audio_transcription.get("success"):
                transcribed_text = audio_transcription.get("text", "")
                if transcribed_text:
                    context_parts.append(f"\n\n[Audio Transcription]:\n{transcribed_text}")
                    logger.info(f"✓ Added audio transcription ({len(transcribed_text)} chars)")
            elif audio_transcription and not audio_transcription.get("success"):
                logger.warning(f"✗ Audio transcription failed: {audio_transcription.get('error')}")
            
            # 2. ADD IMAGE OCR TEXT
            image_ocr = state.get("image_ocr")
            if image_ocr and image_ocr.get("success"):
                ocr_text = image_ocr.get("text", "")
                if ocr_text:
                    context_parts.append(f"\n\n[Image Text (OCR)]:\n{ocr_text}")
                    logger.info(f"✓ Added image OCR text ({len(ocr_text)} chars)")
            elif image_ocr and not image_ocr.get("success"):
                logger.warning(f"✗ Image OCR failed: {image_ocr.get('error')}")
            
            # 3. ADD DOCUMENT ANALYSIS
            doc_analysis = state.get("document_analysis")
            if doc_analysis and doc_analysis.get("success"):
                extracted_text = doc_analysis.get("extracted_text", "")
                if extracted_text:
                    context_parts.append(f"\n\n[Document Content]:\n{extracted_text[:1000]}")
                
                key_entities = doc_analysis.get("key_entities", {})
                if key_entities:
                    entity_info = []
                    if key_entities.get("dates"):
                        entity_info.append(f"- Dates: {', '.join(key_entities['dates'][:3])}")
                    if key_entities.get("amounts"):
                        entity_info.append(f"- Amounts: {', '.join(key_entities['amounts'][:3])}")
                    if key_entities.get("locations"):
                        entity_info.append(f"- Locations: {', '.join(key_entities['locations'][:3])}")
                    
                    if entity_info:
                        context_parts.append("\n\n[Key Information from Document]:\n" + "\n".join(entity_info))
                
                logger.info(f"✓ Added document analysis ({len(extracted_text)} chars)")
            elif doc_analysis and not doc_analysis.get("success"):
                logger.warning(f"✗ Document analysis failed: {doc_analysis.get('error')}")
            
            # Combine everything for LLM analysis
            if context_parts:
                enhanced_text = state["grievance_text"] + "".join(context_parts)
                logger.info(f"Enhanced grievance text with {len(context_parts)} additional sources")
            
            # Call understanding chain with FULL context
            analysis = await self.understanding_chain.analyze(enhanced_text)
            
            # Update state with analysis results
            state["summary"] = analysis.get("summary", "")
            state["category"] = analysis.get("category", "Others")
            state["department"] = analysis.get("department", "Municipal")
            state["priority"] = analysis.get("priority", "Medium")
            state["keywords"] = analysis.get("keywords", [])
            state["confidence_score"] = analysis.get("confidence_score", 0.5)
            state["explanation"] = analysis.get("explanation")
            state["status"] = GrievanceStatus.IN_REVIEW.value
            
            # Create auto-assignment
            state["assignment"] = {
                "assigned_by": "system",
                "assigned_by_name": "AI System",
                "assigned_to_department": state["department"],
                "assignment_type": "auto",
                "assigned_at": datetime.utcnow()
            }
            
            logger.info(f"✓ Analysis complete: {state['category']} → {state['department']} [{state['priority']}]")
            
        except Exception as e:
            logger.error(f"Error in analyze step: {e}", exc_info=True)
            state["error"] = str(e)
            state["status"] = GrievanceStatus.OPEN.value
        
        return state
    
    async def suggest_redressal(self, state: GrievanceState) -> GrievanceState:
        """
        Step 2: Generate redressal suggestions with similar cases
        """
        try:
            logger.info("Generating redressal suggestions")
            
            # Call redressal chain with keywords for RAG
            suggestions = await self.redressal_chain.suggest_actions(
                grievance_text=state["grievance_text"],
                summary=state["summary"],
                category=state["category"],
                department=state["department"],
                priority=state["priority"],
                keywords=state.get("keywords", [])  # Pass keywords for RAG
            )
            
            # Update state
            state["recommended_actions"] = suggestions.get("recommended_actions", [])
            state["escalation_needed"] = suggestions.get("escalation_needed", False)
            state["estimated_resolution_time"] = suggestions.get(
                "estimated_resolution_time", "7-10 days"
            )
            state["similar_cases"] = suggestions.get("similar_cases", [])  # NEW
            
            logger.info(f"Redressal suggestions generated with {len(state['similar_cases'])} similar cases")
            
        except Exception as e:
            logger.error(f"Error in redressal step: {e}")
            state["error"] = str(e)
        
        return state
    
    async def save_to_database(self, state: GrievanceState) -> GrievanceState:
        """
        Step 3: Save processed grievance to database
        ENHANCED: Saves ALL multi-modal data
        """
        try:
            logger.info(f"Saving to database: {state['grievance_id']}")
            
            collection = db.get_collection("grievances")
            
            grievance_doc = {
                "grievance_id": state["grievance_id"],
                "user_name": state.get("user_name"),
                "user_contact": state.get("user_contact"),
                "location": state.get("location"),
                "grievance_text": state["grievance_text"],
                "language": state["language"],
                
                # NEW: Save all multi-modal inputs
                "audio_transcription": state.get("audio_transcription"),
                "image_ocr": state.get("image_ocr"),
                "document_analysis": state.get("document_analysis"),
                
                # Analysis results
                "summary": state.get("summary"),
                "category": state.get("category"),
                "department": state.get("department"),
                "priority": state.get("priority"),
                "keywords": state.get("keywords", []),
                "confidence_score": state.get("confidence_score"),
                "explanation": state.get("explanation"),
                
                # Redressal
                "recommended_actions": state.get("recommended_actions", []),
                "escalation_needed": state.get("escalation_needed", False),
                "estimated_resolution_time": state.get("estimated_resolution_time"),
                "similar_cases": state.get("similar_cases", []),
                
                # Assignment
                "assignment": state.get("assignment"),
                "status": state.get("status", GrievanceStatus.IN_REVIEW.value),
                
                # Initialize addresser updates
                "addresser_updates": [],
                
                # Timestamps
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                
                # Processing logs with details
                "processing_logs": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "analyzed",
                        "actor": "system",
                        "details": self._generate_processing_summary(state)
                    }
                ]
            }
            
            await collection.insert_one(grievance_doc)
            logger.info("✓ Successfully saved to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}", exc_info=True)
            state["error"] = str(e)
        
        return state
    
    def _generate_processing_summary(self, state: GrievanceState) -> str:
        """Generate a summary of what was processed"""
        parts = ["LLM analysis completed"]
        
        # FIXED: Use 'or {}' to handle None values
        if (state.get("audio_transcription") or {}).get("success"):
            parts.append("audio transcribed")
        if (state.get("image_ocr") or {}).get("success"):
            parts.append("image OCR")
        if (state.get("document_analysis") or {}).get("success"):
            parts.append("document analyzed")
        
        return " with " + ", ".join(parts[1:]) if len(parts) > 1 else parts[0]
    
    async def process_grievance(
        self,
        grievance_text: str,
        language: str = "english",
        user_name: Optional[str] = None,
        user_contact: Optional[str] = None,
        location: Optional[str] = None,
        audio_transcription: Optional[Dict[str, Any]] = None,  # NEW
        image_ocr: Optional[Dict[str, Any]] = None,  # NEW
        document_analysis: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Process a complete grievance through the workflow
        
        Args:
            grievance_text: The grievance text
            language: Language of the grievance
            user_name: Name of the person
            user_contact: Contact information
            location: Location/district
            audio_transcription: Results from audio transcription
            image_ocr: Results from image OCR
            document_analysis: Results from document understanding
            
        Returns:
            Final state dictionary
        """
        try:
            grievance_id = f"GRV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            
            initial_state: GrievanceState = {
                "grievance_id": grievance_id,
                "grievance_text": grievance_text,
                "language": language,
                "user_name": user_name or "",
                "user_contact": user_contact or "",
                "location": location or "",
                
                # NEW: Multi-modal inputs
                "audio_transcription": audio_transcription,
                "image_ocr": image_ocr,
                "document_analysis": document_analysis,
                
                "summary": "",
                "category": "",
                "department": "",
                "priority": "Medium",
                "keywords": [],
                "confidence_score": 0.0,
                "explanation": None,
                "recommended_actions": [],
                "escalation_needed": False,
                "estimated_resolution_time": "",
                "similar_cases": [],
                "assignment": None,
                "status": GrievanceStatus.OPEN.value,
                "error": ""
            }
            
            logger.info(f"Starting workflow for {grievance_id}")
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info(f"✓ Workflow complete for {grievance_id}")
            return dict(final_state)
            
        except Exception as e:
            logger.error(f"Error in workflow: {e}", exc_info=True)
            raise


# Singleton instance
grievance_workflow = GrievanceWorkflow()