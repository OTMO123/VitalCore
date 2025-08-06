"""
Document Diff Engine

Advanced document comparison and diff generation for version control.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import difflib
import hashlib
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)

class DiffType(Enum):
    """Types of differences between documents."""
    CONTENT_CHANGE = "content_change"
    METADATA_CHANGE = "metadata_change"
    STRUCTURE_CHANGE = "structure_change"
    SIZE_CHANGE = "size_change"
    HASH_CHANGE = "hash_change"

@dataclass
class DocumentDiff:
    """Represents differences between two document versions."""
    
    from_version: str
    to_version: str
    diff_type: DiffType
    timestamp: datetime
    changes: List[Dict[str, Any]]
    summary: str
    details: Dict[str, Any]
    confidence: float = 1.0
    
    def __post_init__(self):
        if not self.changes:
            self.changes = []
        if not self.details:
            self.details = {}

class DiffEngine:
    """Advanced document comparison and diff generation engine."""
    
    def __init__(self):
        self.diff_algorithms = {
            "text": self._text_diff,
            "binary": self._binary_diff,
            "metadata": self._metadata_diff,
            "structure": self._structure_diff
        }
    
    def generate_diff(
        self,
        old_content: bytes,
        new_content: bytes,
        old_metadata: Dict[str, Any],
        new_metadata: Dict[str, Any],
        old_version: str,
        new_version: str,
        content_type: str = "application/octet-stream"
    ) -> DocumentDiff:
        """
        Generate comprehensive diff between two document versions.
        
        Args:
            old_content: Content of the old version
            new_content: Content of the new version
            old_metadata: Metadata of the old version
            new_metadata: Metadata of the new version
            old_version: Version identifier for old document
            new_version: Version identifier for new document
            content_type: MIME type of the document
            
        Returns:
            DocumentDiff object with detailed changes
        """
        
        logger.info(
            "Generating document diff",
            from_version=old_version,
            to_version=new_version,
            content_type=content_type,
            old_size=len(old_content),
            new_size=len(new_content)
        )
        
        changes = []
        diff_type = DiffType.CONTENT_CHANGE
        
        # Generate content hash comparison
        old_hash = hashlib.sha256(old_content).hexdigest()
        new_hash = hashlib.sha256(new_content).hexdigest()
        
        if old_hash != new_hash:
            # Content has changed
            if content_type.startswith("text/") or content_type == "application/pdf":
                # Use text diff for text-based content
                content_changes = self._text_diff(old_content, new_content)
                changes.extend(content_changes)
            else:
                # Use binary diff for other content
                binary_changes = self._binary_diff(old_content, new_content)
                changes.extend(binary_changes)
        
        # Generate metadata diff
        metadata_changes = self._metadata_diff(old_metadata, new_metadata)
        if metadata_changes:
            changes.extend(metadata_changes)
            if not changes or all(c.get("type") == "metadata" for c in changes):
                diff_type = DiffType.METADATA_CHANGE
        
        # Check for size changes
        old_size = len(old_content)
        new_size = len(new_content)
        if abs(new_size - old_size) > old_size * 0.1:  # More than 10% size change
            changes.append({
                "type": "size_change",
                "old_size": old_size,
                "new_size": new_size,
                "size_delta": new_size - old_size,
                "percentage_change": ((new_size - old_size) / old_size) * 100 if old_size > 0 else 100
            })
            diff_type = DiffType.SIZE_CHANGE
        
        # Generate summary
        summary = self._generate_diff_summary(changes, old_version, new_version)
        
        # Calculate confidence based on diff quality
        confidence = self._calculate_diff_confidence(changes, content_type)
        
        diff = DocumentDiff(
            from_version=old_version,
            to_version=new_version,
            diff_type=diff_type,
            timestamp=datetime.now(),
            changes=changes,
            summary=summary,
            details={
                "content_type": content_type,
                "old_hash": old_hash,
                "new_hash": new_hash,
                "total_changes": len(changes),
                "algorithms_used": list(self.diff_algorithms.keys())
            },
            confidence=confidence
        )
        
        logger.info(
            "Document diff generated",
            from_version=old_version,
            to_version=new_version,
            diff_type=diff_type.value,
            total_changes=len(changes),
            confidence=confidence
        )
        
        return diff
    
    def _text_diff(self, old_content: bytes, new_content: bytes) -> List[Dict[str, Any]]:
        """Generate text-based diff using unified diff algorithm."""
        
        try:
            # Decode content to text
            old_text = old_content.decode('utf-8', errors='ignore')
            new_text = new_content.decode('utf-8', errors='ignore')
            
            # Split into lines for diff
            old_lines = old_text.splitlines(keepends=True)
            new_lines = new_text.splitlines(keepends=True)
            
            # Generate unified diff
            diff_lines = list(difflib.unified_diff(
                old_lines, 
                new_lines, 
                fromfile='old_version', 
                tofile='new_version',
                n=3  # 3 lines of context
            ))
            
            if not diff_lines:
                return []
            
            changes = []
            
            # Parse diff output
            added_lines = 0
            removed_lines = 0
            
            for line in diff_lines:
                if line.startswith('+') and not line.startswith('+++'):
                    added_lines += 1
                elif line.startswith('-') and not line.startswith('---'):
                    removed_lines += 1
            
            changes.append({
                "type": "text_diff",
                "added_lines": added_lines,
                "removed_lines": removed_lines,
                "total_diff_lines": len(diff_lines),
                "diff_output": diff_lines[:100],  # Limit output size
                "similarity_ratio": difflib.SequenceMatcher(None, old_text, new_text).ratio()
            })
            
            # Detect significant changes
            if added_lines > 10 or removed_lines > 10:
                changes.append({
                    "type": "major_text_change",
                    "description": f"Major text changes detected: +{added_lines} -{removed_lines} lines",
                    "change_magnitude": "high" if (added_lines + removed_lines) > 50 else "medium"
                })
            
            return changes
            
        except Exception as e:
            logger.warning("Text diff generation failed", error=str(e))
            return self._binary_diff(old_content, new_content)
    
    def _binary_diff(self, old_content: bytes, new_content: bytes) -> List[Dict[str, Any]]:
        """Generate binary diff for non-text content."""
        
        changes = []
        
        # Basic binary comparison
        if old_content != new_content:
            # Calculate byte-level differences
            different_bytes = sum(1 for a, b in zip(old_content, new_content) if a != b)
            
            # Handle different lengths
            if len(old_content) != len(new_content):
                size_diff = abs(len(new_content) - len(old_content))
                different_bytes += size_diff
            
            total_bytes = max(len(old_content), len(new_content))
            similarity = 1.0 - (different_bytes / total_bytes) if total_bytes > 0 else 0.0
            
            changes.append({
                "type": "binary_diff",
                "different_bytes": different_bytes,
                "total_bytes": total_bytes,
                "similarity": similarity,
                "old_size": len(old_content),
                "new_size": len(new_content),
                "change_type": "binary_modification"
            })
            
            # Detect complete replacement
            if similarity < 0.5:
                changes.append({
                    "type": "binary_replacement",
                    "description": "Content appears to be completely replaced",
                    "similarity": similarity
                })
        
        return changes
    
    def _metadata_diff(self, old_metadata: Dict[str, Any], new_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate metadata diff."""
        
        changes = []
        
        # Find added, removed, and modified metadata
        old_keys = set(old_metadata.keys())
        new_keys = set(new_metadata.keys())
        
        # Added metadata
        added_keys = new_keys - old_keys
        if added_keys:
            changes.append({
                "type": "metadata_added",
                "added_fields": list(added_keys),
                "values": {key: new_metadata[key] for key in added_keys}
            })
        
        # Removed metadata
        removed_keys = old_keys - new_keys
        if removed_keys:
            changes.append({
                "type": "metadata_removed",
                "removed_fields": list(removed_keys),
                "old_values": {key: old_metadata[key] for key in removed_keys}
            })
        
        # Modified metadata
        common_keys = old_keys & new_keys
        modified_fields = {}
        
        for key in common_keys:
            old_value = old_metadata[key]
            new_value = new_metadata[key]
            
            if old_value != new_value:
                modified_fields[key] = {
                    "old_value": old_value,
                    "new_value": new_value
                }
        
        if modified_fields:
            changes.append({
                "type": "metadata_modified",
                "modified_fields": list(modified_fields.keys()),
                "changes": modified_fields
            })
        
        return changes
    
    def _structure_diff(self, old_data: Any, new_data: Any) -> List[Dict[str, Any]]:
        """Generate structural diff for complex data structures."""
        
        changes = []
        
        # This is a placeholder for more advanced structural analysis
        # Could be extended to analyze document structure like:
        # - PDF page structure
        # - Document sections
        # - Table structures
        # - Image locations
        
        if type(old_data) != type(new_data):
            changes.append({
                "type": "structure_type_change",
                "old_type": str(type(old_data)),
                "new_type": str(type(new_data))
            })
        
        return changes
    
    def _generate_diff_summary(self, changes: List[Dict[str, Any]], old_version: str, new_version: str) -> str:
        """Generate human-readable summary of changes."""
        
        if not changes:
            return f"No changes detected between {old_version} and {new_version}"
        
        summary_parts = []
        
        # Count change types
        change_types = {}
        for change in changes:
            change_type = change.get("type", "unknown")
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        # Generate summary based on changes
        if "text_diff" in change_types:
            text_change = next(c for c in changes if c.get("type") == "text_diff")
            added = text_change.get("added_lines", 0)
            removed = text_change.get("removed_lines", 0)
            summary_parts.append(f"Text: +{added} -{removed} lines")
        
        if "binary_diff" in change_types:
            binary_change = next(c for c in changes if c.get("type") == "binary_diff")
            similarity = binary_change.get("similarity", 0)
            summary_parts.append(f"Binary: {similarity:.1%} similarity")
        
        if "metadata_added" in change_types:
            meta_change = next(c for c in changes if c.get("type") == "metadata_added")
            count = len(meta_change.get("added_fields", []))
            summary_parts.append(f"Metadata: +{count} fields")
        
        if "metadata_removed" in change_types:
            meta_change = next(c for c in changes if c.get("type") == "metadata_removed")
            count = len(meta_change.get("removed_fields", []))
            summary_parts.append(f"Metadata: -{count} fields")
        
        if "metadata_modified" in change_types:
            meta_change = next(c for c in changes if c.get("type") == "metadata_modified")
            count = len(meta_change.get("modified_fields", []))
            summary_parts.append(f"Metadata: ~{count} fields")
        
        if "size_change" in change_types:
            size_change = next(c for c in changes if c.get("type") == "size_change")
            delta = size_change.get("size_delta", 0)
            percentage = size_change.get("percentage_change", 0)
            summary_parts.append(f"Size: {delta:+} bytes ({percentage:+.1f}%)")
        
        if summary_parts:
            return f"Changes from {old_version} to {new_version}: " + ", ".join(summary_parts)
        else:
            return f"Document modified between {old_version} and {new_version}"
    
    def _calculate_diff_confidence(self, changes: List[Dict[str, Any]], content_type: str) -> float:
        """Calculate confidence score for the diff analysis."""
        
        confidence = 0.8  # Base confidence
        
        # Adjust based on content type
        if content_type.startswith("text/"):
            confidence += 0.1  # Higher confidence for text
        elif content_type == "application/pdf":
            confidence += 0.05  # Medium confidence for PDF
        
        # Adjust based on change complexity
        if len(changes) == 0:
            confidence = 1.0  # Perfect confidence for no changes
        elif len(changes) > 10:
            confidence -= 0.1  # Lower confidence for many changes
        
        # Check for text similarity if available
        for change in changes:
            if change.get("type") == "text_diff":
                similarity = change.get("similarity_ratio", 0.5)
                confidence += (similarity - 0.5) * 0.2  # Adjust based on similarity
                break
        
        return max(0.1, min(1.0, confidence))
    
    def compare_versions(
        self,
        version1_data: Tuple[bytes, Dict[str, Any], str],
        version2_data: Tuple[bytes, Dict[str, Any], str],
        version1_id: str,
        version2_id: str
    ) -> DocumentDiff:
        """
        Compare two document versions.
        
        Args:
            version1_data: Tuple of (content, metadata, content_type) for version 1
            version2_data: Tuple of (content, metadata, content_type) for version 2
            version1_id: Version identifier for first document
            version2_id: Version identifier for second document
            
        Returns:
            DocumentDiff object
        """
        
        content1, metadata1, content_type1 = version1_data
        content2, metadata2, content_type2 = version2_data
        
        # Use the more specific content type
        content_type = content_type2 if content_type2 != "application/octet-stream" else content_type1
        
        return self.generate_diff(
            old_content=content1,
            new_content=content2,
            old_metadata=metadata1,
            new_metadata=metadata2,
            old_version=version1_id,
            new_version=version2_id,
            content_type=content_type
        )