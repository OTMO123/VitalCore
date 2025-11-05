"""
Comprehensive Test Suite for File Upload Security

Tests all security controls for file upload functionality:
- File type validation
- File size limits
- MIME type verification
- Filename sanitization
- Path traversal prevention
- Malware scanning hooks
- Rate limiting
"""

import pytest
from pathlib import Path
from typing import Tuple
from unittest.mock import AsyncMock, Mock, patch

from app.core.validators import FileValidator, file_validator
from app.core.security_scanning import (
    NoOpMalwareScanner,
    ClamAVScanner,
    HashBasedScanner,
    scan_uploaded_file,
    configure_scanner
)


@pytest.mark.security
class TestFileTypeValidation:
    """Test file type validation with whitelist approach."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    def test_accept_pdf_files(self, validator):
        """Should accept valid PDF files."""
        is_valid, error = validator.validate_file_type("report.pdf")
        assert is_valid is True
        assert error is None

    def test_accept_dicom_files(self, validator):
        """Should accept DICOM medical images."""
        is_valid, error = validator.validate_file_type("scan.dcm")
        assert is_valid is True
        assert error is None

    def test_accept_jpeg_files(self, validator):
        """Should accept JPEG images."""
        is_valid, error = validator.validate_file_type("xray.jpg")
        assert is_valid is True
        assert error is None

        is_valid, error = validator.validate_file_type("xray.jpeg")
        assert is_valid is True
        assert error is None

    def test_accept_png_files(self, validator):
        """Should accept PNG images."""
        is_valid, error = validator.validate_file_type("scan.png")
        assert is_valid is True
        assert error is None

    def test_accept_xml_files(self, validator):
        """Should accept XML files (FHIR/CDA)."""
        is_valid, error = validator.validate_file_type("patient.xml")
        assert is_valid is True
        assert error is None

    def test_accept_json_files(self, validator):
        """Should accept JSON files (FHIR)."""
        is_valid, error = validator.validate_file_type("bundle.json")
        assert is_valid is True
        assert error is None

    def test_accept_hl7_files(self, validator):
        """Should accept HL7 message files."""
        is_valid, error = validator.validate_file_type("adt.hl7")
        assert is_valid is True
        assert error is None

    def test_accept_txt_files(self, validator):
        """Should accept text files."""
        is_valid, error = validator.validate_file_type("results.txt")
        assert is_valid is True
        assert error is None

    def test_reject_executable_files(self, validator):
        """Should reject executable files."""
        dangerous_extensions = [
            "malware.exe",
            "script.sh",
            "batch.bat",
            "command.cmd",
            "library.dll",
            "library.so"
        ]

        for filename in dangerous_extensions:
            is_valid, error = validator.validate_file_type(filename)
            assert is_valid is False, f"Should reject {filename}"
            assert error is not None
            assert "blocked for security reasons" in error.lower() or "not allowed" in error.lower()

    def test_reject_script_files(self, validator):
        """Should reject script files."""
        script_files = [
            "script.js",
            "script.vbs",
            "script.ps1",
            "script.php",
            "script.asp",
            "script.jsp"
        ]

        for filename in script_files:
            is_valid, error = validator.validate_file_type(filename)
            assert is_valid is False, f"Should reject {filename}"
            assert error is not None

    def test_reject_archive_executable_files(self, validator):
        """Should reject Java archives and installers."""
        dangerous_files = [
            "app.jar",
            "app.war",
            "install.msi",
            "package.deb",
            "package.rpm"
        ]

        for filename in dangerous_files:
            is_valid, error = validator.validate_file_type(filename)
            assert is_valid is False, f"Should reject {filename}"
            assert error is not None

    def test_reject_unknown_extensions(self, validator):
        """Should reject files with unknown extensions."""
        is_valid, error = validator.validate_file_type("document.xyz")
        assert is_valid is False
        assert error is not None
        assert ".xyz" in error


@pytest.mark.security
class TestFileSizeValidation:
    """Test file size limit enforcement."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    def test_accept_small_pdf(self, validator):
        """Should accept PDF under 100MB."""
        # 50 MB file
        is_valid, error = validator.validate_file_size("report.pdf", 50 * 1024 * 1024)
        assert is_valid is True
        assert error is None

    def test_reject_large_pdf(self, validator):
        """Should reject PDF over 100MB."""
        # 150 MB file
        is_valid, error = validator.validate_file_size("report.pdf", 150 * 1024 * 1024)
        assert is_valid is False
        assert error is not None
        assert "too large" in error.lower()
        assert "150" in error or "150.0" in error

    def test_accept_large_dicom(self, validator):
        """Should accept DICOM up to 500MB."""
        # 400 MB DICOM file
        is_valid, error = validator.validate_file_size("scan.dcm", 400 * 1024 * 1024)
        assert is_valid is True
        assert error is None

    def test_reject_huge_dicom(self, validator):
        """Should reject DICOM over 500MB."""
        # 600 MB file
        is_valid, error = validator.validate_file_size("scan.dcm", 600 * 1024 * 1024)
        assert is_valid is False
        assert error is not None
        assert "too large" in error.lower()

    def test_reject_empty_files(self, validator):
        """Should reject empty files."""
        is_valid, error = validator.validate_file_size("empty.pdf", 0)
        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()

    def test_accept_hl7_under_limit(self, validator):
        """Should accept HL7 files under 10MB."""
        # 5 MB HL7 file
        is_valid, error = validator.validate_file_size("message.hl7", 5 * 1024 * 1024)
        assert is_valid is True
        assert error is None

    def test_reject_hl7_over_limit(self, validator):
        """Should reject HL7 files over 10MB."""
        # 15 MB HL7 file
        is_valid, error = validator.validate_file_size("message.hl7", 15 * 1024 * 1024)
        assert is_valid is False
        assert error is not None

    def test_default_size_limit(self, validator):
        """Should use default limit for unknown extensions."""
        # 60 MB file with unknown extension (default is 50MB)
        is_valid, error = validator.validate_file_size("file.unknown", 60 * 1024 * 1024)
        assert is_valid is False
        assert error is not None


