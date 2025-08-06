"""
Document Version Control Service

Manages document versions, tracks changes, and provides rollback capabilities
following Git-like versioning principles adapted for medical documents.
"""

import asyncio
import hashlib
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class VersionType(Enum):
    """Types of document versions."""
    INITIAL = "initial"
    REVISION = "revision"
    CORRECTION = "correction"
    AMENDMENT = "amendment"
    SUPERSEDED = "superseded"


class ChangeType(Enum):
    """Types of changes between versions."""
    CONTENT_UPDATE = "content_update"
    METADATA_UPDATE = "metadata_update"
    CLASSIFICATION_UPDATE = "classification_update"
    FILENAME_UPDATE = "filename_update"
    SECURITY_UPDATE = "security_update"


@dataclass
class DocumentVersion:
    """Represents a specific version of a document."""
    
    version_id: str
    document_id: str
    version_number: str
    version_type: VersionType
    parent_version_id: Optional[str]
    content_hash: str
    metadata_hash: str
    file_size: int
    storage_path: str
    created_at: datetime
    created_by: str
    change_summary: str
    change_type: ChangeType
    tags: List[str]
    is_current: bool
    metadata: Dict[str, Any]


@dataclass
class VersionComparison:
    """Comparison between two document versions."""
    
    from_version: DocumentVersion
    to_version: DocumentVersion
    content_changed: bool
    metadata_changed: bool
    changes_summary: List[str]
    similarity_score: float
    comparison_metadata: Dict[str, Any]


