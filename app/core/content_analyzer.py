# ============================================
# FILE: app/core/content_analyzer.py (NEW)
# Content-based analysis with OCR and metadata
# ============================================

"""Content-based file analysis including OCR and metadata extraction"""
import logging
from pathlib import Path
from typing import Dict, Optional, List
import mimetypes

logger = logging.getLogger("FileOrganizer")


class ContentAnalyzer:
    """Analyze file content for better classification"""
    
    def __init__(self):
        self.ocr_enabled = False
        self.metadata_enabled = True
        self._init_dependencies()
    
    def _init_dependencies(self):
        """Initialize optional dependencies"""
        # Try to import OCR library
        try:
            import pytesseract
            from PIL import Image
            self.ocr_enabled = True
            logger.info("OCR enabled (Tesseract found)")
        except ImportError:
            logger.info("OCR disabled (pytesseract not installed)")
        
        # Try to import metadata libraries
        try:
            from PIL import Image
            import PyPDF2
            self.metadata_enabled = True
            logger.info("Metadata extraction enabled")
        except ImportError:
            logger.warning("Some metadata libraries not available")
    
    def analyze_file(self, file_path: Path) -> Dict:
        """
        Analyze file content and extract information
        Returns dict with: content_text, metadata, keywords, suggested_category
        """
        result = {
            "content_text": "",
            "metadata": {},
            "keywords": [],
            "suggested_category": None,
            "confidence": 0.0
        }
        
        try:
            file_type = self._get_file_type(file_path)
            
            if file_type == "image":
                result.update(self._analyze_image(file_path))
            elif file_type == "pdf":
                result.update(self._analyze_pdf(file_path))
            elif file_type == "document":
                result.update(self._analyze_document(file_path))
            elif file_type == "audio":
                result.update(self._analyze_audio(file_path))
            elif file_type == "video":
                result.update(self._analyze_video(file_path))
            
            # Extract keywords from content
            if result["content_text"]:
                result["keywords"] = self._extract_keywords(result["content_text"])
                result["suggested_category"] = self._suggest_category(result)
            
        except Exception as e:
            logger.error(f"Content analysis failed for {file_path.name}: {e}")
        
        return result
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type"""
        ext = file_path.suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            return "image"
        elif ext == '.pdf':
            return "pdf"
        elif ext in ['.docx', '.doc', '.txt', '.odt']:
            return "document"
        elif ext in ['.mp3', '.wav', '.flac', '.m4a']:
            return "audio"
        elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
            return "video"
        else:
            return "unknown"
    
    def _analyze_image(self, file_path: Path) -> Dict:
        """Analyze image file"""
        result = {"metadata": {}, "content_text": ""}
        
        try:
            from PIL import Image
            import PIL.ExifTags
            
            with Image.open(file_path) as img:
                # Basic metadata
                result["metadata"].update({
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                })
                
                # EXIF data
                exif_data = img._getexif()
                if exif_data:
                    exif = {
                        PIL.ExifTags.TAGS.get(k, k): v
                        for k, v in exif_data.items()
                        if k in PIL.ExifTags.TAGS
                    }
                    
                    # Extract useful EXIF fields
                    if "DateTime" in exif:
                        result["metadata"]["date_taken"] = exif["DateTime"]
                    if "Make" in exif:
                        result["metadata"]["camera_make"] = exif["Make"]
                    if "Model" in exif:
                        result["metadata"]["camera_model"] = exif["Model"]
                    if "GPSInfo" in exif:
                        result["metadata"]["has_gps"] = True
                
                # OCR if enabled
                if self.ocr_enabled:
                    result["content_text"] = self._ocr_image(file_path)
        
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
        
        return result
    
    def _ocr_image(self, file_path: Path) -> str:
        """Perform OCR on image"""
        try:
            import pytesseract
            from PIL import Image
            
            with Image.open(file_path) as img:
                text = pytesseract.image_to_string(img)
                return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def _analyze_pdf(self, file_path: Path) -> Dict:
        """Analyze PDF file"""
        result = {"metadata": {}, "content_text": ""}
        
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                
                # Metadata
                if pdf.metadata:
                    result["metadata"] = {
                        "title": pdf.metadata.get('/Title', ''),
                        "author": pdf.metadata.get('/Author', ''),
                        "subject": pdf.metadata.get('/Subject', ''),
                        "creator": pdf.metadata.get('/Creator', ''),
                        "pages": len(pdf.pages)
                    }
                
                # Extract text from first few pages
                text_parts = []
                for page_num in range(min(3, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    text_parts.append(page.extract_text())
                
                result["content_text"] = " ".join(text_parts)[:2000]  # Limit size
        
        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
        
        return result
    
    def _analyze_document(self, file_path: Path) -> Dict:
        """Analyze document file"""
        result = {"metadata": {}, "content_text": ""}
        
        try:
            if file_path.suffix.lower() == '.txt':
                # Plain text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    result["content_text"] = f.read(2000)  # First 2000 chars
            
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                # Word document
                try:
                    import docx
                    doc = docx.Document(file_path)
                    
                    # Metadata
                    core_props = doc.core_properties
                    result["metadata"] = {
                        "title": core_props.title or "",
                        "author": core_props.author or "",
                        "created": str(core_props.created) if core_props.created else ""
                    }
                    
                    # Extract text
                    text_parts = [para.text for para in doc.paragraphs[:20]]
                    result["content_text"] = " ".join(text_parts)[:2000]
                
                except ImportError:
                    logger.warning("python-docx not installed")
        
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
        
        return result
    
    def _analyze_audio(self, file_path: Path) -> Dict:
        """Analyze audio file metadata"""
        result = {"metadata": {}}
        
        try:
            from mutagen import File
            
            audio = File(file_path)
            if audio:
                result["metadata"] = {
                    "duration": getattr(audio.info, 'length', 0),
                    "bitrate": getattr(audio.info, 'bitrate', 0),
                    "sample_rate": getattr(audio.info, 'sample_rate', 0)
                }
                
                # ID3 tags
                if hasattr(audio, 'tags') and audio.tags:
                    tags = audio.tags
                    result["metadata"]["title"] = str(tags.get('TIT2', [''])[0])
                    result["metadata"]["artist"] = str(tags.get('TPE1', [''])[0])
                    result["metadata"]["album"] = str(tags.get('TALB', [''])[0])
                    result["metadata"]["genre"] = str(tags.get('TCON', [''])[0])
        
        except ImportError:
            logger.warning("mutagen not installed for audio metadata")
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
        
        return result
    
    def _analyze_video(self, file_path: Path) -> Dict:
        """Analyze video file metadata"""
        result = {"metadata": {}}
        
        try:
            # Basic file info
            result["metadata"]["size_mb"] = file_path.stat().st_size / (1024 * 1024)
        
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
        
        return result
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        if not text:
            return []
        
        # Simple keyword extraction
        keywords = []
        
        # Financial keywords
        financial_terms = ['invoice', 'receipt', 'payment', 'bill', 'tax', 
                          'expense', 'salary', 'payroll', 'budget']
        # Work keywords
        work_terms = ['report', 'presentation', 'meeting', 'project', 
                     'proposal', 'contract', 'agreement']
        # Personal keywords
        personal_terms = ['vacation', 'family', 'personal', 'birthday', 
                         'wedding', 'trip']
        
        text_lower = text.lower()
        
        for term in financial_terms:
            if term in text_lower:
                keywords.append(term)
        
        for term in work_terms:
            if term in text_lower:
                keywords.append(term)
        
        for term in personal_terms:
            if term in text_lower:
                keywords.append(term)
        
        return list(set(keywords))  # Remove duplicates
    
    def _suggest_category(self, analysis: Dict) -> Optional[str]:
        """Suggest category based on analysis"""
        keywords = analysis.get("keywords", [])
        metadata = analysis.get("metadata", {})
        
        # Financial documents
        financial_keywords = ['invoice', 'receipt', 'payment', 'bill', 'tax']
        if any(kw in keywords for kw in financial_keywords):
            return "Finance"
        
        # Work documents
        work_keywords = ['report', 'presentation', 'meeting', 'project']
        if any(kw in keywords for kw in work_keywords):
            return "Work"
        
        # Personal documents
        personal_keywords = ['vacation', 'family', 'personal']
        if any(kw in keywords for kw in personal_keywords):
            return "Personal"
        
        # Photos from camera
        if metadata.get("camera_make"):
            return "Photos"
        
        # Scanned documents (OCR text found)
        if analysis.get("content_text") and len(analysis["content_text"]) > 100:
            return "Scanned Documents"
        
        return None