@pytest.mark.security
class TestFilenameSanitization:
    """Test filename sanitization for path traversal prevention."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    def test_sanitize_path_traversal(self, validator):
        """Should remove path traversal attempts."""
        malicious_filenames = [
            "../../etc/passwd",
            "../../../windows/system32/config",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32\\config"
        ]

        for filename in malicious_filenames:
            sanitized = validator.sanitize_filename(filename)
            assert ".." not in sanitized, f"Should remove .. from {filename}"
            assert "/" not in sanitized or sanitized.count("/") == 0
            assert "\\" not in sanitized

    def test_sanitize_dangerous_characters(self, validator):
        """Should remove dangerous characters."""
        dangerous_filenames = [
            "test<script>.pdf",
            "file;rm -rf.pdf",
            "doc|command.pdf",
            "file&command.pdf",
            "doc`whoami`.pdf"
        ]

        for filename in dangerous_filenames:
            sanitized = validator.sanitize_filename(filename)
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert "|" not in sanitized
            assert ";" not in sanitized
            assert "`" not in sanitized

    def test_sanitize_null_bytes(self, validator):
        """Should remove null bytes."""
        filename_with_null = "test\x00.pdf"
        sanitized = validator.sanitize_filename(filename_with_null)
        assert "\x00" not in sanitized

    def test_preserve_extension(self, validator):
        """Should preserve file extension."""
        sanitized = validator.sanitize_filename("document.pdf")
        assert sanitized.endswith(".pdf")

        sanitized = validator.sanitize_filename("../../../etc/passwd.pdf")
        assert sanitized.endswith(".pdf")

    def test_limit_filename_length(self, validator):
        """Should limit filename length."""
        long_filename = "a" * 300 + ".pdf"
        sanitized = validator.sanitize_filename(long_filename)
        assert len(sanitized) <= 255

    def test_handle_spaces_and_special_chars(self, validator):
        """Should handle spaces and special characters."""
        filename = "My Document (Final) v2.1.pdf"
        sanitized = validator.sanitize_filename(filename)
        assert sanitized.endswith(".pdf")
        # Should have alphanumeric, underscores, and dots
        assert all(c.isalnum() or c in "._- " for c in sanitized)

    def test_normal_filenames_unchanged(self, validator):
        """Should leave normal filenames mostly unchanged."""
        normal_files = [
            "report.pdf",
            "scan-2024.dcm",
            "patient_record.json"
        ]

        for filename in normal_files:
            sanitized = validator.sanitize_filename(filename)
            # Should be similar (allowing underscore normalization)
            assert Path(sanitized).suffix == Path(filename).suffix


@pytest.mark.security
class TestMIMETypeValidation:
    """Test MIME type validation with magic number checks."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    def test_validate_pdf_mime(self, validator):
        """Should validate PDF magic numbers."""
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        is_valid, error = validator._basic_magic_check(pdf_content, '.pdf')
        assert is_valid is True

    def test_validate_jpeg_mime(self, validator):
        """Should validate JPEG magic numbers."""
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        is_valid, error = validator._basic_magic_check(jpeg_content, '.jpg')
        assert is_valid is True

    def test_validate_png_mime(self, validator):
        """Should validate PNG magic numbers."""
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        is_valid, error = validator._basic_magic_check(png_content, '.png')
        assert is_valid is True

    def test_reject_mismatched_mime(self, validator):
        """Should reject files with mismatched extensions and content."""
        # PDF header but .jpg extension
        pdf_content = b'%PDF-1.4\n'
        is_valid, error = validator._basic_magic_check(pdf_content, '.jpg')
        assert is_valid is False
        assert error is not None