class VersionNumberGenerator:
    """Generates semantic version numbers for documents."""
    
    def __init__(self):
        self.logger = logger.bind(component="VersionNumberGenerator")
    
    def generate_initial_version(self) -> str:
        """Generate initial version number."""
        return "1.0.0"
    
    def generate_next_version(
        self, 
        current_version: str, 
        change_type: ChangeType
    ) -> str:
        """Generate next version number based on change type."""
        
        try:
            # Parse current version (semantic versioning: MAJOR.MINOR.PATCH)
            parts = current_version.split('.')
            if len(parts) != 3:
                self.logger.warning("Invalid version format", version=current_version)
                return "1.0.0"
            
            major, minor, patch = map(int, parts)
            
            # Increment based on change type
            if change_type == ChangeType.CONTENT_UPDATE:
                # Major content changes increment major version
                major += 1
                minor = 0
                patch = 0
            elif change_type in [ChangeType.METADATA_UPDATE, ChangeType.CLASSIFICATION_UPDATE]:
                # Minor changes increment minor version
                minor += 1
                patch = 0
            else:
                # Small changes increment patch version
                patch += 1
            
            return f"{major}.{minor}.{patch}"
            
        except Exception as e:
            self.logger.error("Version generation failed", error=str(e))
            return "1.0.0"
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version numbers. Returns -1, 0, or 1."""
        
        try:
            v1_parts = list(map(int, version1.split('.')))
            v2_parts = list(map(int, version2.split('.')))
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 < v2:
                    return -1
                elif v1 > v2:
                    return 1
            
            return 0
            
        except Exception:
            return 0


class ContentHashCalculator:
    """Calculates content hashes for version tracking."""
    
    def __init__(self):
        self.logger = logger.bind(component="ContentHashCalculator")
    
    def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of document content."""
        return hashlib.sha256(content).hexdigest()
    
    def calculate_metadata_hash(self, metadata: Dict[str, Any]) -> str:
        """Calculate hash of document metadata."""
        
        # Sort metadata for consistent hashing
        sorted_metadata = self._sort_metadata(metadata)
        metadata_str = str(sorted_metadata)
        
        return hashlib.sha256(metadata_str.encode()).hexdigest()
    
    def _sort_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sort metadata recursively for consistent hashing."""
        
        if isinstance(metadata, dict):
            return {k: self._sort_metadata(v) for k, v in sorted(metadata.items())}
        elif isinstance(metadata, list):
            return [self._sort_metadata(item) for item in metadata]
        else:
            return metadata


class VersionControlService:
    """
    Main version control service for document management.
    
    Provides Git-like versioning for medical documents with audit trails.
    """
    
    def __init__(self):
        self.version_generator = VersionNumberGenerator()
        self.hash_calculator = ContentHashCalculator()
        self.logger = logger.bind(service="VersionControlService")
    
    async def create_initial_version(
        self,
        document_id: str,
        content: bytes,
        metadata: Dict[str, Any],
        storage_path: str,
        created_by: str,
        change_summary: str = "Initial document creation"
    ) -> DocumentVersion:
        """Create the initial version of a document."""
        
        try:
            version_id = str(uuid.uuid4())
            content_hash = self.hash_calculator.calculate_content_hash(content)
            metadata_hash = self.hash_calculator.calculate_metadata_hash(metadata)
            
            version = DocumentVersion(
                version_id=version_id,
                document_id=document_id,
                version_number=self.version_generator.generate_initial_version(),
                version_type=VersionType.INITIAL,
                parent_version_id=None,
                content_hash=content_hash,
                metadata_hash=metadata_hash,
                file_size=len(content),
                storage_path=storage_path,
                created_at=datetime.utcnow(),
                created_by=created_by,
                change_summary=change_summary,
                change_type=ChangeType.CONTENT_UPDATE,
                tags=["initial"],
                is_current=True,
                metadata=metadata.copy()
            )
            
            self.logger.info(
                "Initial version created",
                document_id=document_id,
                version_id=version_id,
                version_number=version.version_number,
                content_hash=content_hash[:16]
            )
            
            return version
            
        except Exception as e:
            self.logger.error("Failed to create initial version", error=str(e))
            raise
    
    async def create_new_version(
        self,
        document_id: str,
        current_version: DocumentVersion,
        new_content: Optional[bytes] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
        storage_path: Optional[str] = None,
        created_by: str = "",
        change_summary: str = "",
        change_type: ChangeType = ChangeType.CONTENT_UPDATE,
        version_type: VersionType = VersionType.REVISION
    ) -> DocumentVersion:
        """Create a new version of an existing document."""
        
        try:
            # Determine what changed
            content_changed = new_content is not None
            metadata_changed = new_metadata is not None
            
            # Calculate hashes
            if content_changed:
                content_hash = self.hash_calculator.calculate_content_hash(new_content)
                file_size = len(new_content)
            else:
                content_hash = current_version.content_hash
                file_size = current_version.file_size
            
            if metadata_changed:
                metadata_hash = self.hash_calculator.calculate_metadata_hash(new_metadata)
                final_metadata = new_metadata.copy()
            else:
                metadata_hash = current_version.metadata_hash
                final_metadata = current_version.metadata.copy()
            
            # Determine change type if not specified
            if change_type == ChangeType.CONTENT_UPDATE and not content_changed:
                if metadata_changed:
                    change_type = ChangeType.METADATA_UPDATE
            
            # Generate new version number
            new_version_number = self.version_generator.generate_next_version(
                current_version.version_number, change_type
            )
            
            # Create new version
            version_id = str(uuid.uuid4())
            new_version = DocumentVersion(
                version_id=version_id,
                document_id=document_id,
                version_number=new_version_number,
                version_type=version_type,
                parent_version_id=current_version.version_id,
                content_hash=content_hash,
                metadata_hash=metadata_hash,
                file_size=file_size,
                storage_path=storage_path or current_version.storage_path,
                created_at=datetime.utcnow(),
                created_by=created_by,
                change_summary=change_summary or "Document updated",
                change_type=change_type,
                tags=self._generate_version_tags(change_type, version_type),
                is_current=True,
                metadata=final_metadata
            )
            
            self.logger.info(
                "New version created",
                document_id=document_id,
                version_id=version_id,
                version_number=new_version_number,
                parent_version=current_version.version_number,
                change_type=change_type.value
            )
            
            return new_version
            
        except Exception as e:
            self.logger.error("Failed to create new version", error=str(e))
            raise
    
    def _generate_version_tags(
        self, 
        change_type: ChangeType, 
        version_type: VersionType
    ) -> List[str]:
        """Generate tags for version based on change and version type."""
        
        tags = [version_type.value, change_type.value]
        
        # Add specific tags based on change type
        if change_type == ChangeType.CONTENT_UPDATE:
            tags.append("content_modified")
        elif change_type == ChangeType.METADATA_UPDATE:
            tags.append("metadata_modified")
        elif change_type == ChangeType.CLASSIFICATION_UPDATE:
            tags.append("classification_modified")
        
        return tags
    
    async def compare_versions(
        self,
        version1: DocumentVersion,
        version2: DocumentVersion
    ) -> VersionComparison:
        """Compare two versions of a document."""
        
        try:
            # Check what changed
            content_changed = version1.content_hash != version2.content_hash
            metadata_changed = version1.metadata_hash != version2.metadata_hash
            
            # Generate changes summary
            changes_summary = []
            
            if content_changed:
                changes_summary.append("Document content modified")
            
            if metadata_changed:
                changes_summary.append("Document metadata modified")
            
            # Calculate similarity score (simplified)
            similarity_factors = []
            
            # Content similarity (based on file size change)
            if content_changed:
                size_ratio = min(version1.file_size, version2.file_size) / max(version1.file_size, version2.file_size)
                similarity_factors.append(size_ratio)
            else:
                similarity_factors.append(1.0)
            
            # Metadata similarity (simplified)
            if metadata_changed:
                common_keys = set(version1.metadata.keys()) & set(version2.metadata.keys())
                total_keys = set(version1.metadata.keys()) | set(version2.metadata.keys())
                metadata_similarity = len(common_keys) / len(total_keys) if total_keys else 1.0
                similarity_factors.append(metadata_similarity)
            else:
                similarity_factors.append(1.0)
            
            # Overall similarity score
            similarity_score = sum(similarity_factors) / len(similarity_factors)
            
            comparison = VersionComparison(
                from_version=version1,
                to_version=version2,
                content_changed=content_changed,
                metadata_changed=metadata_changed,
                changes_summary=changes_summary,
                similarity_score=similarity_score,
                comparison_metadata={
                    "version_number_comparison": self.version_generator.compare_versions(
                        version1.version_number, version2.version_number
                    ),
                    "time_difference_seconds": (version2.created_at - version1.created_at).total_seconds(),
                    "file_size_change": version2.file_size - version1.file_size
                }
            )
            
            self.logger.info(
                "Version comparison completed",
                from_version=version1.version_number,
                to_version=version2.version_number,
                similarity_score=similarity_score,
                content_changed=content_changed,
                metadata_changed=metadata_changed
            )
            
            return comparison
            
        except Exception as e:
            self.logger.error("Version comparison failed", error=str(e))
            raise
    
    async def get_version_history(
        self,
        document_id: str,
        limit: Optional[int] = None
    ) -> List[DocumentVersion]:
        """Get version history for a document."""
        
        # This would normally query the database
        # For now, return empty list as placeholder
        return []
    
    async def rollback_to_version(
        self,
        document_id: str,
        target_version: DocumentVersion,
        created_by: str,
        rollback_reason: str = ""
    ) -> DocumentVersion:
        """Rollback document to a previous version."""
        
        try:
            # Create a new version that restores the target version's content
            rollback_version = await self.create_new_version(
                document_id=document_id,
                current_version=target_version,  # This would be the current version in real implementation
                new_content=None,  # Would restore content from target version
                new_metadata=target_version.metadata,
                created_by=created_by,
                change_summary=f"Rollback to version {target_version.version_number}. Reason: {rollback_reason}",
                change_type=ChangeType.CONTENT_UPDATE,
                version_type=VersionType.REVISION
            )
            
            # Add rollback-specific tags
            rollback_version.tags.extend(["rollback", f"restored_from_{target_version.version_number}"])
            
            self.logger.info(
                "Document rolled back",
                document_id=document_id,
                target_version=target_version.version_number,
                new_version=rollback_version.version_number,
                reason=rollback_reason
            )
            
            return rollback_version
            
        except Exception as e:
            self.logger.error("Rollback failed", error=str(e))
            raise
    
    def validate_version_integrity(self, version: DocumentVersion) -> bool:
        """Validate the integrity of a document version."""
        
        try:
            # Check required fields
            required_fields = [
                'version_id', 'document_id', 'version_number',
                'content_hash', 'metadata_hash', 'created_at', 'created_by'
            ]
            
            for field in required_fields:
                if not getattr(version, field, None):
                    self.logger.warning("Missing required field", field=field)
                    return False
            
            # Validate version number format
            if not re.match(r'^\d+\.\d+\.\d+$', version.version_number):
                self.logger.warning("Invalid version number format", version=version.version_number)
                return False
            
            # Validate hashes
            if len(version.content_hash) != 64:  # SHA-256 hex length
                self.logger.warning("Invalid content hash length")
                return False
            
            if len(version.metadata_hash) != 64:  # SHA-256 hex length
                self.logger.warning("Invalid metadata hash length")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("Version validation failed", error=str(e))
            return False
    
    async def get_version_statistics(self, document_id: str) -> Dict[str, Any]:
        """Get statistics about document versions."""
        
        # This would calculate real statistics from database
        return {
            "total_versions": 0,
            "content_changes": 0,
            "metadata_changes": 0,
            "total_size_changes": 0,
            "first_version_date": None,
            "last_version_date": None,
            "most_active_contributor": None,
            "version_frequency": 0.0
        }
    
    async def cleanup_old_versions(
        self,
        document_id: str,
        retention_policy: Dict[str, Any]
    ) -> Dict[str, int]:
        """Cleanup old versions based on retention policy."""
        
        try:
            # Example retention policy:
            # {
            #     "keep_major_versions": True,
            #     "keep_last_n_versions": 10,
            #     "keep_versions_newer_than_days": 90,
            #     "keep_tagged_versions": ["important", "milestone"]
            # }
            
            self.logger.info(
                "Version cleanup initiated",
                document_id=document_id,
                retention_policy=retention_policy
            )
            
            # This would implement actual cleanup logic
            return {
                "versions_examined": 0,
                "versions_deleted": 0,
                "versions_kept": 0,
                "space_freed_bytes": 0
            }
            
        except Exception as e:
            self.logger.error("Version cleanup failed", error=str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for version control service."""
        
        try:
            # Test version number generation
            test_version = self.version_generator.generate_initial_version()
            next_version = self.version_generator.generate_next_version(
                test_version, ChangeType.CONTENT_UPDATE
            )
            
            # Test hash calculation
            test_content = b"Test content for health check"
            content_hash = self.hash_calculator.calculate_content_hash(test_content)
            
            # Test metadata hashing
            test_metadata = {"test": "metadata", "number": 123}
            metadata_hash = self.hash_calculator.calculate_metadata_hash(test_metadata)
            
            return {
                "status": "healthy",
                "version_generator": "working",
                "hash_calculator": "working",
                "test_version": test_version,
                "test_next_version": next_version,
                "test_content_hash": content_hash[:16],
                "test_metadata_hash": metadata_hash[:16]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Factory function
def get_version_control_service() -> VersionControlService:
    """Factory function to create version control service."""
    return VersionControlService()


# Import for regex
import re