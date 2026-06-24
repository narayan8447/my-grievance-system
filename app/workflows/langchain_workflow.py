"""
LangChain-based Conversational Workflow for Grievance Submission
Alternative implementation to LangGraph - can be used as backup
Provides memory, context awareness, and multi-turn conversations
"""
import logging
from typing import TypedDict, Optional, Dict, List, Any
from datetime import datetime
from bson import ObjectId

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.services.llm_service import llm_service
from app.chains.understanding_chain import UnderstandingChain
from app.chains.redressal_chain import RedressalChain
from app.models.database import db, find_secretariat_by_location
from app.models.schemas import GrievanceStatus, Priority
from app.utils.helpers import calculate_sla_deadline, extract_district_code

logger = logging.getLogger(__name__)


class ConversationalGrievanceState(TypedDict):
    """State maintained across conversation"""
    # User info
    citizen_id: Optional[str]
    user_name: Optional[str]
    user_contact: Optional[str]
    
    # Conversation context
    conversation_stage: str  # greeting, collecting, location, confirming, complete
    messages_history: List[Dict[str, str]]
    
    # Collected information
    grievance_text: str
    language: str
    location_text: Optional[str]
    location_lat: Optional[float]
    location_lon: Optional[float]
    
    # Multimodal inputs
    audio_transcription: Optional[Dict[str, Any]]
    image_ocr: Optional[Dict[str, Any]]
    document_analysis: Optional[Dict[str, Any]]
    
    # Generated data
    grievance_id: Optional[str]
    ai_analysis: Optional[Dict[str, Any]]
    
    # Metadata
    created_at: datetime
    last_updated: datetime


