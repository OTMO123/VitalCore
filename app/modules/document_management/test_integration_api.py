"""
Integration Tests for Document Management API

Tests for full API integration with database and services.
"""

import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.modules.document_management.router import router
from app.modules.document_management.schemas import (
    DocumentUploadRequest, DocumentUpdateRequest, DocumentSearchRequest,
    BulkDeleteRequest, BulkUpdateTagsRequest
)
from app.core.database_unified import DocumentType, Base
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create test database engine."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session."""
    async with AsyncSession(test_db_engine) as session:
        yield session


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/documents")
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # Create test access token
    test_user_id = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": test_user_id, "type": "access"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "patient_id": str(uuid.uuid4()),
        "filename": "test_lab_result.pdf",
        "document_type": "LAB_RESULT",
        "document_category": "Laboratory",
        "tags": ["urgent", "blood_test"],
        "metadata": {"test_type": "Complete Blood Count"}
    }


@pytest.fixture
def sample_pdf_file():
    """Sample PDF file content for testing."""
    # Minimal PDF content for testing
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000125 00000 n 
0000000185 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
285
%%EOF"""
    return pdf_content


class TestDocumentUploadIntegration:
    """Integration tests for document upload endpoint."""
    
    @pytest.mark.asyncio
    async def test_upload_document_success(self, test_client, auth_headers, sample_document_data, sample_pdf_file):
        """Test successful document upload with full integration."""
        # Prepare multipart form data
        files = {"file": ("test_document.pdf", sample_pdf_file, "application/pdf")}
        data = {
            "patient_id": sample_document_data["patient_id"],
            "document_type": sample_document_data["document_type"],
            "document_category": sample_document_data["document_category"],
            "tags": ",".join(sample_document_data["tags"]),
            "metadata": str(sample_document_data["metadata"]),
            "auto_classify": "true",
            "auto_generate_filename": "true"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert "document_id" in result
        assert result["filename"] == "test_document.pdf"
        assert result["document_type"] == "LAB_RESULT"
        assert result["file_size"] > 0
        assert "hash_sha256" in result
    
    @pytest.mark.asyncio
    async def test_upload_document_unauthorized(self, test_client, sample_pdf_file):
        """Test document upload without authentication."""
        files = {"file": ("test.pdf", sample_pdf_file, "application/pdf")}
        data = {"patient_id": str(uuid.uuid4())}
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data
        )
        
        # Assert
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_upload_document_invalid_file(self, test_client, auth_headers):
        """Test document upload with invalid file."""
        files = {"file": ("test.txt", b"", "text/plain")}
        data = {"patient_id": str(uuid.uuid4())}
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400
        assert "File is empty" in response.json()["detail"]


class TestDocumentCRUDIntegration:
    """Integration tests for document CRUD operations."""
    
    @pytest.fixture
    async def uploaded_document(self, test_client, auth_headers, sample_document_data, sample_pdf_file):
        """Upload a document for testing CRUD operations."""
        files = {"file": ("test_document.pdf", sample_pdf_file, "application/pdf")}
        data = {
            "patient_id": sample_document_data["patient_id"],
            "document_type": sample_document_data["document_type"],
            "document_category": sample_document_data["document_category"],
            "tags": ",".join(sample_document_data["tags"])
        }
        
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        return response.json()
    
    @pytest.mark.asyncio
    async def test_get_document_metadata_success(self, test_client, auth_headers, uploaded_document):
        """Test successful document metadata retrieval."""
        document_id = uploaded_document["document_id"]
        
        # Act
        response = test_client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["document_id"] == document_id
        assert result["filename"] == "test_document.pdf"
        assert result["document_type"] == "LAB_RESULT"
        assert "uploaded_at" in result
    
    @pytest.mark.asyncio
    async def test_get_document_metadata_not_found(self, test_client, auth_headers):
        """Test document metadata retrieval for non-existent document."""
        non_existent_id = str(uuid.uuid4())
        
        # Act
        response = test_client.get(
            f"/api/v1/documents/{non_existent_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_document_metadata_success(self, test_client, auth_headers, uploaded_document):
        """Test successful document metadata update."""
        document_id = uploaded_document["document_id"]
        
        update_data = {
            "filename": "updated_lab_result.pdf",
            "document_category": "Updated Laboratory",
            "tags": ["updated", "blood_test", "complete"]
        }
        
        # Act
        response = test_client.patch(
            f"/api/v1/documents/{document_id}?reason=Integration test update",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["filename"] == "updated_lab_result.pdf"
        assert result["document_category"] == "Updated Laboratory"
        assert "updated" in result["tags"]
        assert result["updated_at"] is not None
    
    @pytest.mark.asyncio
    async def test_delete_document_success(self, test_client, auth_headers, uploaded_document):
        """Test successful document deletion."""
        document_id = uploaded_document["document_id"]
        
        # Act
        response = test_client.delete(
            f"/api/v1/documents/{document_id}?deletion_reason=Integration test deletion",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["document_id"] == document_id
        assert result["deletion_type"] == "soft"
        assert result["reason"] == "Integration test deletion"
        assert "deleted_at" in result


class TestDocumentSearchIntegration:
    """Integration tests for document search functionality."""
    
    @pytest.fixture
    async def multiple_documents(self, test_client, auth_headers, sample_pdf_file):
        """Upload multiple documents for search testing."""
        documents = []
        patient_id = str(uuid.uuid4())
        
        test_documents = [
            {
                "filename": "lab_result_1.pdf",
                "document_type": "LAB_RESULT",
                "document_category": "Laboratory",
                "tags": "urgent,blood_test"
            },
            {
                "filename": "clinical_note_1.pdf", 
                "document_type": "CLINICAL_NOTE",
                "document_category": "Clinical",
                "tags": "routine,checkup"
            },
            {
                "filename": "imaging_scan.pdf",
                "document_type": "IMAGING",
                "document_category": "Radiology", 
                "tags": "mri,urgent"
            }
        ]
        
        for doc_data in test_documents:
            files = {"file": (doc_data["filename"], sample_pdf_file, "application/pdf")}
            data = {
                "patient_id": patient_id,
                "document_type": doc_data["document_type"],
                "document_category": doc_data["document_category"],
                "tags": doc_data["tags"]
            }
            
            response = test_client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            documents.append(response.json())
        
        return documents, patient_id
    
    @pytest.mark.asyncio
    async def test_search_documents_by_patient(self, test_client, auth_headers, multiple_documents):
        """Test document search by patient ID."""
        documents, patient_id = multiple_documents
        
        search_data = {
            "patient_id": patient_id,
            "limit": 50,
            "offset": 0
        }
        
        # Act
        response = test_client.post(
            "/api/v1/documents/search",
            json=search_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["total"] == 3
        assert len(result["documents"]) == 3
        
        # Verify all documents belong to the same patient
        for doc in result["documents"]:
            assert doc["patient_id"] == patient_id
    
    @pytest.mark.asyncio
    async def test_search_documents_by_type(self, test_client, auth_headers, multiple_documents):
        """Test document search by document type."""
        documents, patient_id = multiple_documents
        
        search_data = {
            "patient_id": patient_id,
            "document_types": ["LAB_RESULT"],
            "limit": 50,
            "offset": 0
        }
        
        # Act
        response = test_client.post(
            "/api/v1/documents/search",
            json=search_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["total"] == 1
        assert len(result["documents"]) == 1
        assert result["documents"][0]["document_type"] == "LAB_RESULT"
    
    @pytest.mark.asyncio
    async def test_search_documents_by_tags(self, test_client, auth_headers, multiple_documents):
        """Test document search by tags."""
        documents, patient_id = multiple_documents
        
        search_data = {
            "patient_id": patient_id,
            "tags": ["urgent"],
            "limit": 50,
            "offset": 0
        }
        
        # Act
        response = test_client.post(
            "/api/v1/documents/search",
            json=search_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["total"] == 2  # lab_result_1 and imaging_scan both have "urgent" tag
        assert len(result["documents"]) == 2
        
        for doc in result["documents"]:
            assert "urgent" in doc["tags"]


class TestDocumentStatsIntegration:
    """Integration tests for document statistics."""
    
    @pytest.mark.asyncio
    async def test_get_document_stats_global(self, test_client, auth_headers, multiple_documents):
        """Test global document statistics retrieval."""
        documents, patient_id = multiple_documents
        
        # Act
        response = test_client.get(
            "/api/v1/documents/stats",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert "total_documents" in result
        assert "documents_by_type" in result
        assert "storage_usage_bytes" in result
        assert "classification_accuracy" in result
        
        # Verify document type counts
        assert result["documents_by_type"]["LAB_RESULT"] >= 1
        assert result["documents_by_type"]["CLINICAL_NOTE"] >= 1
        assert result["documents_by_type"]["IMAGING"] >= 1
    
    @pytest.mark.asyncio
    async def test_get_document_stats_by_patient(self, test_client, auth_headers, multiple_documents):
        """Test document statistics filtered by patient."""
        documents, patient_id = multiple_documents
        
        # Act
        response = test_client.get(
            f"/api/v1/documents/stats?patient_id={patient_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["total_documents"] == 3
        assert len(result["recent_uploads"]) <= 3


class TestBulkOperationsIntegration:
    """Integration tests for bulk operations."""
    
    @pytest.mark.asyncio
    async def test_bulk_delete_documents_success(self, test_client, auth_headers, multiple_documents):
        """Test successful bulk document deletion."""
        documents, patient_id = multiple_documents
        
        # Get first two document IDs
        document_ids = [doc["document_id"] for doc in documents[:2]]
        
        bulk_delete_data = {
            "document_ids": document_ids,
            "reason": "Bulk integration test deletion",
            "hard_delete": False
        }
        
        # Act
        response = test_client.post(
            "/api/v1/documents/bulk/delete",
            json=bulk_delete_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["success_count"] == 2
        assert result["failed_count"] == 0
        assert result["total_count"] == 2
        assert len(result["failed_documents"]) == 0
    
    @pytest.mark.asyncio
    async def test_bulk_update_tags_success(self, test_client, auth_headers, multiple_documents):
        """Test successful bulk tag updates."""
        documents, patient_id = multiple_documents
        
        # Get all document IDs
        document_ids = [doc["document_id"] for doc in documents]
        
        bulk_tags_data = {
            "document_ids": document_ids,
            "tags": ["integration_test", "bulk_updated"],
            "action": "add"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/documents/bulk/update-tags",
            json=bulk_tags_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert result["success_count"] == 3
        assert result["failed_count"] == 0
        assert result["total_count"] == 3


class TestDocumentDownloadIntegration:
    """Integration tests for document download."""
    
    @pytest.mark.asyncio
    async def test_download_document_success(self, test_client, auth_headers, uploaded_document):
        """Test successful document download."""
        document_id = uploaded_document["document_id"]
        
        # Act
        response = test_client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0
    
    @pytest.mark.asyncio
    async def test_download_document_not_found(self, test_client, auth_headers):
        """Test document download for non-existent document."""
        non_existent_id = str(uuid.uuid4())
        
        # Act
        response = test_client.get(
            f"/api/v1/documents/{non_existent_id}/download",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404


class TestHealthCheckIntegration:
    """Integration tests for health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, test_client):
        """Test health check endpoint."""
        # Act
        response = test_client.get("/api/v1/documents/health")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert "status" in result
        assert result["status"] in ["healthy", "unhealthy"]


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_uuid_format(self, test_client, auth_headers):
        """Test error handling for invalid UUID format."""
        invalid_id = "not-a-uuid"
        
        # Act
        response = test_client.get(
            f"/api/v1/documents/{invalid_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400
        assert "Invalid document ID format" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client, auth_headers):
        """Test error handling for missing required fields."""
        # Act - Try to update without providing reason
        response = test_client.patch(
            f"/api/v1/documents/{str(uuid.uuid4())}",
            json={"filename": "new_name.pdf"},
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, test_client, auth_headers):
        """Test rate limiting behavior simulation."""
        # This would require actual rate limiting implementation
        # For now, just test that multiple requests work
        
        for i in range(5):
            response = test_client.get(
                "/api/v1/documents/health",
                headers=auth_headers
            )
            assert response.status_code == 200


if __name__ == "__main__":
    # Run tests with: python -m pytest app/modules/document_management/test_integration_api.py -v
    pytest.main([__file__, "-v"])