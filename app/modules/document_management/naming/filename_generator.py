"""
Smart Filename Generator

Generates intelligent, descriptive filenames based on document content,
classification results, and metadata following medical naming conventions.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
import hashlib

import structlog

from app.core.database_unified import DocumentType
from app.modules.document_management.classification.classifier import ClassificationResult

logger = structlog.get_logger(__name__)


@dataclass
class GeneratedFilename:
    """Result of filename generation."""
    
    filename: str
    original_filename: str
    generation_method: str
    confidence: float
    metadata: Dict[str, Any]
    suggestions: List[str]
    safe_filename: str
    success: bool
    error: Optional[str] = None


class ContentAnalyzer:
    """Analyzes document content to extract meaningful filename components."""
    
    def __init__(self):
        self.logger = logger.bind(component="ContentAnalyzer")
    
    def extract_key_information(
        self, 
        text: str, 
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """Extract key information from document text."""
        
        info = {
            "document_type": classification.document_type.value,
            "category": classification.category,
            "dates": self._extract_dates(text),
            "patient_info": self._extract_patient_info(text),
            "medical_terms": self._extract_medical_terms(text, classification.document_type),
            "test_names": self._extract_test_names(text, classification.document_type),
            "provider_info": self._extract_provider_info(text),
            "urgency": self._extract_urgency_indicators(text),
            "body_parts": self._extract_body_parts(text),
            "procedures": self._extract_procedures(text)
        }
        
        return info
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates from document text."""
        dates = []
        
        # Common date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or MM-DD-YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',    # YYYY/MM/DD or YYYY-MM-DD
            r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',  # Month DD, YYYY
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                dates.append({
                    "raw": date_str,
                    "position": match.start(),
                    "type": "extracted"
                })
        
        return dates[:5]  # Limit to first 5 dates
    
    def _extract_patient_info(self, text: str) -> Dict[str, Any]:
        """Extract patient information."""
        patient_info = {}
        
        # Patient name patterns
        name_patterns = [
            r'(?i)patient[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?i)name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?i)pt[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                patient_info["name"] = match.group(1).strip()
                break
        
        # Patient ID patterns
        id_patterns = [
            r'(?i)(?:patient\s+id|pt\s+id|medical\s+record)[:\s#]*([A-Z0-9-]+)',
            r'(?i)mrn[:\s#]*([A-Z0-9-]+)',
            r'(?i)id[:\s#]*([A-Z0-9]{6,})',
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, text)
            if match:
                patient_info["id"] = match.group(1).strip()
                break
        
        # Age/DOB patterns
        age_patterns = [
            r'(?i)age[:\s]*(\d{1,3})',
            r'(?i)(\d{1,3})\s*(?:year|yr)s?\s*old',
            r'(?i)dob[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text)
            if match:
                patient_info["age_or_dob"] = match.group(1).strip()
                break
        
        return patient_info
    
    def _extract_medical_terms(self, text: str, doc_type: DocumentType) -> List[str]:
        """Extract relevant medical terms based on document type."""
        
        medical_vocabularies = {
            DocumentType.LAB_RESULT: [
                "hemoglobin", "glucose", "cholesterol", "creatinine", "bilirubin",
                "albumin", "protein", "electrolytes", "sodium", "potassium",
                "chloride", "co2", "bun", "ast", "alt", "alkaline", "phosphatase",
                "triglycerides", "hdl", "ldl", "tsh", "t3", "t4", "hba1c"
            ],
            DocumentType.IMAGING: [
                "chest", "abdomen", "pelvis", "head", "neck", "spine", "extremity",
                "contrast", "enhanced", "axial", "sagittal", "coronal", "angiogram",
                "venogram", "arthrogram", "myelogram", "fluoroscopy"
            ],
            DocumentType.CLINICAL_NOTE: [
                "hypertension", "diabetes", "asthma", "copd", "pneumonia", "bronchitis",
                "arthritis", "depression", "anxiety", "migraine", "seizure", "stroke",
                "myocardial", "infarction", "angina", "arrhythmia", "heart", "failure"
            ],
            DocumentType.PRESCRIPTION: [
                "lisinopril", "metformin", "atorvastatin", "amlodipine", "omeprazole",
                "levothyroxine", "albuterol", "hydrochlorothiazide", "losartan",
                "simvastatin", "metoprolol", "prednisone", "amoxicillin", "ibuprofen"
            ]
        }
        
        vocabulary = medical_vocabularies.get(doc_type, [])
        found_terms = []
        
        text_lower = text.lower()
        for term in vocabulary:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms[:3]  # Limit to top 3 most relevant terms
    
    def _extract_test_names(self, text: str, doc_type: DocumentType) -> List[str]:
        """Extract test/procedure names."""
        
        if doc_type not in [DocumentType.LAB_RESULT, DocumentType.IMAGING]:
            return []
        
        test_patterns = {
            DocumentType.LAB_RESULT: [
                r'(?i)\b(CBC|complete blood count)\b',
                r'(?i)\b(BMP|basic metabolic panel)\b',
                r'(?i)\b(CMP|comprehensive metabolic panel)\b',
                r'(?i)\b(lipid panel|lipid profile)\b',
                r'(?i)\b(liver function tests?|LFTs?)\b',
                r'(?i)\b(thyroid function tests?|TFTs?)\b',
                r'(?i)\b(hemoglobin a1c|hba1c)\b',
                r'(?i)\b(urinalysis|urine analysis)\b',
                r'(?i)\b(blood culture)\b',
                r'(?i)\b(sed rate|ESR)\b'
            ],
            DocumentType.IMAGING: [
                r'(?i)\b(ct|computed tomography)\s+(?:scan\s+)?(?:of\s+)?(\w+)',
                r'(?i)\b(mri|magnetic resonance)\s+(?:imaging\s+)?(?:of\s+)?(\w+)',
                r'(?i)\b(x-ray|radiograph)\s+(?:of\s+)?(\w+)',
                r'(?i)\b(ultrasound|sonogram)\s+(?:of\s+)?(\w+)',
                r'(?i)\b(mammogram|mammography)\b',
                r'(?i)\b(echocardiogram|echo)\b',
                r'(?i)\b(angiogram|angiography)\b',
                r'(?i)\b(pet scan|positron emission)\b'
            ]
        }
        
        patterns = test_patterns.get(doc_type, [])
        found_tests = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                test_name = match.group(0).strip()
                if len(match.groups()) > 1:
                    # Include body part if captured
                    body_part = match.group(2) if len(match.groups()) >= 2 else ""
                    if body_part:
                        test_name = f"{match.group(1)} {body_part}"
                found_tests.append(test_name.lower())
        
        return list(set(found_tests))[:2]  # Unique tests, max 2
    
    def _extract_provider_info(self, text: str) -> Dict[str, str]:
        """Extract healthcare provider information."""
        provider_info = {}
        
        # Doctor patterns
        doctor_patterns = [
            r'(?i)dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?i)doctor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?i)physician[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text)
            if match:
                provider_info["doctor"] = match.group(1).strip()
                break
        
        # Department/specialty patterns
        dept_patterns = [
            r'(?i)department[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?i)clinic[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?i)(?:cardiology|neurology|orthopedic|radiology|pathology|oncology|gastroenterology)',
        ]
        
        for pattern in dept_patterns:
            match = re.search(pattern, text)
            if match:
                provider_info["department"] = match.group(0).strip()
                break
        
        return provider_info
    
    def _extract_urgency_indicators(self, text: str) -> Optional[str]:
        """Extract urgency/priority indicators."""
        urgency_patterns = [
            (r'(?i)\b(stat|emergency|urgent|critical|abnormal)\b', "urgent"),
            (r'(?i)\b(routine|normal|stable)\b', "routine"),
            (r'(?i)\b(follow.?up|return|recheck)\b', "followup"),
        ]
        
        for pattern, urgency in urgency_patterns:
            if re.search(pattern, text):
                return urgency
        
        return None
    
    def _extract_body_parts(self, text: str) -> List[str]:
        """Extract body parts/anatomy mentioned."""
        body_parts = [
            "chest", "abdomen", "pelvis", "head", "neck", "spine", "back",
            "shoulder", "arm", "elbow", "wrist", "hand", "hip", "knee",
            "ankle", "foot", "heart", "lung", "liver", "kidney", "brain",
            "thyroid", "prostate", "breast", "ovary", "uterus"
        ]
        
        found_parts = []
        text_lower = text.lower()
        
        for part in body_parts:
            if part in text_lower:
                found_parts.append(part)
        
        return found_parts[:2]  # Limit to 2 most relevant
    
    def _extract_procedures(self, text: str) -> List[str]:
        """Extract procedure names."""
        procedure_patterns = [
            r'(?i)\b(biopsy|surgery|operation|procedure)\b',
            r'(?i)\b(colonoscopy|endoscopy|bronchoscopy)\b',
            r'(?i)\b(catheterization|angioplasty|stent)\b',
            r'(?i)\b(injection|aspiration|drainage)\b',
        ]
        
        found_procedures = []
        for pattern in procedure_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                found_procedures.append(match.group(0).lower())
        
        return list(set(found_procedures))[:2]  # Unique procedures, max 2


class FilenameTemplateEngine:
    """Generates filenames using templates based on document type and content."""
    
    def __init__(self):
        self.logger = logger.bind(component="FilenameTemplateEngine")
        self._load_templates()
    
    def _load_templates(self):
        """Load filename templates for different document types."""
        
        self.templates = {
            DocumentType.LAB_RESULT: [
                "{patient_name}_{test_name}_{date}",
                "Lab_{test_name}_{patient_id}_{date}",
                "{date}_{patient_name}_{test_name}_Results",
                "LabResult_{category}_{date}_{patient_id}",
                "{patient_name}_Lab_{medical_terms}_{date}"
            ],
            
            DocumentType.IMAGING: [
                "{patient_name}_{test_name}_{body_part}_{date}",
                "Imaging_{test_name}_{patient_id}_{date}",
                "{date}_{patient_name}_{test_name}_{body_part}",
                "{test_name}_{body_part}_{patient_id}_{date}",
                "{patient_name}_{category}_{date}_{urgency}"
            ],
            
            DocumentType.CLINICAL_NOTE: [
                "{patient_name}_{visit_type}_{date}",
                "ClinicalNote_{patient_id}_{date}_{urgency}",
                "{date}_{patient_name}_{category}_Note",
                "{patient_name}_{provider}_{date}_Visit",
                "Note_{category}_{patient_id}_{date}"
            ],
            
            DocumentType.PRESCRIPTION: [
                "{patient_name}_{medication}_{date}",
                "Rx_{patient_id}_{medication}_{date}",
                "{date}_{patient_name}_Prescription_{medication}",
                "Prescription_{medication}_{patient_id}_{date}",
                "{patient_name}_Rx_{date}_{provider}"
            ],
            
            DocumentType.INSURANCE: [
                "{patient_name}_{insurance_type}_{date}",
                "Insurance_{patient_id}_{category}_{date}",
                "{date}_{patient_name}_{category}_Auth",
                "{patient_name}_Insurance_{date}_{urgency}",
                "Auth_{category}_{patient_id}_{date}"
            ],
            
            DocumentType.PATHOLOGY: [
                "{patient_name}_{specimen_type}_{date}",
                "Pathology_{patient_id}_{procedure}_{date}",
                "{date}_{patient_name}_{category}_Path",
                "{patient_name}_{body_part}_Biopsy_{date}",
                "Path_{procedure}_{patient_id}_{date}"
            ],
            
            DocumentType.OTHER: [
                "{patient_name}_{category}_{date}",
                "Document_{patient_id}_{date}_{urgency}",
                "{date}_{patient_name}_{original_name}",
                "{patient_name}_Medical_{date}",
                "Doc_{category}_{patient_id}_{date}"
            ]
        }
    
    def generate_filename(
        self, 
        info: Dict[str, Any],
        classification: ClassificationResult,
        original_filename: str
    ) -> Tuple[str, float]:
        """Generate filename using best matching template."""
        
        doc_type = classification.document_type
        templates = self.templates.get(doc_type, self.templates[DocumentType.OTHER])
        
        # Prepare variables for template substitution
        variables = self._prepare_variables(info, classification, original_filename)
        
        # Try templates in order of preference
        best_filename = None
        best_score = 0.0
        
        for template in templates:
            filename, score = self._apply_template(template, variables)
            if score > best_score and filename:
                best_filename = filename
                best_score = score
        
        if not best_filename:
            # Fallback to simple pattern
            best_filename = self._generate_fallback_filename(variables)
            best_score = 0.5
        
        return best_filename, best_score
    
    def _prepare_variables(
        self, 
        info: Dict[str, Any],
        classification: ClassificationResult,
        original_filename: str
    ) -> Dict[str, str]:
        """Prepare variables for template substitution."""
        
        variables = {}
        
        # Patient information
        patient_info = info.get("patient_info", {})
        variables["patient_name"] = self._clean_name(patient_info.get("name", "Patient"))
        variables["patient_id"] = patient_info.get("id", "ID")
        
        # Date information
        dates = info.get("dates", [])
        if dates:
            variables["date"] = self._format_date(dates[0]["raw"])
        else:
            variables["date"] = datetime.now().strftime("%Y%m%d")
        
        # Medical information
        test_names = info.get("test_names", [])
        variables["test_name"] = self._clean_term(test_names[0] if test_names else "Test")
        
        medical_terms = info.get("medical_terms", [])
        variables["medical_terms"] = self._clean_term(medical_terms[0] if medical_terms else "Medical")
        variables["medication"] = variables["medical_terms"]  # Alias for prescriptions
        
        body_parts = info.get("body_parts", [])
        variables["body_part"] = self._clean_term(body_parts[0] if body_parts else "Area")
        
        procedures = info.get("procedures", [])
        variables["procedure"] = self._clean_term(procedures[0] if procedures else "Procedure")
        variables["specimen_type"] = variables["procedure"]  # Alias for pathology
        
        # Provider information
        provider_info = info.get("provider_info", {})
        variables["provider"] = self._clean_name(provider_info.get("doctor", "Provider"))
        
        # Classification information
        variables["category"] = self._clean_term(classification.category or "General")
        variables["visit_type"] = variables["category"]  # Alias for clinical notes
        variables["insurance_type"] = variables["category"]  # Alias for insurance
        
        # Urgency
        urgency = info.get("urgency")
        variables["urgency"] = urgency.title() if urgency else "Routine"
        
        # Original filename components
        original_base = original_filename.split('.')[0] if '.' in original_filename else original_filename
        variables["original_name"] = self._clean_filename_component(original_base)
        
        return variables
    
    def _apply_template(self, template: str, variables: Dict[str, str]) -> Tuple[Optional[str], float]:
        """Apply template with available variables."""
        
        # Find all template variables
        template_vars = re.findall(r'\{(\w+)\}', template)
        
        # Calculate availability score
        available_vars = sum(1 for var in template_vars if var in variables and variables[var] != "Unknown")
        score = available_vars / len(template_vars) if template_vars else 0.0
        
        # Only use template if we have most variables
        if score < 0.6:
            return None, score
        
        # Substitute variables
        try:
            filename = template
            for var in template_vars:
                value = variables.get(var, "Unknown")
                filename = filename.replace(f"{{{var}}}", value)
            
            # Clean up the filename
            filename = self._clean_filename(filename)
            
            return filename, score
            
        except Exception as e:
            self.logger.warning("Template application failed", template=template, error=str(e))
            return None, 0.0
    
    def _generate_fallback_filename(self, variables: Dict[str, str]) -> str:
        """Generate fallback filename when templates fail."""
        
        components = []
        
        # Always include patient and date
        if variables.get("patient_name") != "Unknown":
            components.append(variables["patient_name"])
        
        # Add most relevant medical component
        for key in ["test_name", "medical_terms", "category"]:
            if variables.get(key) and variables[key] != "Unknown":
                components.append(variables[key])
                break
        
        # Always add date
        components.append(variables["date"])
        
        filename = "_".join(components)
        return self._clean_filename(filename)
    
    def _clean_name(self, name: str) -> str:
        """Clean patient/provider names for filename use."""
        if not name or name.lower() in ["unknown", "patient", "provider"]:
            return "Unknown"
        
        # Remove titles and clean
        name = re.sub(r'(?i)\b(dr|doctor|mr|mrs|ms)\b\.?\s*', '', name)
        name = re.sub(r'[^\w\s]', '', name)  # Remove special chars
        name = re.sub(r'\s+', '', name)  # Remove spaces
        
        return name.title()[:20]  # Limit length
    
    def _clean_term(self, term: str) -> str:
        """Clean medical terms for filename use."""
        if not term:
            return "Unknown"
        
        # Clean and format
        term = re.sub(r'[^\w\s]', '', term)  # Remove special chars
        term = re.sub(r'\s+', '', term)  # Remove spaces
        
        return term.title()[:15]  # Limit length
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for filename use."""
        try:
            # Try to parse and reformat date
            # This is a simplified implementation
            date_str = re.sub(r'[^\d]', '', date_str)  # Extract numbers only
            if len(date_str) >= 6:
                if len(date_str) == 8:
                    # MMDDYYYY or YYYYMMDD
                    return date_str
                elif len(date_str) == 6:
                    # MMDDYY - add 20 prefix
                    return "20" + date_str[-2:] + date_str[:4]
            
            # Fallback to current date
            return datetime.now().strftime("%Y%m%d")
            
        except:
            return datetime.now().strftime("%Y%m%d")
    
    def _clean_filename_component(self, component: str) -> str:
        """Clean filename component."""
        if not component:
            return "Document"
        
        # Remove extension and clean
        component = re.sub(r'[^\w\s]', '', component)
        component = re.sub(r'\s+', '', component)
        
        return component.title()[:20]
    
    def _clean_filename(self, filename: str) -> str:
        """Final filename cleaning and validation."""
        
        # Remove multiple underscores
        filename = re.sub(r'_+', '_', filename)
        
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        
        # Ensure reasonable length
        if len(filename) > 100:
            components = filename.split('_')
            # Keep first 3 and last component (usually date)
            if len(components) > 4:
                filename = '_'.join(components[:3] + [components[-1]])
        
        # Ensure not empty
        if not filename:
            filename = f"Document_{datetime.now().strftime('%Y%m%d')}"
        
        return filename


class FilenameGenerator:
    """
    Main filename generator service.
    
    Orchestrates content analysis and template-based filename generation.
    """
    
    def __init__(self):
        self.content_analyzer = ContentAnalyzer()
        self.template_engine = FilenameTemplateEngine()
        self.logger = logger.bind(service="FilenameGenerator")
    
    async def generate_filename(
        self,
        text: str,
        classification: ClassificationResult,
        original_filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GeneratedFilename:
        """Generate smart filename based on document content."""
        
        try:
            self.logger.info(
                "Starting filename generation",
                original_filename=original_filename,
                document_type=classification.document_type.value,
                classification_confidence=classification.confidence
            )
            
            # Analyze content to extract key information
            content_info = self.content_analyzer.extract_key_information(text, classification)
            
            # Generate filename using template engine
            generated_name, confidence = self.template_engine.generate_filename(
                content_info, classification, original_filename
            )
            
            # Generate alternative suggestions
            suggestions = await self._generate_suggestions(
                content_info, classification, original_filename, generated_name
            )
            
            # Create safe filename version
            safe_filename = self._ensure_safe_filename(generated_name)
            
            # Ensure filename has extension
            final_filename = self._add_extension(safe_filename, original_filename)
            
            self.logger.info(
                "Filename generation completed",
                original_filename=original_filename,
                generated_filename=final_filename,
                confidence=confidence
            )
            
            return GeneratedFilename(
                filename=final_filename,
                original_filename=original_filename,
                generation_method="content_analysis",
                confidence=confidence,
                metadata={
                    "content_info": content_info,
                    "template_score": confidence,
                    "classification_confidence": classification.confidence,
                    "text_length": len(text)
                },
                suggestions=suggestions,
                safe_filename=safe_filename,
                success=True
            )
            
        except Exception as e:
            self.logger.error("Filename generation failed", error=str(e))
            
            # Generate fallback filename
            fallback_name = self._generate_fallback_filename(original_filename)
            
            return GeneratedFilename(
                filename=fallback_name,
                original_filename=original_filename,
                generation_method="fallback",
                confidence=0.3,
                metadata={"error": str(e)},
                suggestions=[],
                safe_filename=fallback_name,
                success=False,
                error=str(e)
            )
    
    async def _generate_suggestions(
        self,
        content_info: Dict[str, Any],
        classification: ClassificationResult,
        original_filename: str,
        primary_filename: str
    ) -> List[str]:
        """Generate alternative filename suggestions."""
        
        suggestions = []
        
        try:
            # Get all templates for document type
            templates = self.template_engine.templates.get(
                classification.document_type, 
                self.template_engine.templates[DocumentType.OTHER]
            )
            
            variables = self.template_engine._prepare_variables(
                content_info, classification, original_filename
            )
            
            # Generate from different templates
            for template in templates[:3]:  # Top 3 templates
                filename, score = self.template_engine._apply_template(template, variables)
                if filename and filename != primary_filename and score > 0.5:
                    safe_filename = self._ensure_safe_filename(filename)
                    final_filename = self._add_extension(safe_filename, original_filename)
                    suggestions.append(final_filename)
            
            # Add simplified versions
            if content_info.get("patient_info", {}).get("name"):
                patient_name = variables.get("patient_name", "Patient")
                date = variables.get("date", datetime.now().strftime("%Y%m%d"))
                doc_type = classification.document_type.value.replace("_", "")
                
                simple_name = f"{patient_name}_{doc_type}_{date}"
                simple_name = self._add_extension(
                    self._ensure_safe_filename(simple_name), 
                    original_filename
                )
                if simple_name not in suggestions:
                    suggestions.append(simple_name)
            
        except Exception as e:
            self.logger.warning("Suggestion generation failed", error=str(e))
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _ensure_safe_filename(self, filename: str) -> str:
        """Ensure filename is safe for filesystem use."""
        
        # Remove/replace unsafe characters
        unsafe_chars = r'[<>:"/\\|?*]'
        filename = re.sub(unsafe_chars, '_', filename)
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Replace multiple underscores/spaces
        filename = re.sub(r'[_\s]+', '_', filename)
        
        # Trim and ensure not empty
        filename = filename.strip('_. ')
        if not filename:
            filename = f"Document_{datetime.now().strftime('%Y%m%d')}"
        
        # Ensure reasonable length (Windows has 255 char limit)
        if len(filename) > 200:
            filename = filename[:200].rsplit('_', 1)[0]  # Keep complete words
        
        return filename
    
    def _add_extension(self, filename: str, original_filename: str) -> str:
        """Add appropriate file extension."""
        
        # Extract extension from original filename
        if '.' in original_filename:
            original_ext = original_filename.split('.')[-1].lower()
        else:
            original_ext = 'pdf'  # Default to PDF for medical documents
        
        # Add extension if not present
        if not filename.endswith(f'.{original_ext}'):
            filename = f"{filename}.{original_ext}"
        
        return filename
    
    def _generate_fallback_filename(self, original_filename: str) -> str:
        """Generate fallback filename when all else fails."""
        
        # Use timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Try to preserve some original name
        if original_filename:
            base_name = original_filename.split('.')[0]
            safe_base = self._ensure_safe_filename(base_name)[:30]
            if safe_base:
                fallback = f"{safe_base}_{timestamp}"
            else:
                fallback = f"Document_{timestamp}"
        else:
            fallback = f"Document_{timestamp}"
        
        return self._add_extension(fallback, original_filename)
    
    async def batch_generate_filenames(
        self,
        documents: List[Tuple[str, ClassificationResult, str]],  # (text, classification, original_filename)
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[GeneratedFilename]:
        """Generate filenames for multiple documents in batch."""
        
        if metadata is None:
            metadata = [None] * len(documents)
        
        tasks = []
        for i, (text, classification, original_filename) in enumerate(documents):
            task = self.generate_filename(text, classification, original_filename, metadata[i])
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for filename generator."""
        
        try:
            # Test with sample data
            from app.modules.document_management.classification.classifier import ClassificationResult
            from app.core.database_unified import DocumentType
            
            test_classification = ClassificationResult(
                document_type=DocumentType.LAB_RESULT,
                confidence=0.9,
                category="laboratory",
                subcategory=None,
                tags=["blood_work"],
                metadata={},
                classification_method="test",
                processing_time_ms=0,
                success=True
            )
            
            test_text = "Laboratory Report Patient: John Doe Blood test results hemoglobin glucose"
            
            result = await self.generate_filename(
                test_text,
                test_classification,
                "lab_results.pdf"
            )
            
            return {
                "status": "healthy" if result.success else "degraded",
                "test_result": result.success,
                "content_analyzer": "available",
                "template_engine": "available"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Factory function
def get_filename_generator() -> FilenameGenerator:
    """Factory function to create filename generator."""
    return FilenameGenerator()