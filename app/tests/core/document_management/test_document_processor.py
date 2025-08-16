"""
Tests for Document Processing Pipeline

Tests OCR, text extraction, and document processing orchestration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from io import BytesIO
from pathlib import Path

# Test the processing pipeline
from app.modules.document_management.processing.document_processor import (
    DocumentProcessor, ProcessingResult, get_document_processor
)
from app.modules.document_management.processing.ocr_service import (
    OCRService, OCRResult, TesseractOCREngine
)
from app.modules.document_management.processing.text_extractor import (
    TextExtractorService, ExtractionResult, PDFTextExtractor
)


class TestDocumentProcessor:
    """Test document processing orchestration."""
    
    @pytest.fixture
    def mock_ocr_service(self):
        """Mock OCR service for testing."""
        ocr_service = Mock(spec=OCRService)
        ocr_service.is_supported_format = Mock(return_value=True)
        ocr_service.process_document = AsyncMock(return_value=OCRResult(
            text="OCR extracted text content",
            confidence=85.0,
            language="eng",
            processing_time_ms=1000,
            page_count=1,
            metadata={"engine": "tesseract"}
        ))
        return ocr_service
    
    @pytest.fixture
    def mock_text_extractor(self):
        """Mock text extractor service for testing."""
        extractor = Mock(spec=TextExtractorService)
        extractor._get_extractor_for_format = Mock(return_value=Mock())
        extractor.extract_text = AsyncMock(return_value=ExtractionResult(
            text="Extracted text content from document",
            format="pdf",
            metadata={"page_count": 2},
            extraction_method="pymupdf",
            success=True
        ))
        extractor.get_supported_formats = Mock(return_value=[
            "application/pdf", "text/plain"
        ])
        return extractor
    
    @pytest.fixture
    def document_processor(self, mock_ocr_service, mock_text_extractor):
        """Create document processor with mocked services."""
        return DocumentProcessor(mock_ocr_service, mock_text_extractor)
    
    @pytest.mark.asyncio
    async def test_process_text_document(self, document_processor):
        """Test processing of plain text document."""
        file_data = b"This is a test document with medical content."
        
        result = await document_processor.process_document(
            file_data=file_data,
            filename="test.txt",
            mime_type="text/plain"
        )
        
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.processing_method == "text_extraction"
        assert result.confidence == 95.0
        assert "Extracted text content" in result.text
        assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_process_image_document(self, document_processor):
        """Test processing of image document (uses OCR)."""
        file_data = b"fake_image_data"  # Mock image data
        
        result = await document_processor.process_document(
            file_data=file_data,
            filename="scan.jpg",
            mime_type="image/jpeg"
        )
        
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.processing_method == "ocr"
        assert result.confidence == 85.0
        assert "OCR extracted text" in result.text
        assert result.ocr_result is not None
    
    @pytest.mark.asyncio
    async def test_process_pdf_hybrid(self, document_processor):
        """Test PDF processing with hybrid approach."""
        file_data = b"fake_pdf_data"
        
        result = await document_processor.process_document(
            file_data=file_data,
            filename="document.pdf",
            mime_type="application/pdf"
        )
        
        assert isinstance(result, ProcessingResult)
        assert result.success is True
        assert result.processing_method in ["hybrid_text_extraction", "hybrid_ocr"]
        assert result.text is not None
        assert len(result.text) > 0
    
    @pytest.mark.asyncio
    async def test_processing_strategy_selection(self, document_processor):
        """Test processing strategy selection logic."""
        # Image format should use OCR
        strategy = document_processor._determine_processing_strategy("image/jpeg", False)
        assert strategy == "ocr"
        
        # Word document should use text extraction
        strategy = document_processor._determine_processing_strategy(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
            False
        )
        assert strategy == "text_extraction"
        
        # PDF should use hybrid
        strategy = document_processor._determine_processing_strategy("application/pdf", False)
        assert strategy == "hybrid"
        
        # OCR preference should override
        strategy = document_processor._determine_processing_strategy("application/pdf", True)
        assert strategy == "ocr"
    
    @pytest.mark.asyncio
    async def test_processing_error_handling(self, document_processor):
        """Test error handling in document processing."""
        # Mock services to raise exceptions
        document_processor.text_extractor.extract_text = AsyncMock(
            side_effect=Exception("Text extraction failed")
        )
        document_processor.ocr_service.process_document = AsyncMock(
            side_effect=Exception("OCR processing failed")
        )
        
        result = await document_processor.process_document(
            file_data=b"test data",
            filename="error.txt",
            mime_type="text/plain"
        )
        
        assert result.success is False
        assert result.error is not None
        assert "failed" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_health_check(self, document_processor):
        """Test document processor health check."""
        health = await document_processor.health_check()
        
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "supported_formats" in health
        assert isinstance(health["supported_formats"], int)
    
    def test_get_supported_formats(self, document_processor):
        """Test getting supported formats."""
        formats = document_processor.get_supported_formats()
        
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "application/pdf" in formats


class TestOCRService:
    """Test OCR service functionality."""
    
    @pytest.fixture
    def mock_ocr_engine(self):
        """Mock OCR engine for testing."""
        engine = Mock()
        engine.extract_text_from_image = AsyncMock(return_value=OCRResult(
            text="Mocked OCR text from image",
            confidence=90.0,
            language="eng",
            processing_time_ms=500,
            page_count=1,
            metadata={"engine": "mock"}
        ))
        engine.extract_text_from_pdf = AsyncMock(return_value=OCRResult(
            text="Mocked OCR text from PDF",
            confidence=88.0,
            language="eng",
            processing_time_ms=1200,
            page_count=2,
            metadata={"engine": "mock"}
        ))
        return engine
    
    @pytest.fixture
    def ocr_service(self, mock_ocr_engine):
        """Create OCR service with mocked engine."""
        return OCRService(mock_ocr_engine)
    
    @pytest.mark.asyncio
    async def test_process_image_document(self, ocr_service):
        """Test OCR processing of image document."""
        file_data = b"fake_image_data"
        
        result = await ocr_service.process_document(
            file_data=file_data,
            mime_type="image/jpeg"
        )
        
        assert isinstance(result, OCRResult)
        assert result.error is None
        assert "Mocked OCR text from image" in result.text
        assert result.confidence == 90.0
    
    @pytest.mark.asyncio
    async def test_process_pdf_document(self, ocr_service):
        """Test OCR processing of PDF document."""
        file_data = b"fake_pdf_data"
        
        result = await ocr_service.process_document(
            file_data=file_data,
            mime_type="application/pdf"
        )
        
        assert isinstance(result, OCRResult)
        assert result.error is None
        assert "Mocked OCR text from PDF" in result.text
        assert result.confidence == 88.0
        assert result.page_count == 2
    
    @pytest.mark.asyncio
    async def test_unsupported_format(self, ocr_service):
        """Test OCR with unsupported format."""
        file_data = b"fake_data"
        
        result = await ocr_service.process_document(
            file_data=file_data,
            mime_type="application/unknown"
        )
        
        assert isinstance(result, OCRResult)
        assert result.error is not None
        assert result.confidence == 0.0
        assert result.text == ""
    
    def test_supported_formats(self, ocr_service):
        """Test supported format checking."""
        assert ocr_service.is_supported_format("application/pdf") is True
        assert ocr_service.is_supported_format("image/jpeg") is True
        assert ocr_service.is_supported_format("image/png") is True
        assert ocr_service.is_supported_format("text/plain") is False
        assert ocr_service.is_supported_format("application/unknown") is False


class TestTextExtractorService:
    """Test text extraction service."""
    
    @pytest.fixture
    def mock_extractors(self):
        """Mock text extractors."""
        pdf_extractor = Mock()
        pdf_extractor.supports_format = Mock(return_value=True)
        pdf_extractor.extract_text = AsyncMock(return_value=ExtractionResult(
            text="PDF extracted text content",
            format="pdf",
            metadata={"page_count": 3},
            extraction_method="pymupdf",
            success=True
        ))
        
        text_extractor = Mock()
        text_extractor.supports_format = Mock(return_value=True)
        text_extractor.extract_text = AsyncMock(return_value=ExtractionResult(
            text="Plain text content",
            format="text",
            metadata={"encoding": "utf-8"},
            extraction_method="direct_decode",
            success=True
        ))
        
        return [pdf_extractor, text_extractor]
    
    @pytest.fixture
    def text_extractor_service(self, mock_extractors):
        """Create text extractor service with mocked extractors."""
        return TextExtractorService(mock_extractors)
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text(self, text_extractor_service):
        """Test PDF text extraction."""
        file_data = b"fake_pdf_data"
        
        result = await text_extractor_service.extract_text(
            file_data=file_data,
            mime_type="application/pdf",
            filename="test.pdf"
        )
        
        assert isinstance(result, ExtractionResult)
        assert result.success is True
        assert "PDF extracted text content" in result.text
        assert result.format == "pdf"
        assert result.extraction_method == "pymupdf"
    
    @pytest.mark.asyncio
    async def test_extract_plain_text(self, text_extractor_service):
        """Test plain text extraction."""
        file_data = b"This is plain text content"
        
        result = await text_extractor_service.extract_text(
            file_data=file_data,
            mime_type="text/plain",
            filename="test.txt"
        )
        
        assert isinstance(result, ExtractionResult)
        assert result.success is True
        assert "Plain text content" in result.text
        assert result.format == "text"
    
    @pytest.mark.asyncio
    async def test_unsupported_format(self, text_extractor_service):
        """Test text extraction with unsupported format."""
        # Mock no extractor found
        text_extractor_service._get_extractor_for_format = Mock(return_value=None)
        
        file_data = b"unknown data"
        
        result = await text_extractor_service.extract_text(
            file_data=file_data,
            mime_type="application/unknown",
            filename="unknown.xyz"
        )
        
        assert isinstance(result, ExtractionResult)
        assert result.success is False
        assert result.error is not None
        assert "No extractor available" in result.error


class TestTesseractOCREngine:
    """Test Tesseract OCR engine (with fallback for Windows)."""
    
    @pytest.fixture
    def tesseract_engine(self):
        """Create Tesseract OCR engine."""
        return TesseractOCREngine()
    
    @pytest.mark.asyncio
    async def test_fallback_ocr_image(self, tesseract_engine):
        """Test fallback OCR when Tesseract is not available."""
        file_data = b"fake_image_data"
        
        result = await tesseract_engine.extract_text_from_image(file_data)
        
        assert isinstance(result, OCRResult)
        # Should either work with Tesseract or use fallback
        assert result.text is not None
        assert result.confidence > 0
        assert result.processing_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_pdf_processing(self, tesseract_engine):
        """Test PDF OCR processing."""
        # Create a minimal fake PDF data
        file_data = b"%PDF-1.4 fake pdf content"
        
        result = await tesseract_engine.extract_text_from_pdf(file_data)
        
        assert isinstance(result, OCRResult)
        # May fail due to invalid PDF, but should handle gracefully
        assert result.processing_time_ms >= 0


class TestIntegration:
    """Integration tests for document processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self):
        """Test complete document processing pipeline."""
        processor = get_document_processor()
        
        # Test with simple text document
        file_data = b"This is a medical document with patient information."
        
        result = await processor.process_document(
            file_data=file_data,
            filename="medical_record.txt",
            mime_type="text/plain"
        )
        
        assert isinstance(result, ProcessingResult)
        assert result.processing_time_ms > 0
        assert result.metadata is not None
    
    @pytest.mark.asyncio
    async def test_processing_pipeline_health(self):
        """Test health of processing pipeline."""
        processor = get_document_processor()
        
        health = await processor.health_check()
        
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_factory_functions(self):
        """Test factory functions create proper instances."""
        from app.modules.document_management.processing.ocr_service import get_ocr_service
        from app.modules.document_management.processing.text_extractor import get_text_extractor_service
        from app.modules.document_management.processing.document_processor import get_document_processor
        
        ocr_service = get_ocr_service()
        assert isinstance(ocr_service, OCRService)
        
        text_extractor = get_text_extractor_service()
        assert isinstance(text_extractor, TextExtractorService)
        
        processor = get_document_processor()
        assert isinstance(processor, DocumentProcessor)


if __name__ == "__main__":
    # Run specific tests for debugging
    pytest.main([__file__, "-v", "-s"])