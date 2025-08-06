"""
Document Processing Module

Contains OCR, text extraction, and document processing services.
"""

from .ocr_service import OCRService, OCRResult
from .text_extractor import TextExtractorService, ExtractionResult
from .document_processor import DocumentProcessor, ProcessingResult

__all__ = [
    "OCRService", "OCRResult",
    "TextExtractorService", "ExtractionResult", 
    "DocumentProcessor", "ProcessingResult"
]