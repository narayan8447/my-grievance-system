"""Image processing service for grievances - ENHANCED with robust OCR"""
import logging
import base64
import asyncio
from io import BytesIO
from PIL import Image
from typing import Optional, Dict, Any

# 🪟 WINDOWS FIX: Configure Tesseract path
import platform
if platform.system() == 'Windows':
    try:
        import pytesseract
        # Configure Tesseract path for Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        logging.getLogger(__name__).info("✅ Windows: Tesseract path configured to C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
    except ImportError:
        logging.getLogger(__name__).warning("⚠️ pytesseract not installed. Run: pip install pytesseract")
    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Error configuring Tesseract: {e}")

logger = logging.getLogger(__name__)


class ImageService:
    """Service for processing grievance images with OCR support"""
    
    def __init__(self):
        self.max_size = (1024, 1024)
        self.supported_formats = ['JPEG', 'PNG', 'JPG', 'WEBP']
        self._tesseract_checked = False
        self._tesseract_available = False
        self._tesseract_langs = []
    
    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process uploaded image: validate, resize, convert
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with processed image info
        """
        try:
            image = Image.open(BytesIO(image_data))
            
            if image.format not in self.supported_formats:
                raise ValueError(f"Unsupported format: {image.format}")
            
            if image.size[0] > self.max_size[0] or image.size[1] > self.max_size[1]:
                image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 Resized image to {image.size}")
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            output = BytesIO()
            image.save(output, format='JPEG', quality=85)
            processed_data = output.getvalue()
            
            base64_image = base64.b64encode(processed_data).decode('utf-8')
            
            return {
                "success": True,
                "format": "JPEG",
                "size": image.size,
                "base64_data": base64_image,
                "file_size": len(processed_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_text_from_image(self, image_data: bytes) -> Optional[str]:
        """
        Extract text from image using OCR with multiple fallback strategies
        
        Priority Order:
        1. Tesseract OCR (local, fast, supports Telugu)
        2. Document Service fallback (if Tesseract unavailable)
        
        Args:
            image_data: Image bytes
            
        Returns:
            Extracted text string or None if no text found
        """
        logger.info("=" * 60)
        logger.info("🔍 STARTING IMAGE OCR EXTRACTION")
        logger.info("=" * 60)
        
        try:
            # Strategy 1: Try Tesseract OCR first
            if self._check_tesseract_available():
                logger.info("✅ Tesseract is available - attempting OCR")
                text = await self._ocr_with_tesseract(image_data)
                
                if text and len(text.strip()) > 5:
                    logger.info(f"✅ SUCCESS: Tesseract extracted {len(text)} characters")
                    logger.info(f"📝 Text preview: '{text[:100]}...'")
                    logger.info("=" * 60)
                    return text.strip()
                else:
                    logger.warning("⚠️ Tesseract completed but found no meaningful text")
            else:
                logger.warning("⚠️ Tesseract OCR not available")
                self._print_tesseract_install_instructions()
            
            # Strategy 2: Fallback to document_service
            logger.info("🔄 Attempting document_service fallback for OCR...")
            try:
                from app.services.document_service import document_service
                
                result = await document_service.analyze_document(
                    document_bytes=image_data,
                    file_extension='jpg',
                    context_text=None
                )
                
                if result.get('success'):
                    extracted_text = result.get('extracted_text', '')
                    if extracted_text and len(extracted_text.strip()) > 5:
                        logger.info(f"✅ SUCCESS: Document service extracted {len(extracted_text)} chars")
                        logger.info("=" * 60)
                        return extracted_text.strip()
                    else:
                        logger.warning("⚠️ Document service returned no meaningful text")
                else:
                    logger.warning(f"⚠️ Document service failed: {result.get('error')}")
                    
            except ImportError:
                logger.warning("⚠️ Document service not available for fallback")
            except Exception as e:
                logger.warning(f"⚠️ Document service error: {e}")
            
            # All strategies failed
            logger.warning("❌ All OCR strategies failed - no text extracted")
            logger.info("=" * 60)
            return None
            
        except Exception as e:
            logger.error(f"❌ Critical error in OCR pipeline: {e}", exc_info=True)
            logger.info("=" * 60)
            return None
    
    def _check_tesseract_available(self) -> bool:
        """
        Check if Tesseract OCR is installed and available (cached)
        
        Returns:
            True if Tesseract is available
        """
        if self._tesseract_checked:
            return self._tesseract_available
        
        self._tesseract_checked = True
        
        try:
            import pytesseract
            
            # Test by getting version
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract version: {version}")
            
            # Check available languages
            try:
                self._tesseract_langs = pytesseract.get_languages()
                logger.info(f"📚 Available languages: {', '.join(self._tesseract_langs)}")
                
                if 'tel' in self._tesseract_langs:
                    logger.info("✅ Telugu language pack detected")
                else:
                    logger.warning("⚠️ Telugu language pack not found")
                    logger.warning("   Windows: Re-run Tesseract installer and select Telugu")
                
                if 'eng' not in self._tesseract_langs:
                    logger.warning("⚠️ English language pack not found (unusual)")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not enumerate languages: {e}")
            
            self._tesseract_available = True
            return True
            
        except ImportError:
            logger.warning("⚠️ pytesseract package not installed")
            logger.warning("   Install: pip install pytesseract")
            self._tesseract_available = False
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Tesseract binary not found: {e}")
            if platform.system() == 'Windows':
                logger.warning("   Windows: Check if Tesseract is installed in C:\\Program Files\\Tesseract-OCR")
                logger.warning("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            self._tesseract_available = False
            return False
    
    async def _ocr_with_tesseract(self, image_data: bytes) -> Optional[str]:
        """
        Extract text using Tesseract OCR with preprocessing and multiple strategies
        
        Args:
            image_data: Image bytes
            
        Returns:
            Extracted text or None
        """
        try:
            import pytesseract
            from PIL import Image, ImageEnhance, ImageFilter
            
            logger.info("🖼️ Loading image for OCR...")
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.info("🎨 Converted to RGB")
            
            # Preprocessing for better OCR
            logger.info("🔧 Preprocessing image...")
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Increase sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            logger.info("✅ Preprocessing complete")
            
            # Strategy 1: Try Telugu + English (for bilingual documents)
            if 'tel' in self._tesseract_langs and 'eng' in self._tesseract_langs:
                logger.info("🔤 Attempting OCR: Telugu + English")
                try:
                    text = await asyncio.to_thread(
                        pytesseract.image_to_string,
                        image,
                        lang='tel+eng',
                        config='--psm 6 --oem 3'  # PSM 6: uniform block, OEM 3: LSTM
                    )
                    
                    if text and len(text.strip()) > 10:
                        logger.info(f"✅ Telugu+English: {len(text)} chars extracted")
                        return text.strip()
                    else:
                        logger.info("⚠️ Telugu+English: minimal text")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Telugu+English failed: {e}")
            
            # Strategy 2: English only
            if 'eng' in self._tesseract_langs:
                logger.info("🔤 Attempting OCR: English only")
                try:
                    text = await asyncio.to_thread(
                        pytesseract.image_to_string,
                        image,
                        lang='eng',
                        config='--psm 6 --oem 3'
                    )
                    
                    if text and len(text.strip()) > 5:
                        logger.info(f"✅ English: {len(text)} chars extracted")
                        return text.strip()
                    else:
                        logger.info("⚠️ English: minimal text")
                        
                except Exception as e:
                    logger.warning(f"⚠️ English failed: {e}")
            
            # Strategy 3: Telugu only
            if 'tel' in self._tesseract_langs:
                logger.info("🔤 Attempting OCR: Telugu only")
                try:
                    text = await asyncio.to_thread(
                        pytesseract.image_to_string,
                        image,
                        lang='tel',
                        config='--psm 6 --oem 3'
                    )
                    
                    if text and len(text.strip()) > 5:
                        logger.info(f"✅ Telugu: {len(text)} chars extracted")
                        return text.strip()
                    else:
                        logger.info("⚠️ Telugu: minimal text")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Telugu failed: {e}")
            
            # Strategy 4: Auto-detect language (fallback)
            logger.info("🔤 Attempting OCR: Auto-detect")
            try:
                text = await asyncio.to_thread(
                    pytesseract.image_to_string,
                    image,
                    config='--psm 6 --oem 3'
                )
                
                if text and len(text.strip()) > 5:
                    logger.info(f"✅ Auto-detect: {len(text)} chars extracted")
                    return text.strip()
                else:
                    logger.info("⚠️ Auto-detect: minimal text")
                    
            except Exception as e:
                logger.warning(f"⚠️ Auto-detect failed: {e}")
            
            logger.warning("❌ All Tesseract strategies returned no meaningful text")
            return None
            
        except ImportError:
            logger.error("❌ pytesseract not installed")
            return None
        except Exception as e:
            logger.error(f"❌ Tesseract OCR error: {e}", exc_info=True)
            return None
    
    def _print_tesseract_install_instructions(self):
        """Print helpful installation instructions for Tesseract"""
        logger.info("")
        logger.info("📋 TESSERACT INSTALLATION INSTRUCTIONS:")
        logger.info("=" * 60)
        
        if platform.system() == 'Windows':
            logger.info("🪟 Windows:")
            logger.info("  1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            logger.info("  2. Run installer (tesseract-ocr-w64-setup-*.exe)")
            logger.info("  3. During installation, select 'Telugu' language pack")
            logger.info("  4. Install to: C:\\Program Files\\Tesseract-OCR")
            logger.info("  5. Run: pip install pytesseract")
        else:
            logger.info("Ubuntu/Debian:")
            logger.info("  sudo apt-get update")
            logger.info("  sudo apt-get install tesseract-ocr tesseract-ocr-tel")
            logger.info("")
            logger.info("macOS:")
            logger.info("  brew install tesseract tesseract-lang")
        
        logger.info("")
        logger.info("Python package:")
        logger.info("  pip install pytesseract")
        logger.info("=" * 60)
        logger.info("")
    
    def get_supported_ocr_languages(self) -> list:
        """
        Get list of languages supported by installed Tesseract
        
        Returns:
            List of language codes
        """
        if not self._check_tesseract_available():
            return []
        
        return self._tesseract_langs
    
    def get_ocr_status(self) -> Dict[str, Any]:
        """
        Get current OCR capability status
        
        Returns:
            Status dictionary
        """
        available = self._check_tesseract_available()
        
        return {
            "tesseract_available": available,
            "languages_supported": self._tesseract_langs if available else [],
            "telugu_supported": 'tel' in self._tesseract_langs if available else False,
            "english_supported": 'eng' in self._tesseract_langs if available else False,
            "fallback_available": True  # document_service fallback
        }


# Singleton instance
image_service = ImageService()