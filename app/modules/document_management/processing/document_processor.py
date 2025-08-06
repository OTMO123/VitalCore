"""
Document Processor

Main orchestrator for document processing pipeline.
Combines OCR, text extraction, and prepares for classification.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime

import structlog

from .ocr_service import OCRService, OCRResult, get_ocr_service
from .text_extractor import TextExtractorService, ExtractionResult, get_text_extractor_service

logger = structlog.get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of complete document processing."""
    
    text: str
    processing_method: str
    confidence: float
    metadata: Dict[str, Any]
    processing_time_ms: int
    success: bool
    ocr_result: Optional[OCRResult] = None
    extraction_result: Optional[ExtractionResult] = None
    error: Optional[str] = None


class DocumentProcessor:
    """
    Main document processing orchestrator.
    
    Implements the strategy pattern to choose between OCR and text extraction
    based on document type and content.
    """
    
    def __init__(
        self,
        ocr_service: Optional[OCRService] = None,
        text_extractor: Optional[TextExtractorService] = None
    ):
        self.ocr_service = ocr_service or get_ocr_service()
        self.text_extractor = text_extractor or get_text_extractor_service()
        self.logger = logger.bind(service="DocumentProcessor")
    
    async def process_document(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        prefer_ocr: bool = False
    ) -> ProcessingResult:
        """
        Process document to extract text content.
        
        Strategy:
        1. For text-based formats (PDF with text, Word, etc.) - use text extraction first
        2. For image formats or scanned documents - use OCR
        3. For PDFs - try text extraction first, fall back to OCR if needed
        4. Combine results when both methods are used
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info(
                "Starting document processing",
                filename=filename,
                mime_type=mime_type,
                file_size=len(file_data),
                prefer_ocr=prefer_ocr
            )
            
            # Determine processing strategy
            strategy = self._determine_processing_strategy(mime_type, prefer_ocr)
            
            if strategy == "text_extraction":
                result = await self._process_with_text_extraction(
                    file_data, filename, mime_type, start_time
                )
            elif strategy == "ocr":
                result = await self._process_with_ocr(
                    file_data, filename, mime_type, start_time
                )
            elif strategy == "hybrid":
                result = await self._process_hybrid(
                    file_data, filename, mime_type, start_time
                )
            else:
                raise ValueError(f"Unknown processing strategy: {strategy}")
            
            self.logger.info(
                "Document processing completed",
                filename=filename,
                success=result.success,
                method=result.processing_method,
                confidence=result.confidence,
                text_length=len(result.text),
                processing_time=result.processing_time_ms
            )
            
            return result
            
        except Exception as e:
            processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            self.logger.error("Document processing failed", error=str(e), filename=filename)
            
            return ProcessingResult(
                text="",
                processing_method="error",
                confidence=0.0,
                metadata={"error": str(e), "filename": filename},
                processing_time_ms=processing_time,
                success=False,
                error=str(e)
            )
    
    def _determine_processing_strategy(self, mime_type: str, prefer_ocr: bool) -> str:
        """Determine the best processing strategy for the document."""
        
        if prefer_ocr:
            if self.ocr_service.is_supported_format(mime_type):
                return "ocr"
        
        # Image formats always use OCR
        if mime_type.startswith("image/"):
            return "ocr"
        
        # Text-based formats use text extraction
        if mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
            "text/html",
            "application/json"
        ]:
            return "text_extraction"
        
        # PDFs use hybrid approach (try text extraction, fall back to OCR)
        if mime_type == "application/pdf":
            return "hybrid"
        
        # Default to text extraction if supported, otherwise OCR
        if self.text_extractor._get_extractor_for_format(mime_type):
            return "text_extraction"
        elif self.ocr_service.is_supported_format(mime_type):
            return "ocr"
        else:
            return "text_extraction"  # Will fail gracefully
    
    async def _process_with_text_extraction(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        start_time: float
    ) -> ProcessingResult:
        """Process document using text extraction."""
        
        extraction_result = await self.text_extractor.extract_text(
            file_data, mime_type, filename
        )
        
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        if extraction_result.success and extraction_result.text.strip():
            return ProcessingResult(
                text=extraction_result.text,
                processing_method="text_extraction",
                confidence=95.0,  # High confidence for direct text extraction
                metadata={
                    "extraction_method": extraction_result.extraction_method,
                    "format": extraction_result.format,
                    **extraction_result.metadata
                },
                processing_time_ms=processing_time,
                success=True,
                extraction_result=extraction_result
            )
        else:
            # Text extraction failed or returned empty text
            return ProcessingResult(
                text=extraction_result.text,
                processing_method="text_extraction_failed",
                confidence=0.0,
                metadata={
                    "extraction_error": extraction_result.error,
                    **extraction_result.metadata
                },
                processing_time_ms=processing_time,
                success=False,
                extraction_result=extraction_result,
                error=extraction_result.error or "Text extraction returned empty content"
            )
    
    async def _process_with_ocr(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        start_time: float
    ) -> ProcessingResult:
        """Process document using OCR."""
        
        ocr_result = await self.ocr_service.process_document(
            file_data, mime_type
        )
        
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        return ProcessingResult(
            text=ocr_result.text,
            processing_method="ocr",
            confidence=ocr_result.confidence,
            metadata={
                "ocr_language": ocr_result.language,
                "page_count": ocr_result.page_count,
                **ocr_result.metadata
            },
            processing_time_ms=processing_time,
            success=ocr_result.error is None,
            ocr_result=ocr_result,
            error=ocr_result.error
        )
    
    async def _process_hybrid(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        start_time: float
    ) -> ProcessingResult:
        """Process document using hybrid approach (text extraction + OCR fallback)."""
        
        # First try text extraction
        extraction_result = await self.text_extractor.extract_text(
            file_data, mime_type, filename
        )
        
        # Check if text extraction was successful and returned meaningful content
        if (extraction_result.success and 
            extraction_result.text.strip() and 
            len(extraction_result.text.strip()) > 50):  # Minimum meaningful content
            
            processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            return ProcessingResult(
                text=extraction_result.text,
                processing_method="hybrid_text_extraction",
                confidence=95.0,
                metadata={
                    "primary_method": "text_extraction",
                    "extraction_method": extraction_result.extraction_method,
                    **extraction_result.metadata
                },
                processing_time_ms=processing_time,
                success=True,
                extraction_result=extraction_result
            )
        
        # Text extraction failed or returned minimal content, try OCR
        self.logger.info(
            "Text extraction insufficient, falling back to OCR",
            filename=filename,
            extracted_length=len(extraction_result.text) if extraction_result.text else 0
        )
        
        ocr_result = await self.ocr_service.process_document(file_data, mime_type)
        
        processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        # Combine results
        combined_text = ""
        if extraction_result.text.strip():
            combined_text += f"[TEXT_EXTRACTION]\n{extraction_result.text}\n\n"
        if ocr_result.text.strip():
            combined_text += f"[OCR_CONTENT]\n{ocr_result.text}"
        
        # Use the better result
        if ocr_result.text.strip() and len(ocr_result.text.strip()) > len(extraction_result.text.strip()):
            primary_text = ocr_result.text
            primary_method = "hybrid_ocr"
            confidence = ocr_result.confidence
        else:
            primary_text = extraction_result.text
            primary_method = "hybrid_text_extraction"
            confidence = 85.0 if extraction_result.success else 0.0
        
        return ProcessingResult(
            text=primary_text,
            processing_method=primary_method,
            confidence=confidence,
            metadata={
                "hybrid_processing": True,
                "text_extraction_attempted": True,
                "ocr_attempted": True,
                "extraction_success": extraction_result.success,
                "ocr_success": ocr_result.error is None,
                "combined_text_available": bool(combined_text.strip()),
                "text_extraction_length": len(extraction_result.text),
                "ocr_text_length": len(ocr_result.text)
            },
            processing_time_ms=processing_time,
            success=bool(primary_text.strip()),
            extraction_result=extraction_result,
            ocr_result=ocr_result,
            error=None if primary_text.strip() else "Both text extraction and OCR failed"
        )
    
    def get_supported_formats(self) -> List[str]:
        """Get list of all supported formats."""
        text_formats = self.text_extractor.get_supported_formats()
        ocr_formats = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/tiff",
            "image/bmp",
            "image/gif"
        ]
        
        # Combine and deduplicate
        all_formats = list(set(text_formats + ocr_formats))
        return sorted(all_formats)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for document processor."""
        try:
            # Test with a simple text document
            test_data = b"Test document content for health check"
            result = await self.process_document(
                test_data,
                "health_check.txt",
                "text/plain"
            )
            
            return {
                "status": "healthy" if result.success else "degraded",
                "ocr_service": "available",
                "text_extractor": "available",
                "supported_formats": len(self.get_supported_formats()),
                "test_result": result.success
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "ocr_service": "unknown",
                "text_extractor": "unknown"
            }


# Factory function
def get_document_processor(
    ocr_service: Optional[OCRService] = None,
    text_extractor: Optional[TextExtractorService] = None
) -> DocumentProcessor:
    """Factory function to create document processor."""
    return DocumentProcessor(ocr_service, text_extractor)