@pytest.mark.security
class TestComprehensiveUploadValidation:
    """Test comprehensive upload validation combining all checks."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    def test_validate_valid_pdf_upload(self, validator):
        """Should accept valid PDF upload."""
        pdf_content = b'%PDF-1.4\n' + b'a' * 1000
        is_valid, error, sanitized = validator.validate_upload("report.pdf", pdf_content)

        assert is_valid is True
        assert error is None
        assert sanitized == "report.pdf"

    def test_reject_dangerous_extension(self, validator):
        """Should reject dangerous file types."""
        content = b'content'
        is_valid, error, sanitized = validator.validate_upload("malware.exe", content)

        assert is_valid is False
        assert error is not None

    def test_reject_oversized_file(self, validator):
        """Should reject oversized files."""
        # 150 MB PDF (over 100MB limit)
        large_content = b'%PDF-1.4\n' + b'a' * (150 * 1024 * 1024)
        is_valid, error, sanitized = validator.validate_upload("large.pdf", large_content)

        assert is_valid is False
        assert error is not None
        assert "too large" in error.lower()

    def test_sanitize_filename_during_validation(self, validator):
        """Should sanitize filename during comprehensive validation."""
        content = b'%PDF-1.4\n' + b'a' * 1000
        is_valid, error, sanitized = validator.validate_upload(
            "../../etc/passwd.pdf",
            content
        )

        assert is_valid is True
        assert ".." not in sanitized
        assert sanitized.endswith(".pdf")


@pytest.mark.security
class TestMalwareScanning:
    """Test malware scanning infrastructure."""

    @pytest.mark.asyncio
    async def test_noop_scanner_warns(self):
        """NoOp scanner should log warning and pass through."""
        scanner = NoOpMalwareScanner()
        is_clean, threat = await scanner.scan_file(b"content", "test.pdf")

        assert is_clean is True
        assert threat is None

    @pytest.mark.asyncio
    async def test_hash_based_scanner_clean(self):
        """Hash-based scanner should pass clean files."""
        scanner = HashBasedScanner()
        is_clean, threat = await scanner.scan_file(b"clean content", "test.pdf")

        assert is_clean is True
        assert threat is None

    @pytest.mark.asyncio
    async def test_hash_based_scanner_detects_malware(self):
        """Hash-based scanner should detect known malware hashes."""
        scanner = HashBasedScanner()

        # Add a malware hash
        import hashlib
        malware_content = b"malicious payload"
        malware_hash = hashlib.sha256(malware_content).hexdigest()
        scanner.add_malware_hash(malware_hash)

        # Try to scan the malware
        is_clean, threat = await scanner.scan_file(malware_content, "malware.exe")

        assert is_clean is False
        assert threat is not None
        assert "known malware" in threat.lower()

    @pytest.mark.asyncio
    async def test_scanner_configuration(self):
        """Should allow scanner configuration."""
        from app.core.security_scanning import configure_scanner, get_scanner

        # Configure hash-based scanner
        hash_scanner = HashBasedScanner()
        configure_scanner(hash_scanner)

        # Get configured scanner
        scanner = get_scanner()
        assert isinstance(scanner, HashBasedScanner)

    @pytest.mark.asyncio
    async def test_scan_uploaded_file_wrapper(self):
        """Test the main scan_uploaded_file function."""
        # Should use configured scanner
        from app.core.security_scanning import configure_scanner

        # Configure NoOp scanner
        configure_scanner(NoOpMalwareScanner())

        is_clean, threat = await scan_uploaded_file(b"content", "test.pdf")

        assert is_clean is True
        assert threat is None


@pytest.mark.security
class TestRateLimiting:
    """Test rate limiting for file uploads."""

    def test_rate_limiter_allows_under_limit(self):
        """Should allow requests under rate limit."""
        from app.core.rate_limiting import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()

        # First 5 requests should be allowed
        for i in range(5):
            allowed = limiter.is_allowed("test_user", max_requests=10, window_seconds=60)
            assert allowed is True

    def test_rate_limiter_blocks_over_limit(self):
        """Should block requests over rate limit."""
        from app.core.rate_limiting import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()

        # Make 10 requests (limit)
        for i in range(10):
            allowed = limiter.is_allowed("test_user", max_requests=10, window_seconds=60)
            assert allowed is True

        # 11th request should be blocked
        allowed = limiter.is_allowed("test_user", max_requests=10, window_seconds=60)
        assert allowed is False

    def test_rate_limiter_window_expiry(self):
        """Should reset after time window expires."""
        import time
        from app.core.rate_limiting import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()

        # Make 10 requests with 1-second window
        for i in range(10):
            allowed = limiter.is_allowed("test_user", max_requests=10, window_seconds=1)
            assert allowed is True

        # Should be blocked immediately
        allowed = limiter.is_allowed("test_user", max_requests=10, window_seconds=1)
        assert allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        allowed = limiter.is_allowed("test_user", max_requests=10, window_seconds=1)
        assert allowed is True


@pytest.mark.security
class TestSecurityIntegration:
    """Integration tests for combined security features."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    @pytest.mark.asyncio
    async def test_complete_security_pipeline(self, validator):
        """Test complete security validation pipeline."""
        # Create valid PDF content
        pdf_content = b'%PDF-1.4\n' + b'Test PDF content' * 100

        # Step 1: Validate upload (type, size, sanitize)
        is_valid, error, sanitized = validator.validate_upload(
            "patient_report.pdf",
            pdf_content
        )
        assert is_valid is True
        assert sanitized == "patient_report.pdf"

        # Step 2: Malware scan
        is_clean, threat = await scan_uploaded_file(pdf_content, sanitized)
        assert is_clean is True

        # If all checks pass, file should be safe for storage
        assert is_valid and is_clean

    @pytest.mark.asyncio
    async def test_security_pipeline_blocks_malicious(self, validator):
        """Test security pipeline blocks malicious files."""
        # Create malicious executable
        exe_content = b'MZ\x90\x00' + b'malicious code'

        # Should be blocked by file type validation
        is_valid, error, sanitized = validator.validate_upload(
            "malware.exe",
            exe_content
        )
        assert is_valid is False
        assert error is not None


