"""
File Upload Security Validators

Production-grade file validation for healthcare document management.
Implements HIPAA-compliant security controls for file uploads.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)

# Healthcare-specific allowed file types (whitelist approach)
ALLOWED_EXTENSIONS = {
    ".dcm",  # DICOM medical images
    ".jpg",  # JPEG images
    ".jpeg",  # JPEG images (alt extension)
    ".png",  # PNG images
    ".pdf",  # PDF documents
    ".xml",  # XML (FHIR/CDA)
    ".json",  # JSON (FHIR)
    ".hl7",  # HL7 messages
    ".txt",  # Text files (lab results)
}

# MIME type whitelist for content validation
ALLOWED_MIME_TYPES = {
    "application/dicom",  # DICOM
    "image/jpeg",  # JPEG
    "image/png",  # PNG
    "application/pdf",  # PDF
    "application/xml",  # XML
    "text/xml",  # XML (text variant)
    "application/json",  # JSON
    "application/hl7-v2",  # HL7 v2
    "text/plain",  # Plain text
    "application/octet-stream",  # Generic binary (for DICOM)
}

# File size limits by extension (in bytes)
MAX_FILE_SIZES = {
    ".dcm": 500 * 1024 * 1024,  # 500 MB for DICOM
    ".pdf": 100 * 1024 * 1024,  # 100 MB for PDFs
    ".hl7": 10 * 1024 * 1024,  # 10 MB for HL7
    ".xml": 10 * 1024 * 1024,  # 10 MB for XML
    ".json": 10 * 1024 * 1024,  # 10 MB for JSON
    ".jpg": 50 * 1024 * 1024,  # 50 MB for JPEG
    ".jpeg": 50 * 1024 * 1024,  # 50 MB for JPEG
    ".png": 50 * 1024 * 1024,  # 50 MB for PNG
    ".txt": 10 * 1024 * 1024,  # 10 MB for text
    "default": 50 * 1024 * 1024,  # 50 MB default
}

# Dangerous file patterns to block
DANGEROUS_PATTERNS = [
    r"\.exe$",
    r"\.sh$",
    r"\.bat$",
    r"\.cmd$",  # Executables
    r"\.dll$",
    r"\.so$",
    r"\.dylib$",  # Libraries
    r"\.js$",
    r"\.vbs$",
    r"\.ps1$",  # Scripts
    r"\.jar$",
    r"\.war$",
    r"\.ear$",  # Java archives
    r"\.app$",
    r"\.deb$",
    r"\.rpm$",  # Applications
    r"\.msi$",
    r"\.pkg$",  # Installers
    r"\.php$",
    r"\.asp$",
    r"\.jsp$",  # Web scripts
]


class FileValidator:
    """
    Healthcare file upload validator with comprehensive security checks.

    Security features:
    - Extension whitelist validation
    - MIME type verification (magic number check)
    - File size enforcement
    - Filename sanitization
    - Path traversal prevention
    - Malicious pattern detection
    """

    def __init__(self):
        self.logger = logger.bind(component="FileValidator")

    def validate_file_type(
        self, filename: str, content: Optional[bytes] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file type by extension and optionally by content.

        Args:
            filename: Original filename from upload
            content: Optional file content for MIME type detection

        Returns:
            (is_valid, error_message)

        Examples:
            >>> validator = FileValidator()
            >>> is_valid, error = validator.validate_file_type("report.pdf")
            >>> assert is_valid is True

            >>> is_valid, error = validator.validate_file_type("malware.exe")
            >>> assert is_valid is False
        """
        try:
            # Extract extension
            file_ext = Path(filename).suffix.lower()

            # Check for dangerous patterns first
            for pattern in DANGEROUS_PATTERNS:
                if re.search(pattern, filename.lower()):
                    self.logger.warning(
                        "Dangerous file pattern detected",
                        filename=filename,
                        pattern=pattern,
                    )
                    return False, f"File type blocked for security reasons: {file_ext}"

            # Check extension whitelist
            if file_ext not in ALLOWED_EXTENSIONS:
                self.logger.warning(
                    "File extension not allowed",
                    filename=filename,
                    extension=file_ext,
                    allowed_extensions=list(ALLOWED_EXTENSIONS),
                )
                return False, (
                    f"File type not allowed. Extension: {file_ext}. "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                )

            # MIME type validation (if content provided)
            if content:
                mime_valid, mime_error = self._validate_mime_type(content, file_ext)
                if not mime_valid:
                    return False, mime_error

            self.logger.info(
                "File type validation passed", filename=filename, extension=file_ext
            )
            return True, None

        except Exception as e:
            self.logger.error(
                "File type validation error", filename=filename, error=str(e)
            )
            return False, f"File validation error: {str(e)}"

    def _validate_mime_type(
        self, content: bytes, expected_ext: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate MIME type by inspecting file magic numbers.

        This provides defense-in-depth by checking actual file content,
        not just the extension.

        Args:
            content: File content bytes
            expected_ext: Expected file extension

        Returns:
            (is_valid, error_message)
        """
        try:
            # Try to use python-magic if available
            try:
                import magic

                detected_mime = magic.from_buffer(content, mime=True)

                if detected_mime not in ALLOWED_MIME_TYPES:
                    self.logger.warning(
                        "MIME type not allowed",
                        detected_mime=detected_mime,
                        expected_ext=expected_ext,
                    )
                    return False, (
                        f"File content type not allowed. MIME: {detected_mime}"
                    )

                self.logger.debug(
                    "MIME type validation passed",
                    mime_type=detected_mime,
                    extension=expected_ext,
                )

            except ImportError:
                # python-magic not available, use basic magic number checks
                self.logger.warning(
                    "python-magic not available, using basic validation"
                )
                mime_valid, error = self._basic_magic_check(content, expected_ext)
                if not mime_valid:
                    return False, error

            return True, None

        except Exception as e:
            self.logger.error("MIME type validation error", error=str(e))
            # Don't fail on MIME check errors, just log
            return True, None

    def _basic_magic_check(
        self, content: bytes, expected_ext: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Basic magic number validation when python-magic is not available.

        Checks common file signatures to prevent obvious file type mismatches.
        """
        if len(content) < 4:
            return True, None  # Too small to check

        # Magic number signatures
        magic_signatures = {
            ".pdf": [b"%PDF"],
            ".jpg": [b"\xff\xd8\xff"],
            ".jpeg": [b"\xff\xd8\xff"],
            ".png": [b"\x89PNG"],
            ".dcm": [b"DICM"],  # DICOM at offset 128
        }

        expected_signatures = magic_signatures.get(expected_ext, [])
        if not expected_signatures:
            return True, None  # No signature to check

        # Check if content starts with expected signature
        for signature in expected_signatures:
            # For DICOM, check at offset 128
            if expected_ext == ".dcm":
                if len(content) > 132 and content[128:132] == signature:
                    return True, None
            else:
                if content.startswith(signature):
                    return True, None

        self.logger.warning(
            "Magic number mismatch",
            expected_ext=expected_ext,
            first_bytes=content[:10].hex(),
        )
        return False, (f"File content does not match extension {expected_ext}")

    def validate_file_size(
        self, filename: str, size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file size against type-specific limits.

        Args:
            filename: Original filename
            size: File size in bytes

        Returns:
            (is_valid, error_message)

        Examples:
            >>> validator = FileValidator()
            >>> is_valid, error = validator.validate_file_size("scan.dcm", 100_000_000)
            >>> assert is_valid is True

            >>> is_valid, error = validator.validate_file_size("scan.dcm", 600_000_000)
            >>> assert is_valid is False
        """
        try:
            # Get extension
            file_ext = Path(filename).suffix.lower()

            # Get size limit
            max_size = MAX_FILE_SIZES.get(file_ext, MAX_FILE_SIZES["default"])

            # Check size
            if size > max_size:
                size_mb = size / (1024 * 1024)
                max_mb = max_size / (1024 * 1024)

                self.logger.warning(
                    "File size exceeds limit",
                    filename=filename,
                    size_mb=round(size_mb, 2),
                    max_mb=round(max_mb, 2),
                    extension=file_ext,
                )

                return False, (
                    f"File too large. Size: {size_mb:.1f}MB, "
                    f"Max: {max_mb:.1f}MB for {file_ext} files"
                )

            # Check minimum size (prevent empty files)
            if size == 0:
                self.logger.warning("Empty file detected", filename=filename)
                return False, "File is empty"

            self.logger.info(
                "File size validation passed",
                filename=filename,
                size_mb=round(size / (1024 * 1024), 2),
                max_mb=round(max_size / (1024 * 1024), 2),
            )
            return True, None

        except Exception as e:
            self.logger.error(
                "File size validation error", filename=filename, error=str(e)
            )
            return False, f"File size validation error: {str(e)}"

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and injection attacks.

        Security measures:
        - Removes path components (../etc/passwd)
        - Strips dangerous characters
        - Limits filename length
        - Preserves extension

        Args:
            filename: Original filename from user

        Returns:
            Sanitized filename safe for storage

        Examples:
            >>> validator = FileValidator()
            >>> clean = validator.sanitize_filename("../../etc/passwd")
            >>> assert clean == "passwd"

            >>> clean = validator.sanitize_filename("test<script>.pdf")
            >>> assert "<script>" not in clean
        """
        try:
            # Remove path components (security critical!)
            filename = Path(filename).name

            # Remove null bytes
            filename = filename.replace("\x00", "")

            # Split name and extension
            path_obj = Path(filename)
            name = path_obj.stem
            ext = path_obj.suffix

            # Remove or replace dangerous characters
            # Allow only: alphanumeric, spaces, hyphens, underscores, periods
            name = re.sub(r"[^\w\s\-.]", "_", name)

            # Remove leading/trailing dots and spaces
            name = name.strip(". ")

            # Replace multiple spaces/underscores with single
            name = re.sub(r"[\s_]+", "_", name)

            # Limit length (leave room for extension)
            max_name_length = 200
            if len(name) > max_name_length:
                name = name[:max_name_length]

            # Reconstruct filename
            sanitized = f"{name}{ext}"

            # Ensure we have a valid filename
            if not sanitized or sanitized == ext:
                sanitized = f"document_{Path(filename).suffix}"

            if sanitized != filename:
                self.logger.info(
                    "Filename sanitized", original=filename, sanitized=sanitized
                )

            return sanitized

        except Exception as e:
            self.logger.error(
                "Filename sanitization error", filename=filename, error=str(e)
            )
            # Return a safe default
            return f"document_{Path(filename).suffix if filename else '.bin'}"

    def validate_upload(
        self, filename: str, content: bytes
    ) -> Tuple[bool, Optional[str], str]:
        """
        Comprehensive upload validation combining all checks.

        Args:
            filename: Original filename
            content: File content bytes

        Returns:
            (is_valid, error_message, sanitized_filename)

        Examples:
            >>> validator = FileValidator()
            >>> valid, error, clean_name = validator.validate_upload(
            ...     "report.pdf",
            ...     b"%PDF-1.4 content..."
            ... )
            >>> assert valid is True
        """
        try:
            # Step 1: Sanitize filename first
            sanitized_filename = self.sanitize_filename(filename)

            # Step 2: Validate file type
            type_valid, type_error = self.validate_file_type(
                sanitized_filename, content
            )
            if not type_valid:
                return False, type_error, sanitized_filename

            # Step 3: Validate file size
            size_valid, size_error = self.validate_file_size(
                sanitized_filename, len(content)
            )
            if not size_valid:
                return False, size_error, sanitized_filename

            # All checks passed
            self.logger.info(
                "Upload validation passed",
                original_filename=filename,
                sanitized_filename=sanitized_filename,
                file_size=len(content),
            )

            return True, None, sanitized_filename

        except Exception as e:
            self.logger.error(
                "Upload validation error", filename=filename, error=str(e)
            )
            return False, f"Upload validation error: {str(e)}", filename


# Global validator instance
file_validator = FileValidator()


def validate_healthcare_file(
    filename: str, content: bytes
) -> Tuple[bool, Optional[str], str]:
    """
    Convenience function for healthcare file validation.

    Args:
        filename: Original filename
        content: File content bytes

    Returns:
        (is_valid, error_message, sanitized_filename)
    """
    return file_validator.validate_upload(filename, content)
