"""
Template Engine for Filename Generation

Advanced template processing for intelligent filename generation.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import structlog
from datetime import datetime
from app.core.database_unified import DocumentType

logger = structlog.get_logger(__name__)

@dataclass
class FilenameTemplate:
    """Template definition for filename generation."""
    
    name: str
    pattern: str
    description: str
    variables: List[str]
    document_types: List[DocumentType]
    examples: List[str] = None
    validation_rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []
        if self.validation_rules is None:
            self.validation_rules = {}

class TemplateEngine:
    """Advanced template engine for filename generation."""
    
    def __init__(self):
        self.templates: Dict[str, FilenameTemplate] = {}
        self.functions: Dict[str, callable] = {}
        self._initialize_default_templates()
        self._initialize_template_functions()
    
    def _initialize_default_templates(self):
        """Initialize default filename templates."""
        
        # Medical document templates
        templates = [
            FilenameTemplate(
                name="medical_standard",
                pattern="{doc_type}_{date:YYYYMMDD}_{patient_mrn}_{sequence:000}",
                description="Standard medical document naming",
                variables=["doc_type", "date", "patient_mrn", "sequence"],
                document_types=[
                    DocumentType.LAB_RESULT, DocumentType.IMAGING, 
                    DocumentType.CLINICAL_NOTE, DocumentType.MEDICAL_RECORD
                ],
                examples=[
                    "LAB_20241230_MRN123456_001.pdf",
                    "IMG_20241230_MRN789012_001.pdf"
                ],
                validation_rules={
                    "max_length": 50,
                    "required_vars": ["doc_type", "date", "patient_mrn"]
                }
            ),
            
            FilenameTemplate(
                name="radiology_detailed",
                pattern="RAD_{modality}_{body_part}_{date:YYYYMMDD}_{patient_mrn}_{study_id}",
                description="Detailed radiology document naming",
                variables=["modality", "body_part", "date", "patient_mrn", "study_id"],
                document_types=[DocumentType.IMAGING],
                examples=[
                    "RAD_CT_CHEST_20241230_MRN123456_STU001.pdf",
                    "RAD_MRI_BRAIN_20241230_MRN789012_STU002.pdf"
                ],
                validation_rules={
                    "max_length": 60,
                    "required_vars": ["modality", "date", "patient_mrn"]
                }
            ),
            
            FilenameTemplate(
                name="lab_comprehensive",
                pattern="LAB_{test_category}_{test_name}_{date:YYYYMMDD}_{patient_mrn}_{lab_id}",
                description="Comprehensive laboratory document naming",
                variables=["test_category", "test_name", "date", "patient_mrn", "lab_id"],
                document_types=[DocumentType.LAB_RESULT],
                examples=[
                    "LAB_HEMATOLOGY_CBC_20241230_MRN123456_LAB001.pdf",
                    "LAB_CHEMISTRY_BMP_20241230_MRN789012_LAB002.pdf"
                ],
                validation_rules={
                    "max_length": 65,
                    "required_vars": ["test_category", "date", "patient_mrn"]
                }
            ),
            
            FilenameTemplate(
                name="clinical_visit",
                pattern="VISIT_{visit_type}_{provider}_{date:YYYYMMDD}_{patient_mrn}_{visit_id}",
                description="Clinical visit documentation naming",
                variables=["visit_type", "provider", "date", "patient_mrn", "visit_id"],
                document_types=[DocumentType.CLINICAL_NOTE],
                examples=[
                    "VISIT_INITIAL_DRSMITH_20241230_MRN123456_VIS001.pdf",
                    "VISIT_FOLLOWUP_DRJONES_20241230_MRN789012_VIS002.pdf"
                ],
                validation_rules={
                    "max_length": 60,
                    "required_vars": ["visit_type", "date", "patient_mrn"]
                }
            ),
            
            FilenameTemplate(
                name="prescription_detailed",
                pattern="RX_{medication}_{strength}_{date:YYYYMMDD}_{patient_mrn}_{rx_number}",
                description="Prescription document naming with medication details",
                variables=["medication", "strength", "date", "patient_mrn", "rx_number"],
                document_types=[DocumentType.PRESCRIPTION],
                examples=[
                    "RX_LISINOPRIL_10MG_20241230_MRN123456_RX001.pdf",
                    "RX_METFORMIN_500MG_20241230_MRN789012_RX002.pdf"
                ],
                validation_rules={
                    "max_length": 55,
                    "required_vars": ["medication", "date", "patient_mrn"]
                }
            ),
            
            FilenameTemplate(
                name="administrative_simple",
                pattern="{doc_category}_{date:YYYYMMDD}_{patient_mrn}_{doc_id}",
                description="Simple administrative document naming",
                variables=["doc_category", "date", "patient_mrn", "doc_id"],
                document_types=[DocumentType.INSURANCE, DocumentType.OTHER],
                examples=[
                    "INS_20241230_MRN123456_DOC001.pdf",
                    "ADMIN_20241230_MRN789012_DOC002.pdf"
                ],
                validation_rules={
                    "max_length": 45,
                    "required_vars": ["doc_category", "patient_mrn"]
                }
            ),
            
            FilenameTemplate(
                name="timestamp_detailed",
                pattern="{doc_type}_{timestamp:YYYYMMDD_HHMMSS}_{patient_mrn}_{hash:8}",
                description="Timestamp-based naming with hash for uniqueness",
                variables=["doc_type", "timestamp", "patient_mrn", "hash"],
                document_types=list(DocumentType),
                examples=[
                    "DOC_20241230_143022_MRN123456_A1B2C3D4.pdf",
                    "LAB_20241230_091500_MRN789012_E5F6G7H8.pdf"
                ],
                validation_rules={
                    "max_length": 50,
                    "required_vars": ["doc_type", "timestamp", "patient_mrn"]
                }
            )
        ]
        
        for template in templates:
            self.templates[template.name] = template
    
    def _initialize_template_functions(self):
        """Initialize template processing functions."""
        
        self.functions.update({
            "upper": lambda x: str(x).upper(),
            "lower": lambda x: str(x).lower(),
            "title": lambda x: str(x).title(),
            "truncate": lambda x, length: str(x)[:int(length)],
            "pad_zero": lambda x, width: str(x).zfill(int(width)),
            "replace_spaces": lambda x, char="_": str(x).replace(" ", char),
            "extract_initials": self._extract_initials,
            "sanitize": self._sanitize_value,
            "hash8": lambda x: self._generate_hash(str(x), 8),
            "current_date": lambda fmt="YYYYMMDD": self._format_current_date(fmt),
            "increment": lambda x: str(int(x) + 1) if str(x).isdigit() else x
        })
    
    def apply_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        document_type: DocumentType = None
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Apply a template to generate a filename.
        
        Returns:
            Tuple of (filename, confidence, metadata)
        """
        
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        # Validate document type compatibility
        if document_type and document_type not in template.document_types:
            logger.warning(
                "Document type not compatible with template",
                template_name=template_name,
                document_type=document_type.value,
                compatible_types=[dt.value for dt in template.document_types]
            )
        
        # Process template
        try:
            filename = self._process_template_pattern(template.pattern, variables)
            confidence = self._calculate_template_confidence(template, variables)
            
            # Apply validation rules
            filename = self._apply_validation_rules(filename, template.validation_rules)
            
            metadata = {
                "template_name": template_name,
                "template_description": template.description,
                "variables_used": list(variables.keys()),
                "missing_variables": [v for v in template.variables if v not in variables],
                "validation_applied": bool(template.validation_rules)
            }
            
            logger.info(
                "Template applied successfully",
                template_name=template_name,
                generated_filename=filename,
                confidence=confidence
            )
            
            return filename, confidence, metadata
            
        except Exception as e:
            logger.error(
                "Template application failed",
                template_name=template_name,
                error=str(e)
            )
            raise
    
    def _process_template_pattern(self, pattern: str, variables: Dict[str, Any]) -> str:
        """Process template pattern with variables and functions."""
        
        result = pattern
        
        # Find all variable placeholders: {variable}, {variable:format}, {function(variable)}
        placeholder_pattern = r'\{([^}]+)\}'
        placeholders = re.findall(placeholder_pattern, result)
        
        for placeholder in placeholders:
            try:
                value = self._resolve_placeholder(placeholder, variables)
                result = result.replace(f"{{{placeholder}}}", str(value))
            except Exception as e:
                logger.warning(
                    "Failed to resolve placeholder",
                    placeholder=placeholder,
                    error=str(e)
                )
                # Replace with placeholder indicator
                result = result.replace(f"{{{placeholder}}}", "UNKNOWN")
        
        return result
    
    def _resolve_placeholder(self, placeholder: str, variables: Dict[str, Any]) -> str:
        """Resolve a single placeholder with optional formatting or functions."""
        
        # Check for formatting: variable:format
        if ":" in placeholder:
            var_name, format_spec = placeholder.split(":", 1)
            var_name = var_name.strip()
            
            if var_name not in variables:
                return "UNKNOWN"
            
            value = variables[var_name]
            return self._apply_format(value, format_spec)
        
        # Check for function calls: function(variable)
        if "(" in placeholder and placeholder.endswith(")"):
            func_call = placeholder
            return self._execute_function_call(func_call, variables)
        
        # Simple variable lookup
        var_name = placeholder.strip()
        if var_name in variables:
            return str(variables[var_name])
        
        return "UNKNOWN"
    
    def _apply_format(self, value: Any, format_spec: str) -> str:
        """Apply format specification to a value."""
        
        if isinstance(value, datetime):
            # Date/time formatting
            if format_spec == "YYYYMMDD":
                return value.strftime("%Y%m%d")
            elif format_spec == "YYYY-MM-DD":
                return value.strftime("%Y-%m-%d")
            elif format_spec == "YYYYMMDD_HHMMSS":
                return value.strftime("%Y%m%d_%H%M%S")
            else:
                return value.strftime(format_spec)
        
        elif isinstance(value, (int, float)):
            # Numeric formatting
            if format_spec.isdigit():
                # Zero-padding
                return str(value).zfill(int(format_spec))
            elif format_spec.startswith("0") and format_spec[1:].isdigit():
                # Zero-padding with explicit zeros
                return str(value).zfill(len(format_spec))
        
        # String formatting
        if format_spec == "upper":
            return str(value).upper()
        elif format_spec == "lower":
            return str(value).lower()
        elif format_spec == "title":
            return str(value).title()
        
        return str(value)
    
    def _execute_function_call(self, func_call: str, variables: Dict[str, Any]) -> str:
        """Execute a function call within a template."""
        
        # Parse function call: function_name(arg1, arg2, ...)
        match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)', func_call)
        if not match:
            return "INVALID_FUNCTION"
        
        func_name, args_str = match.groups()
        
        if func_name not in self.functions:
            return "UNKNOWN_FUNCTION"
        
        # Parse arguments
        args = []
        if args_str.strip():
            for arg in args_str.split(","):
                arg = arg.strip()
                if arg.startswith('"') and arg.endswith('"'):
                    # String literal
                    args.append(arg[1:-1])
                elif arg in variables:
                    # Variable reference
                    args.append(variables[arg])
                else:
                    # Literal value
                    args.append(arg)
        
        try:
            result = self.functions[func_name](*args)
            return str(result)
        except Exception as e:
            logger.warning(
                "Function execution failed",
                function=func_name,
                args=args,
                error=str(e)
            )
            return "FUNCTION_ERROR"
    
    def _calculate_template_confidence(
        self,
        template: FilenameTemplate,
        variables: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for template application."""
        
        confidence = 0.7  # Base confidence for template use
        
        # Check required variables
        required_vars = template.validation_rules.get("required_vars", [])
        if required_vars:
            found_required = sum(1 for var in required_vars if var in variables and variables[var] != "UNKNOWN")
            confidence += (found_required / len(required_vars)) * 0.2
        
        # Check all template variables
        found_vars = sum(1 for var in template.variables if var in variables and variables[var] != "UNKNOWN")
        if template.variables:
            confidence += (found_vars / len(template.variables)) * 0.1
        
        return min(confidence, 1.0)
    
    def _apply_validation_rules(self, filename: str, validation_rules: Dict[str, Any]) -> str:
        """Apply validation rules to generated filename."""
        
        if not validation_rules:
            return filename
        
        # Apply max length
        max_length = validation_rules.get("max_length")
        if max_length and len(filename) > max_length:
            # Try to preserve extension
            if "." in filename:
                name, ext = filename.rsplit(".", 1)
                name = name[:max_length - len(ext) - 1]
                filename = f"{name}.{ext}"
            else:
                filename = filename[:max_length]
        
        # Sanitize for filesystem
        filename = self._sanitize_value(filename)
        
        return filename
    
    def _extract_initials(self, name: str) -> str:
        """Extract initials from a name."""
        words = str(name).split()
        initials = "".join(word[0].upper() for word in words if word)
        return initials[:3]  # Limit to 3 characters
    
    def _sanitize_value(self, value: str) -> str:
        """Sanitize value for use in filenames."""
        # Remove invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', str(value))
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized
    
    def _generate_hash(self, value: str, length: int = 8) -> str:
        """Generate a hash of specified length from a value."""
        import hashlib
        hash_obj = hashlib.md5(value.encode())
        return hash_obj.hexdigest()[:length].upper()
    
    def _format_current_date(self, format_spec: str) -> str:
        """Format current date according to specification."""
        now = datetime.now()
        if format_spec == "YYYYMMDD":
            return now.strftime("%Y%m%d")
        elif format_spec == "YYYY-MM-DD":
            return now.strftime("%Y-%m-%d")
        elif format_spec == "YYYYMMDD_HHMMSS":
            return now.strftime("%Y%m%d_%H%M%S")
        else:
            return now.strftime(format_spec.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d"))
    
    def get_template(self, name: str) -> Optional[FilenameTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def list_templates(self, document_type: DocumentType = None) -> List[FilenameTemplate]:
        """List available templates, optionally filtered by document type."""
        if document_type:
            return [t for t in self.templates.values() if document_type in t.document_types]
        return list(self.templates.values())
    
    def add_template(self, template: FilenameTemplate):
        """Add a custom template."""
        self.templates[template.name] = template
        logger.info(
            "Custom template added",
            template_name=template.name,
            variables=template.variables
        )