@pytest.mark.security
class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    def test_empty_filename(self, validator):
        """Should handle empty filename gracefully."""
        sanitized = validator.sanitize_filename("")
        assert sanitized != ""  # Should return a default

    def test_filename_with_only_extension(self, validator):
        """Should handle filename with only extension."""
        sanitized = validator.sanitize_filename(".pdf")
        assert sanitized.endswith(".pdf")

    def test_very_long_extension(self, validator):
        """Should handle very long extensions."""
        is_valid, error = validator.validate_file_type("file.verylongextension")
        assert is_valid is False

    def test_case_insensitive_extensions(self, validator):
        """Should handle uppercase extensions."""
        is_valid, error = validator.validate_file_type("REPORT.PDF")
        assert is_valid is True

        is_valid, error = validator.validate_file_type("SCAN.DCM")
        assert is_valid is True


# Performance tests (optional)
@pytest.mark.performance
class TestSecurityPerformance:
    """Test performance of security checks."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FileValidator()

    def test_validation_performance(self, validator, benchmark):
        """Benchmark validation performance."""
        content = b'%PDF-1.4\n' + b'a' * (10 * 1024 * 1024)  # 10 MB

        result = benchmark(
            validator.validate_upload,
            "test.pdf",
            content
        )

        is_valid, error, sanitized = result
        assert is_valid is True
