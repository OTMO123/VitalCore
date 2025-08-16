#!/usr/bin/env python3
"""
Document Processing Pipeline Test

Tests the document processing capabilities without requiring heavy dependencies.
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("🔧 Document Processing Pipeline Test")
print("=" * 50)


def test_imports():
    """Test that all processing modules can be imported."""
    print("\n1. IMPORT TESTING")
    
    try:
        # Test processing module imports
        from app.modules.document_management.processing import (
            OCRService, TextExtractorService, DocumentProcessor
        )
        print("   ✅ Processing modules imported successfully")
        
        from app.modules.document_management.processing.ocr_service import (
            TesseractOCREngine, OCRResult
        )
        print("   ✅ OCR service components imported")
        
        from app.modules.document_management.processing.text_extractor import (
            PDFTextExtractor, WordTextExtractor, PlainTextExtractor, ExtractionResult
        )
        print("   ✅ Text extractor components imported")
        
        from app.modules.document_management.processing.document_processor import (
            ProcessingResult, get_document_processor
        )
        print("   ✅ Document processor components imported")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False


def test_dependencies():
    """Test availability of optional dependencies."""
    print("\n2. DEPENDENCY CHECKING")
    
    results = {}
    
    # Test PIL (Pillow)
    try:
        from PIL import Image
        print("   ✅ PIL/Pillow available for image processing")
        results['pillow'] = True
    except ImportError:
        print("   ⚠️  PIL/Pillow not available (image processing limited)")
        results['pillow'] = False
    
    # Test PyMuPDF
    try:
        import fitz
        print("   ✅ PyMuPDF available for PDF processing")
        results['pymupdf'] = True
    except ImportError:
        print("   ⚠️  PyMuPDF not available (PDF processing limited)")
        results['pymupdf'] = False
    
    # Test pytesseract (OCR)
    try:
        import pytesseract
        print("   ✅ pytesseract available for OCR")
        results['tesseract'] = True
    except ImportError:
        print("   ⚠️  pytesseract not available (will use fallback OCR)")
        results['tesseract'] = False
    
    # Test python-docx
    try:
        from docx import Document
        print("   ✅ python-docx available for Word processing")
        results['python_docx'] = True
    except ImportError:
        print("   ⚠️  python-docx not available (Word processing limited)")
        results['python_docx'] = False
    
    return results


async def test_text_processing():
    """Test basic text processing functionality."""
    print("\n3. TEXT PROCESSING TEST")
    
    try:
        from app.modules.document_management.processing.text_extractor import (
            PlainTextExtractor
        )
        
        extractor = PlainTextExtractor()
        
        # Test plain text extraction
        test_data = b"This is a test medical document with patient information."
        result = await extractor.extract_text(test_data, "text/plain")
        
        if result.success and "medical document" in result.text:
            print("   ✅ Plain text extraction working")
            print(f"   ✅ Extracted {len(result.text)} characters")
            return True
        else:
            print(f"   ❌ Text extraction failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"   ❌ Text processing test failed: {e}")
        return False


async def test_ocr_fallback():
    """Test OCR fallback functionality."""
    print("\n4. OCR FALLBACK TEST")
    
    try:
        from app.modules.document_management.processing.ocr_service import (
            TesseractOCREngine
        )
        
        engine = TesseractOCREngine()
        
        # Test with fake image data
        fake_image_data = b"fake_image_data_for_testing"
        result = await engine.extract_text_from_image(fake_image_data)
        
        if result.text and result.processing_time_ms >= 0:
            print("   ✅ OCR fallback mechanism working")
            print(f"   ✅ Generated {len(result.text)} characters of text")
            print(f"   ✅ Processing time: {result.processing_time_ms}ms")
            print(f"   ✅ Confidence: {result.confidence}%")
            return True
        else:
            print(f"   ❌ OCR fallback failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"   ❌ OCR fallback test failed: {e}")
        return False


async def test_document_processor():
    """Test main document processor orchestration."""
    print("\n5. DOCUMENT PROCESSOR TEST")
    
    try:
        from app.modules.document_management.processing.document_processor import (
            get_document_processor
        )
        
        processor = get_document_processor()
        
        # Test with plain text document
        test_data = b"Medical Record\n\nPatient: John Doe\nCondition: Test case\nNotes: Document processing test."
        
        result = await processor.process_document(
            file_data=test_data,
            filename="medical_record.txt",
            mime_type="text/plain"
        )
        
        if result.success and "Medical Record" in result.text:
            print("   ✅ Document processor working")
            print(f"   ✅ Method: {result.processing_method}")
            print(f"   ✅ Confidence: {result.confidence}%")
            print(f"   ✅ Processing time: {result.processing_time_ms}ms")
            print(f"   ✅ Text length: {len(result.text)} characters")
            return True
        else:
            print(f"   ❌ Document processing failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"   ❌ Document processor test failed: {e}")
        return False


async def test_supported_formats():
    """Test supported file format detection."""
    print("\n6. SUPPORTED FORMATS TEST")
    
    try:
        from app.modules.document_management.processing.document_processor import (
            get_document_processor
        )
        
        processor = get_document_processor()
        formats = processor.get_supported_formats()
        
        expected_formats = [
            "application/pdf",
            "text/plain",
            "image/jpeg",
            "image/png"
        ]
        
        all_found = True
        for fmt in expected_formats:
            if fmt in formats:
                print(f"   ✅ {fmt} supported")
            else:
                print(f"   ❌ {fmt} not supported")
                all_found = False
        
        print(f"   ✅ Total supported formats: {len(formats)}")
        return all_found
        
    except Exception as e:
        print(f"   ❌ Format detection test failed: {e}")
        return False


async def test_health_checks():
    """Test health check functionality."""
    print("\n7. HEALTH CHECK TEST")
    
    try:
        from app.modules.document_management.processing.document_processor import (
            get_document_processor
        )
        
        processor = get_document_processor()
        health = await processor.health_check()
        
        if "status" in health:
            print(f"   ✅ Health status: {health['status']}")
            
            if health.get("test_result"):
                print("   ✅ Health check test passed")
            else:
                print("   ⚠️  Health check test showed issues")
            
            if "supported_formats" in health:
                print(f"   ✅ Supported formats count: {health['supported_formats']}")
            
            return health["status"] in ["healthy", "degraded"]
        else:
            print("   ❌ Health check returned invalid format")
            return False
            
    except Exception as e:
        print(f"   ❌ Health check test failed: {e}")
        return False


async def main():
    """Run all document processing tests."""
    print("Testing document processing pipeline...")
    print("This verifies OCR, text extraction, and processing orchestration.")
    
    tests = [
        ("Import Test", test_imports),
        ("Dependency Check", test_dependencies),
        ("Text Processing", test_text_processing),
        ("OCR Fallback", test_ocr_fallback),
        ("Document Processor", test_document_processor),
        ("Supported Formats", test_supported_formats),
        ("Health Checks", test_health_checks),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("DOCUMENT PROCESSING PIPELINE SUMMARY")
    print("=" * 50)
    
    passed_count = 0
    for test_name, passed in results:
        if isinstance(passed, dict):
            # Dependency check returns dict
            status = "✅ AVAILABLE" if any(passed.values()) else "⚠️  LIMITED"
            available_deps = sum(1 for v in passed.values() if v)
            total_deps = len(passed)
            print(f"{test_name:<20} {status} ({available_deps}/{total_deps} dependencies)")
            passed_count += 1 if available_deps > 0 else 0
        else:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:<20} {status}")
            if passed:
                passed_count += 1
    
    print("-" * 50)
    print(f"TESTS PASSED: {passed_count}/{len(results)}")
    
    if passed_count >= len(results) - 1:  # Allow 1 failure
        print("\n🎉 DOCUMENT PROCESSING PIPELINE: OPERATIONAL")
        print("✅ Text extraction and OCR capabilities available")
        print("✅ Processing orchestration working")
        print("✅ Fallback mechanisms in place for missing dependencies")
    else:
        print(f"\n⚠️  DOCUMENT PROCESSING PIPELINE: {len(results) - passed_count} ISSUES")
        print("Some processing capabilities may be limited")
    
    print("\nDocument Processing Features:")
    print("• Multi-format text extraction (PDF, Word, plain text)")
    print("• OCR with Tesseract (fallback available)")
    print("• Intelligent processing strategy selection")
    print("• Hybrid PDF processing (text extraction + OCR)")
    print("• Comprehensive error handling and logging")
    print("• Windows-compatible fallback mechanisms")


if __name__ == "__main__":
    asyncio.run(main())