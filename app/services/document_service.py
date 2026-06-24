"""Document processing service with AI-powered entity extraction"""
import logging
from typing import Optional, Dict, Any
import re
from io import BytesIO

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for processing documents with OCR and entity extraction"""
    
    def __init__(self):
        self.supported_formats = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png']
    
    async def analyze_document(
        self,
        document_bytes: bytes,
        file_extension: str,
        context_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document: extract text + entities
        
        Args:
            document_bytes: Document file bytes
            file_extension: File extension (pdf, docx, jpg, etc.)
            context_text: Optional context for better understanding
            
        Returns:
            Dictionary with extracted text and entities
        """
        try:
            logger.info(f"📄 Analyzing {file_extension} document ({len(document_bytes)} bytes)")
            
            # Step 1: Extract raw text based on file type
            extracted_text = await self._extract_text(document_bytes, file_extension)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                logger.warning("⚠️ No meaningful text extracted from document")
                return {
                    "success": False,
                    "error": "No text could be extracted from document",
                    "extracted_text": "",
                    "key_entities": self._empty_entities(),
                    "document_type": "unknown",
                    "confidence": 0.0
                }
            
            logger.info(f"✅ Extracted {len(extracted_text)} characters from document")
            
            # Step 2: Extract entities using LLM
            key_entities = await self._extract_entities_with_llm(extracted_text)
            
            # Step 3: Classify document type
            document_type = await self._classify_document_type(extracted_text, context_text)
            
            # Step 4: Calculate confidence
            confidence = self._calculate_confidence(extracted_text, key_entities)
            
            return {
                "success": True,
                "extracted_text": extracted_text,
                "key_entities": key_entities,
                "document_type": document_type,
                "confidence": confidence,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing document: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "extracted_text": "",
                "key_entities": self._empty_entities(),
                "document_type": "unknown",
                "confidence": 0.0
            }
    
    async def _extract_text(self, document_bytes: bytes, file_extension: str) -> str:
        """Extract text from document based on file type"""
        file_ext = file_extension.lower()
        
        # Images (JPG, PNG) - Use OCR
        if file_ext in ['jpg', 'jpeg', 'png', 'webp']:
            return await self._extract_text_from_image(document_bytes)
        
        # PDF
        elif file_ext == 'pdf':
            return await self._extract_text_from_pdf(document_bytes)
        
        # Word documents
        elif file_ext in ['doc', 'docx']:
            return await self._extract_text_from_word(document_bytes)
        
        # Plain text
        elif file_ext == 'txt':
            return document_bytes.decode('utf-8', errors='ignore')
        
        else:
            logger.warning(f"Unsupported file format: {file_ext}")
            return ""
    
    async def _extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract with Telugu + English
            text = pytesseract.image_to_string(
                image,
                lang='tel+eng',
                config='--psm 6 --oem 3'
            )
            
            return text.strip()
            
        except ImportError:
            logger.error("❌ pytesseract not installed")
            return ""
        except Exception as e:
            logger.error(f"❌ Image OCR error: {e}")
            return ""
    
    async def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
            
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except ImportError:
            logger.error("❌ PyPDF2 not installed. Run: pip install PyPDF2")
            return ""
        except Exception as e:
            logger.error(f"❌ PDF extraction error: {e}")
            return ""
    
    async def _extract_text_from_word(self, doc_bytes: bytes) -> str:
        """Extract text from Word document"""
        try:
            import docx
            
            doc_file = BytesIO(doc_bytes)
            document = docx.Document(doc_file)
            
            text = "\n".join([paragraph.text for paragraph in document.paragraphs])
            
            return text.strip()
            
        except ImportError:
            logger.error("❌ python-docx not installed. Run: pip install python-docx")
            return ""
        except Exception as e:
            logger.error(f"❌ Word extraction error: {e}")
            return ""
    
    async def _extract_entities_with_llm(self, text: str) -> Dict[str, list]:
        """
        ✅ USE LLM TO EXTRACT ENTITIES (dates, amounts, locations, people, organizations)
        """
        try:
            from app.services.llm_service import llm_service
            
            # Limit text length for LLM
            text_sample = text[:2000] if len(text) > 2000 else text
            
            system_prompt = """You are an entity extraction AI. Extract key information from the given text.

Extract and return ONLY a valid JSON object with these fields:
{
    "dates": ["date1", "date2"],
    "amounts": ["₹1000", "$500"],
    "locations": ["location1", "location2"],
    "people": ["name1", "name2"],
    "organizations": ["org1", "org2"]
}

Rules:
- Return ONLY the JSON, no other text
- If no entities found for a category, use empty array []
- Extract dates in any format mentioned
- Extract monetary amounts with currency symbols
- Extract place names, addresses, districts
- Extract person names mentioned
- Extract company/organization/department names"""

            user_prompt = f"""Extract entities from this text:

{text_sample}

Return ONLY the JSON object."""

            logger.info("🤖 Calling LLM for entity extraction...")
            
            # Call LLM
            response = await llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            # Parse JSON response
            import json
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                entities = json.loads(json_str)
                
                logger.info(f"✅ LLM extracted entities: {sum(len(v) for v in entities.values())} total")
                
                # Ensure all required keys exist
                return {
                    "dates": entities.get("dates", []),
                    "amounts": entities.get("amounts", []),
                    "locations": entities.get("locations", []),
                    "people": entities.get("people", []),
                    "organizations": entities.get("organizations", [])
                }
            else:
                logger.warning("⚠️ LLM response not valid JSON, falling back to regex")
                return self._extract_entities_with_regex(text)
            
        except Exception as e:
            logger.error(f"❌ LLM entity extraction failed: {e}")
            # Fallback to regex-based extraction
            return self._extract_entities_with_regex(text)
    
    def _extract_entities_with_regex(self, text: str) -> Dict[str, list]:
        """
        Fallback: Extract entities using regex patterns
        """
        entities = {
            "dates": [],
            "amounts": [],
            "locations": [],
            "people": [],
            "organizations": []
        }
        
        # Extract dates (various formats)
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD-MM-YYYY, DD/MM/YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY-MM-DD
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # 15 Jan 2024
        ]
        for pattern in date_patterns:
            entities["dates"].extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Extract amounts (currency)
        amount_patterns = [
            r'₹\s*\d+(?:,\d+)*(?:\.\d+)?',  # ₹1,000 or ₹1000.50
            r'Rs\.?\s*\d+(?:,\d+)*',         # Rs. 1000
            r'\$\s*\d+(?:,\d+)*(?:\.\d+)?',  # $500
        ]
        for pattern in amount_patterns:
            entities["amounts"].extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Extract locations (basic - can be improved)
        # Look for common location keywords
        location_keywords = ['district', 'village', 'mandal', 'city', 'town', 'ward', 'area']
        for keyword in location_keywords:
            pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+' + keyword
            entities["locations"].extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))[:5]  # Max 5 per category
        
        logger.info(f"✅ Regex extracted: {sum(len(v) for v in entities.values())} entities")
        
        return entities
    
    async def _classify_document_type(
        self,
        text: str,
        context_text: Optional[str] = None
    ) -> str:
        """
        Classify document type using keywords
        """
        text_lower = text.lower()
        
        # Check for complaint indicators
        complaint_keywords = ['complaint', 'grievance', 'issue', 'problem', 'damage', 'broken']
        if any(kw in text_lower for kw in complaint_keywords):
            return "complaint_letter"
        
        # Check for application indicators
        application_keywords = ['application', 'request', 'apply', 'seeking', 'kindly']
        if any(kw in text_lower for kw in application_keywords):
            return "application"
        
        # Check for official document indicators
        official_keywords = ['subject:', 'ref:', 'date:', 'to whom', 'sir/madam']
        if any(kw in text_lower for kw in official_keywords):
            return "official_document"
        
        return "other"
    
    def _calculate_confidence(self, text: str, entities: Dict[str, list]) -> float:
        """
        Calculate confidence score based on text quality and entities
        """
        confidence = 0.5  # Base confidence
        
        # More text = higher confidence
        if len(text) > 100:
            confidence += 0.2
        if len(text) > 500:
            confidence += 0.1
        
        # More entities = higher confidence
        total_entities = sum(len(v) for v in entities.values())
        if total_entities > 0:
            confidence += 0.1
        if total_entities > 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _empty_entities(self) -> Dict[str, list]:
        """Return empty entities structure"""
        return {
            "dates": [],
            "amounts": [],
            "locations": [],
            "people": [],
            "organizations": []
        }


# Singleton instance
document_service = DocumentService()