class LangChainGrievanceWorkflow:
    """
    LangChain-based conversational workflow for grievance submission
    Alternative to LangGraph - uses memory and prompt engineering
    """
    
    def __init__(self):
        self.understanding_chain = UnderstandingChain(llm_service)
        self.redressal_chain = RedressalChain(llm_service)
        self.llm = llm_service.get_llm()
        
        # Conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize prompts
        self._init_prompts()
        
        # Conversation chain
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.greeting_prompt,
            verbose=True
        )
    
    def _init_prompts(self):
        """Initialize conversation prompts for different stages"""
        
        # Greeting prompt
        self.greeting_prompt = PromptTemplate(
            input_variables=["chat_history", "input"],
            template="""You are an AI assistant helping citizens submit grievances to the Andhra Pradesh government.

Your role:
- Be friendly, empathetic, and professional
- Help users describe their issues clearly
- Ask clarifying questions if needed
- Guide them through the submission process

Current conversation:
{chat_history}

User: {input}
Assistant: Let me help you submit your grievance. """
        )
        
        # Information collection prompt
        self.collection_prompt = PromptTemplate(
            input_variables=["chat_history", "input", "current_grievance"],
            template="""You are collecting information for a grievance submission.

Current grievance details collected:
{current_grievance}

Conversation history:
{chat_history}

User's latest message: {input}

Your task:
1. If the user is providing grievance details, acknowledge and ask if they have more to add
2. If details are sufficient (>30 words), ask for location information
3. If user is providing location, confirm and summarize
4. Be conversational and supportive

Response:"""
        )
        
        # Confirmation prompt
        self.confirmation_prompt = PromptTemplate(
            input_variables=["grievance_summary"],
            template="""Based on the conversation, here's the grievance summary:

{grievance_summary}

Please confirm:
- Type 'submit' to file this grievance
- Type 'edit' to make changes
- Type 'cancel' to start over

Your response:"""
        )
    
    async def start_conversation(self, citizen_id: Optional[str] = None, 
                                 user_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new grievance submission conversation
        
        Returns:
            Initial state and greeting message
        """
        state: ConversationalGrievanceState = {
            "citizen_id": citizen_id,
            "user_name": user_name,
            "user_contact": None,
            "conversation_stage": "greeting",
            "messages_history": [],
            "grievance_text": "",
            "language": "en",
            "location_text": None,
            "location_lat": None,
            "location_lon": None,
            "audio_transcription": None,
            "image_ocr": None,
            "document_analysis": None,
            "grievance_id": None,
            "ai_analysis": None,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
        
        greeting = self._generate_greeting(user_name)
        
        state["messages_history"].append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "state": state,
            "message": greeting,
            "stage": "greeting"
        }
    
    def _generate_greeting(self, user_name: Optional[str] = None) -> str:
        """Generate personalized greeting"""
        name_part = f", {user_name}" if user_name else ""
        
        return f"""👋 Hello{name_part}! I'm your AI Grievance Assistant.

I'll help you submit your complaint to the Andhra Pradesh government in a conversational way.

**You can:**
• Type your grievance in Telugu or English
• Upload images, audio, or documents
• I'll guide you through the process step-by-step

**Let's begin - please describe your issue:**"""
    
    async def process_message(self, state: ConversationalGrievanceState, 
                             user_message: str,
                             audio_file: Optional[Any] = None,
                             image_file: Optional[Any] = None,
                             document_file: Optional[Any] = None) -> Dict[str, Any]:
        """
        Process user message in the conversation
        
        Args:
            state: Current conversation state
            user_message: User's text message
            audio_file: Optional audio file
            image_file: Optional image file
            document_file: Optional document file
        
        Returns:
            Updated state and assistant response
        """
        try:
            # Process multimodal inputs if provided
            if audio_file:
                state["audio_transcription"] = await self._process_audio(audio_file)
                if state["audio_transcription"] and state["audio_transcription"].get("success"):
                    user_message += " " + state["audio_transcription"].get("text", "")
            
            if image_file:
                state["image_ocr"] = await self._process_image(image_file)
                if state["image_ocr"] and state["image_ocr"].get("success"):
                    user_message += " " + state["image_ocr"].get("text", "")
            
            if document_file:
                state["document_analysis"] = await self._process_document(document_file)
                if state["document_analysis"] and state["document_analysis"].get("success"):
                    user_message += " " + state["document_analysis"].get("extracted_text", "")
            
            # Add to history
            state["messages_history"].append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Process based on stage
            current_stage = state["conversation_stage"]
            
            if current_stage == "greeting":
                response, next_stage = await self._handle_greeting_stage(state, user_message)
            
            elif current_stage == "collecting":
                response, next_stage = await self._handle_collecting_stage(state, user_message)
            
            elif current_stage == "location":
                response, next_stage = await self._handle_location_stage(state, user_message)
            
            elif current_stage == "confirming":
                response, next_stage = await self._handle_confirming_stage(state, user_message)
            
            elif current_stage == "complete":
                response, next_stage = await self._handle_complete_stage(state, user_message)
            
            else:
                response = "I'm not sure what to do. Let's start over."
                next_stage = "greeting"
            
            # Update state
            state["conversation_stage"] = next_stage
            state["last_updated"] = datetime.utcnow()
            
            state["messages_history"].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "state": state,
                "message": response,
                "stage": next_stage
            }
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "state": state,
                "message": f"I encountered an error: {str(e)}. Let's try again.",
                "stage": state["conversation_stage"]
            }
    
    async def _handle_greeting_stage(self, state: ConversationalGrievanceState, 
                                    message: str) -> tuple[str, str]:
        """Handle greeting stage - transition to collecting"""
        state["conversation_stage"] = "collecting"
        state["grievance_text"] = message
        
        if len(message) < 20:
            return (
                "I see you've started describing your issue. Please provide more details so I can help you better.",
                "collecting"
            )
        
        return (
            f"Thank you for sharing that. I understand you're facing: \"{message[:100]}...\"\n\n"
            "Please continue with any additional details or context.",
            "collecting"
        )
    
    async def _handle_collecting_stage(self, state: ConversationalGrievanceState,
                                      message: str) -> tuple[str, str]:
        """Handle information collection stage"""
        # Append to grievance text
        state["grievance_text"] += " " + message
        
        # Check if we have enough information
        if len(state["grievance_text"]) >= 50:
            # Move to location stage
            return (
                "✅ Thank you for the detailed information.\n\n"
                "📍 **Where is this issue located?**\n"
                "You can provide:\n"
                "- Ward/Village name\n"
                "- District\n"
                "- Street/landmark\n\n"
                "Or type 'skip' if location is not applicable.",
                "location"
            )
        else:
            return (
                "I've noted that. Please continue with more details about your issue.",
                "collecting"
            )
    
    async def _handle_location_stage(self, state: ConversationalGrievanceState,
                                    message: str) -> tuple[str, str]:
        """Handle location collection stage"""
        if message.lower() not in ["skip", "no", "n/a", "not applicable"]:
            state["location_text"] = message
        
        # Generate summary
        summary = await self._generate_summary(state)
        
        return (
            f"""📋 **Here's a summary of your grievance:**

**Issue Description:**
{state['grievance_text'][:300]}...

**Location:** {state['location_text'] or 'Not provided'}

**Attachments:**
{self._format_attachments(state)}

---

**Is this correct?**
- Type **'submit'** to file your grievance
- Type **'edit'** to make changes
- Type **'cancel'** to start over""",
            "confirming"
        )
    
    async def _handle_confirming_stage(self, state: ConversationalGrievanceState,
                                      message: str) -> tuple[str, str]:
        """Handle confirmation stage"""
        message_lower = message.lower().strip()
        
        if message_lower == "cancel":
            # Reset state
            return (
                "❌ Grievance cancelled. Type 'new' or 'start' to begin again.",
                "complete"
            )
        
        elif message_lower == "edit":
            return (
                "What would you like to change? Please describe your grievance again.",
                "collecting"
            )
        
        elif message_lower == "submit":
            # Submit grievance
            result = await self._submit_grievance(state)
            
            if result.get("success"):
                grievance_id = result.get("grievance_id")
                state["grievance_id"] = grievance_id
                
                return (
                    f"""🎉 **Your grievance has been submitted successfully!**

📋 **Grievance ID:** `{grievance_id}`

**Status:** Submitted
**Priority:** {result.get('priority', 'Medium')}
**Category:** {result.get('category', 'N/A')}
**Department:** {result.get('department', 'N/A')}

💡 **Please save this ID to track your complaint.**

---

Type **'new'** to submit another grievance.""",
                    "complete"
                )
            else:
                return (
                    f"❌ Submission failed: {result.get('error', 'Unknown error')}\n\n"
                    "Type 'retry' to try again or 'cancel' to start over.",
                    "confirming"
                )
        
        else:
            return (
                "Please type:\n"
                "- **'submit'** to confirm\n"
                "- **'edit'** to make changes\n"
                "- **'cancel'** to start over",
                "confirming"
            )
    
    async def _handle_complete_stage(self, state: ConversationalGrievanceState,
                                    message: str) -> tuple[str, str]:
        """Handle completion stage"""
        if message.lower() in ["new", "start", "begin"]:
            # Start new conversation (caller should reset state)
            return (
                self._generate_greeting(state.get("user_name")),
                "greeting"
            )
        
        return (
            "Your previous grievance was submitted.\n\n"
            "Type **'new'** to submit another grievance.",
            "complete"
        )
    
    async def _generate_summary(self, state: ConversationalGrievanceState) -> str:
        """Generate AI summary of the grievance"""
        try:
            summary_prompt = f"""Summarize this grievance in 2-3 sentences:

Grievance: {state['grievance_text']}

Summary:"""
            
            llm = llm_service.get_llm()
            summary = await llm.ainvoke(summary_prompt)
            
            return summary.content if hasattr(summary, 'content') else str(summary)
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return state['grievance_text'][:200] + "..."
    
    def _format_attachments(self, state: ConversationalGrievanceState) -> str:
        """Format attachment information"""
        attachments = []
        
        if state.get("audio_transcription"):
            attachments.append("🎤 Audio recording")
        if state.get("image_ocr"):
            attachments.append("📷 Image")
        if state.get("document_analysis"):
            attachments.append("📄 Document")
        
        return "\n".join([f"- {a}" for a in attachments]) if attachments else "None"
    
    async def _submit_grievance(self, state: ConversationalGrievanceState) -> Dict[str, Any]:
        """
        Submit the grievance to database
        Similar to LangGraph workflow but streamlined
        """
        try:
            # Step 1: Analyze with AI
            analysis = await self.understanding_chain.analyze(
                grievance_text=state["grievance_text"],
                audio_transcription=state.get("audio_transcription", {}).get("text") if state.get("audio_transcription") else None,
                image_ocr_text=state.get("image_ocr", {}).get("text") if state.get("image_ocr") else None,
                document_text=state.get("document_analysis", {}).get("extracted_text") if state.get("document_analysis") else None
            )
            
            state["ai_analysis"] = analysis
            
            # Step 2: Geospatial routing (if location provided)
            secretariat_id = None
            location_details = None
            department_id = "GEN_ADMIN"
            
            if state.get("location_lat") and state.get("location_lon"):
                secretariat = await find_secretariat_by_location(
                    state["location_lon"],
                    state["location_lat"]
                )
                
                if secretariat:
                    secretariat_id = secretariat["unit_id"]
                    department_id = secretariat["unit_id"]
                    
                    location_details = {
                        "secretariat_name": secretariat["name_english"],
                        "mandal": None,
                        "district": None
                    }
            
            # Step 3: Generate grievance ID
            district_code = extract_district_code(state.get("location_lat"), state.get("location_lon")) if state.get("location_lat") else "TMP"
            grievance_id = await db.generate_grievance_id(district_code)
            
            # Step 4: Calculate SLA
            priority = analysis.get("priority_suggestion", "Medium")
            sla_due_date = calculate_sla_deadline(priority)
            
            # Step 5: Get redressal suggestions
            suggestions = await self.redressal_chain.suggest_actions(
                grievance_text=state["grievance_text"],
                summary=analysis.get("summary", ""),
                category=analysis.get("predicted_category", "Others"),
                department=analysis.get("department_suggestion", "General"),
                priority=priority,
                keywords=analysis.get("keywords", []),
                location_details=location_details
            )
            
            # Step 6: Build grievance document
            grievance_doc = {
                "grievance_id": grievance_id,
                "citizen_id": state.get("citizen_id"),
                "title": analysis.get("summary", "")[:100],
                
                "input_data": {
                    "original_text": state["grievance_text"],
                    "voice_url": None,
                    "image_urls": []
                },
                
                "ai_analysis": analysis,
                
                "location": {
                    "geo": {
                        "type": "Point",
                        "coordinates": [state.get("location_lon", 0), state.get("location_lat", 0)]
                    } if state.get("location_lat") else None,
                    "secretariat_id": secretariat_id or "UNKNOWN",
                    "details": location_details
                } if state.get("location_lat") else None,
                
                "department_id": department_id,
                "assigned_to": None,
                "priority": priority,
                "status": GrievanceStatus.SUBMITTED.value,
                "sla_due_date": sla_due_date,
                "attachments": [],
                "document_analysis": state.get("document_analysis"),
                "history": [],
                "assignment_history": [],
                "duplicate_of_id": None,
                "similar_cases": suggestions.get("similar_cases", []),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "resolved_at": None,
                "processing_logs": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "created",
                        "actor": "langchain_workflow",
                        "details": f"Conversational submission via LangChain"
                    }
                ]
            }
            
            # Step 7: Insert into database
            await db.grievances().insert_one(grievance_doc)
            
            logger.info(f"✅ Grievance submitted via LangChain: {grievance_id}")
            
            return {
                "success": True,
                "grievance_id": grievance_id,
                "priority": priority,
                "category": analysis.get("predicted_category", "N/A"),
                "department": department_id
            }
        
        except Exception as e:
            logger.error(f"❌ Submission error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_audio(self, audio_file: Any) -> Optional[Dict[str, Any]]:
        """Process audio file (placeholder - integrate with audio_service)"""
        # TODO: Integrate with app.services.audio_service
        return {
            "success": True,
            "text": "[Audio transcription would be here]",
            "language": "en",
            "confidence": 0.8
        }
    
    async def _process_image(self, image_file: Any) -> Optional[Dict[str, Any]]:
        """Process image file (placeholder - integrate with image_service)"""
        # TODO: Integrate with app.services.image_service
        return {
            "success": True,
            "text": "[Image OCR text would be here]",
            "confidence": 0.75
        }
    
    async def _process_document(self, document_file: Any) -> Optional[Dict[str, Any]]:
        """Process document file (placeholder - integrate with document_service)"""
        # TODO: Integrate with app.services.document_service
        return {
            "success": True,
            "extracted_text": "[Document text would be here]",
            "document_type": "complaint_letter",
            "key_entities": {},
            "confidence": 0.8
        }


# Singleton instance for LangChain workflow
langchain_workflow = LangChainGrievanceWorkflow()


# ===== USAGE EXAMPLE =====
"""
# Start conversation
result = await langchain_workflow.start_conversation(
    citizen_id="citizen_123",
    user_name="Ramesh Kumar"
)

state = result["state"]
print(result["message"])  # Show greeting to user

# Process user messages
while state["conversation_stage"] != "complete":
    user_input = input("You: ")
    
    result = await langchain_workflow.process_message(
        state=state,
        user_message=user_input
    )
    
    state = result["state"]
    print(f"Assistant: {result['message']}")
    
    if result["stage"] == "complete":
        break
"""