#!/usr/bin/env python3
"""
Real-Time Audit Log Integrity Verification System
Implements cryptographic hash chains and tamper detection for SOC2/HIPAA compliance.

Security Principles Applied:
- Immutability: Audit logs cannot be modified without detection
- Non-repudiation: Cryptographic proof of log authenticity
- Integrity: Hash chains prevent insertion/deletion attacks
- Transparency: Real-time verification status
- Continuous Monitoring: Automated integrity checking

Cryptographic Techniques:
- Merkle Tree: Efficient integrity verification of log batches
- Hash Chains: Sequential linking of audit entries
- Digital Signatures: Non-repudiation of log entries
- Blockchain-inspired: Immutable log architecture
- Timestamping: Trusted time verification

Architecture Patterns:
- Observer Pattern: Real-time integrity monitoring
- Chain of Responsibility: Multi-layer verification
- Command Pattern: Audit actions as verifiable commands
- Factory Pattern: Verification strategy selection
"""

import asyncio
import json
import time
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from enum import Enum, auto
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
import structlog
import uuid
import base64
from concurrent.futures import ThreadPoolExecutor
import threading

# Cryptographic imports
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = structlog.get_logger()

class IntegrityStatus(Enum):
    """Audit log integrity verification status"""
    VERIFIED = auto()
    COMPROMISED = auto()
    MISSING = auto()
    PENDING_VERIFICATION = auto()
    VERIFICATION_FAILED = auto()
    CHAIN_BROKEN = auto()

class VerificationLevel(Enum):
    """Levels of integrity verification"""
    BASIC_HASH = "basic_hash"           # Simple hash verification
    HASH_CHAIN = "hash_chain"           # Sequential hash chain
    MERKLE_TREE = "merkle_tree"         # Batch verification
    DIGITAL_SIGNATURE = "digital_sig"   # Non-repudiation
    BLOCKCHAIN_STYLE = "blockchain"     # Full immutable chain

class TamperType(Enum):
    """Types of detected tampering"""
    MODIFICATION = "modification"       # Content changed
    INSERTION = "insertion"            # Entry inserted
    DELETION = "deletion"              # Entry removed
    REORDERING = "reordering"          # Order changed
    TIMESTAMP_MANIPULATION = "timestamp_manipulation"
    SIGNATURE_INVALID = "signature_invalid"

@dataclass(frozen=True)
class AuditLogEntry:
    """Immutable audit log entry with integrity metadata"""
    entry_id: str
    timestamp: datetime
    event_type: str
    user_id: str
    resource: str
    action: str
    outcome: str
    details: Dict[str, Any]
    
    # Integrity metadata
    sequence_number: int
    previous_hash: Optional[str]
    content_hash: str
    merkle_leaf_hash: str
    digital_signature: Optional[str]
    
    # Verification metadata
    verified: bool = False
    verification_timestamp: Optional[datetime] = None
    verification_level: Optional[VerificationLevel] = None

@dataclass
class IntegrityVerificationResult:
    """Result of integrity verification"""
    verification_id: str
    entry_id: str
    status: IntegrityStatus
    verification_level: VerificationLevel
    timestamp: datetime
    
    # Verification details
    hash_verified: bool
    chain_verified: bool
    signature_verified: bool
    merkle_verified: bool
    
    # Tamper detection
    tampering_detected: bool
    tamper_types: List[TamperType]
    tamper_evidence: Dict[str, Any]
    
    # Performance metrics
    verification_time_ms: float
    computational_cost: str

@dataclass
class IntegrityAlert:
    """Alert for integrity violations"""
    alert_id: str
    entry_id: str
    tamper_types: List[TamperType]
    detection_timestamp: datetime
    severity: str  # critical, high, medium, low
    evidence: Dict[str, Any]
    investigation_required: bool
    alert_escalated: bool = False

class MerkleTree:
    """Merkle tree implementation for batch audit log verification"""
    
    def __init__(self):
        self.leaves: List[bytes] = []
        self.tree: List[List[bytes]] = []
        self.root_hash: Optional[bytes] = None
    
    def add_leaf(self, data: bytes):
        """Add leaf to Merkle tree"""
        leaf_hash = hashlib.sha256(data).digest()
        self.leaves.append(leaf_hash)
        self._rebuild_tree()
    
    def _rebuild_tree(self):
        """Rebuild Merkle tree from leaves"""
        if not self.leaves:
            self.root_hash = None
            return
        
        current_level = self.leaves.copy()
        self.tree = [current_level.copy()]
        
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs of hashes
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                
                # Combine and hash
                combined = left + right
                parent_hash = hashlib.sha256(combined).digest()
                next_level.append(parent_hash)
            
            self.tree.append(next_level.copy())
            current_level = next_level
        
        self.root_hash = current_level[0] if current_level else None
    
    def get_proof(self, leaf_index: int) -> List[Tuple[bytes, str]]:
        """Get Merkle proof for leaf at index"""
        if leaf_index >= len(self.leaves):
            raise IndexError("Leaf index out of range")
        
        proof = []
        current_index = leaf_index
        
        for level in range(len(self.tree) - 1):
            current_level = self.tree[level]
            
            # Determine sibling
            if current_index % 2 == 0:
                # Left node, sibling is right
                sibling_index = current_index + 1
                side = "right"
            else:
                # Right node, sibling is left
                sibling_index = current_index - 1
                side = "left"
            
            if sibling_index < len(current_level):
                sibling_hash = current_level[sibling_index]
                proof.append((sibling_hash, side))
            
            current_index = current_index // 2
        
        return proof
    
    def verify_proof(self, leaf_data: bytes, proof: List[Tuple[bytes, str]]) -> bool:
        """Verify Merkle proof"""
        current_hash = hashlib.sha256(leaf_data).digest()
        
        for sibling_hash, side in proof:
            if side == "left":
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash
            
            current_hash = hashlib.sha256(combined).digest()
        
        return current_hash == self.root_hash

class DigitalSignatureVerifier:
    """Digital signature verification for audit logs"""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._generate_keypair()
    
    def _generate_keypair(self):
        """Generate RSA keypair for signing"""
        if not CRYPTO_AVAILABLE:
            logger.warning("Cryptography library not available, digital signatures disabled")
            return
        
        try:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
        except Exception as e:
            logger.error("Failed to generate keypair", error=str(e))
    
    def sign_entry(self, entry_data: bytes) -> Optional[str]:
        """Sign audit log entry"""
        if not self.private_key or not CRYPTO_AVAILABLE:
            return None
        
        try:
            signature = self.private_key.sign(
                entry_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            logger.error("Failed to sign entry", error=str(e))
            return None
    
    def verify_signature(self, entry_data: bytes, signature_b64: str) -> bool:
        """Verify digital signature"""
        if not self.public_key or not CRYPTO_AVAILABLE:
            return False
        
        try:
            signature = base64.b64decode(signature_b64)
            self.public_key.verify(
                signature,
                entry_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logger.error("Signature verification error", error=str(e))
            return False

class AuditIntegrityVerifier:
    """Real-time audit log integrity verification system"""
    
    def __init__(self, verification_level: VerificationLevel = VerificationLevel.HASH_CHAIN):
        self.verification_level = verification_level
        self.signature_verifier = DigitalSignatureVerifier()
        
        # Audit log storage
        self.audit_entries: Dict[str, AuditLogEntry] = {}
        self.entry_sequence: List[str] = []  # Ordered list of entry IDs
        
        # Integrity tracking
        self.verification_results: Dict[str, IntegrityVerificationResult] = {}
        self.integrity_alerts: List[IntegrityAlert] = []
        
        # Hash chain state
        self.last_hash: Optional[str] = None
        self.sequence_counter: int = 0
        
        # Merkle tree for batch verification
        self.merkle_tree = MerkleTree()
        self.merkle_batch_size = 100
        
        # Real-time monitoring
        self.monitoring_active = True
        self.verification_thread: Optional[threading.Thread] = None
        self.verification_interval_seconds = 30
        
        # Performance tracking
        self.verification_stats = {
            "total_verifications": 0,
            "failed_verifications": 0,
            "average_verification_time_ms": 0.0,
            "alerts_generated": 0
        }
        
        # Start background verification
        self._start_background_verification()
    
    async def add_audit_entry(self, event_type: str, user_id: str, resource: str, 
                             action: str, outcome: str, details: Dict[str, Any]) -> str:
        """Add new audit entry with integrity protection"""
        
        entry_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Calculate content hash
        entry_content = {
            "entry_id": entry_id,
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "outcome": outcome,
            "details": details
        }
        
        content_json = json.dumps(entry_content, sort_keys=True)
        content_hash = hashlib.sha256(content_json.encode()).hexdigest()
        
        # Calculate previous hash for chain
        if self.verification_level in [VerificationLevel.HASH_CHAIN, VerificationLevel.BLOCKCHAIN_STYLE]:
            previous_hash = self.last_hash
            
            # Create hash chain
            if previous_hash:
                chain_input = f"{previous_hash}{content_hash}"
            else:
                chain_input = content_hash
            
            current_hash = hashlib.sha256(chain_input.encode()).hexdigest()
            self.last_hash = current_hash
        else:
            previous_hash = None
        
        # Calculate Merkle leaf hash
        merkle_leaf_data = f"{entry_id}{content_hash}".encode()
        merkle_leaf_hash = hashlib.sha256(merkle_leaf_data).hexdigest()
        
        # Digital signature
        digital_signature = None
        if self.verification_level in [VerificationLevel.DIGITAL_SIGNATURE, VerificationLevel.BLOCKCHAIN_STYLE]:
            signature_data = content_json.encode()
            digital_signature = self.signature_verifier.sign_entry(signature_data)
        
        # Create audit entry
        audit_entry = AuditLogEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details,
            sequence_number=self.sequence_counter,
            previous_hash=previous_hash,
            content_hash=content_hash,
            merkle_leaf_hash=merkle_leaf_hash,
            digital_signature=digital_signature
        )
        
        # Store entry
        self.audit_entries[entry_id] = audit_entry
        self.entry_sequence.append(entry_id)
        self.sequence_counter += 1
        
        # Add to Merkle tree
        self.merkle_tree.add_leaf(merkle_leaf_data)
        
        # Immediate verification for critical events
        if outcome == "failure" or "error" in event_type.lower():
            await self._verify_entry_immediate(entry_id)
        
        logger.info("AUDIT_INTEGRITY - Entry added",
                   entry_id=entry_id,
                   event_type=event_type,
                   sequence_number=self.sequence_counter - 1,
                   verification_level=self.verification_level.value)
        
        return entry_id
    
    async def verify_entry_integrity(self, entry_id: str) -> IntegrityVerificationResult:
        """Comprehensive integrity verification for audit entry"""
        
        verification_id = str(uuid.uuid4())
        start_time = time.time()
        
        if entry_id not in self.audit_entries:
            return IntegrityVerificationResult(
                verification_id=verification_id,
                entry_id=entry_id,
                status=IntegrityStatus.MISSING,
                verification_level=self.verification_level,
                timestamp=datetime.utcnow(),
                hash_verified=False,
                chain_verified=False,
                signature_verified=False,
                merkle_verified=False,
                tampering_detected=True,
                tamper_types=[TamperType.DELETION],
                tamper_evidence={"error": "Entry not found"},
                verification_time_ms=0.0,
                computational_cost="none"
            )
        
        entry = self.audit_entries[entry_id]
        tamper_types = []
        tamper_evidence = {}
        
        # 1. Hash verification
        hash_verified = await self._verify_content_hash(entry)
        if not hash_verified:
            tamper_types.append(TamperType.MODIFICATION)
            tamper_evidence["content_hash"] = "Content hash mismatch"
        
        # 2. Hash chain verification
        chain_verified = True
        if self.verification_level in [VerificationLevel.HASH_CHAIN, VerificationLevel.BLOCKCHAIN_STYLE]:
            chain_verified = await self._verify_hash_chain(entry)
            if not chain_verified:
                tamper_types.append(TamperType.CHAIN_BROKEN)
                tamper_evidence["hash_chain"] = "Hash chain integrity broken"
        
        # 3. Digital signature verification
        signature_verified = True
        if self.verification_level in [VerificationLevel.DIGITAL_SIGNATURE, VerificationLevel.BLOCKCHAIN_STYLE]:
            signature_verified = await self._verify_digital_signature(entry)
            if not signature_verified:
                tamper_types.append(TamperType.SIGNATURE_INVALID)
                tamper_evidence["digital_signature"] = "Digital signature invalid"
        
        # 4. Merkle tree verification
        merkle_verified = True
        if self.verification_level in [VerificationLevel.MERKLE_TREE, VerificationLevel.BLOCKCHAIN_STYLE]:
            merkle_verified = await self._verify_merkle_inclusion(entry)
            if not merkle_verified:
                tamper_types.append(TamperType.INSERTION)
                tamper_evidence["merkle_tree"] = "Merkle tree verification failed"
        
        # 5. Timestamp verification
        timestamp_verified = await self._verify_timestamp(entry)
        if not timestamp_verified:
            tamper_types.append(TamperType.TIMESTAMP_MANIPULATION)
            tamper_evidence["timestamp"] = "Timestamp inconsistency detected"
        
        # Determine overall status
        all_verified = hash_verified and chain_verified and signature_verified and merkle_verified and timestamp_verified
        tampering_detected = len(tamper_types) > 0
        
        if all_verified:
            status = IntegrityStatus.VERIFIED
        elif tampering_detected:
            status = IntegrityStatus.COMPROMISED
        else:
            status = IntegrityStatus.VERIFICATION_FAILED
        
        verification_time = (time.time() - start_time) * 1000
        
        # Create verification result
        result = IntegrityVerificationResult(
            verification_id=verification_id,
            entry_id=entry_id,
            status=status,
            verification_level=self.verification_level,
            timestamp=datetime.utcnow(),
            hash_verified=hash_verified,
            chain_verified=chain_verified,
            signature_verified=signature_verified,
            merkle_verified=merkle_verified,
            tampering_detected=tampering_detected,
            tamper_types=tamper_types,
            tamper_evidence=tamper_evidence,
            verification_time_ms=verification_time,
            computational_cost=self._calculate_computational_cost(verification_time)
        )
        
        # Store verification result
        self.verification_results[entry_id] = result
        
        # Generate alert if tampering detected
        if tampering_detected:
            await self._generate_integrity_alert(entry_id, tamper_types, tamper_evidence)
        
        # Update statistics
        self._update_verification_stats(result)
        
        logger.info("AUDIT_INTEGRITY - Verification completed",
                   verification_id=verification_id,
                   entry_id=entry_id,
                   status=status.name,
                   tampering_detected=tampering_detected,
                   verification_time_ms=round(verification_time, 2))
        
        return result
    
    async def _verify_content_hash(self, entry: AuditLogEntry) -> bool:
        """Verify content hash integrity"""
        
        # Reconstruct content hash
        entry_content = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "user_id": entry.user_id,
            "resource": entry.resource,
            "action": entry.action,
            "outcome": entry.outcome,
            "details": entry.details
        }
        
        content_json = json.dumps(entry_content, sort_keys=True)
        calculated_hash = hashlib.sha256(content_json.encode()).hexdigest()
        
        return calculated_hash == entry.content_hash
    
    async def _verify_hash_chain(self, entry: AuditLogEntry) -> bool:
        """Verify hash chain integrity"""
        
        if not entry.previous_hash:
            # First entry in chain
            return True
        
        # Find previous entry in sequence
        entry_index = self.entry_sequence.index(entry.entry_id)
        if entry_index == 0:
            return entry.previous_hash is None
        
        previous_entry_id = self.entry_sequence[entry_index - 1]
        previous_entry = self.audit_entries[previous_entry_id]
        
        # Verify chain link
        chain_input = f"{previous_entry.content_hash}{entry.content_hash}"
        expected_hash = hashlib.sha256(chain_input.encode()).hexdigest()
        
        return expected_hash == entry.content_hash
    
    async def _verify_digital_signature(self, entry: AuditLogEntry) -> bool:
        """Verify digital signature"""
        
        if not entry.digital_signature:
            return True  # No signature to verify
        
        # Reconstruct signed content
        entry_content = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "user_id": entry.user_id,
            "resource": entry.resource,
            "action": entry.action,
            "outcome": entry.outcome,
            "details": entry.details
        }
        
        content_json = json.dumps(entry_content, sort_keys=True)
        signature_data = content_json.encode()
        
        return self.signature_verifier.verify_signature(signature_data, entry.digital_signature)
    
    async def _verify_merkle_inclusion(self, entry: AuditLogEntry) -> bool:
        """Verify Merkle tree inclusion"""
        
        # Find entry index in sequence
        try:
            entry_index = self.entry_sequence.index(entry.entry_id)
        except ValueError:
            return False
        
        # Reconstruct leaf data
        merkle_leaf_data = f"{entry.entry_id}{entry.content_hash}".encode()
        
        # Get Merkle proof
        try:
            proof = self.merkle_tree.get_proof(entry_index)
            return self.merkle_tree.verify_proof(merkle_leaf_data, proof)
        except (IndexError, Exception):
            return False
    
    async def _verify_timestamp(self, entry: AuditLogEntry) -> bool:
        """Verify timestamp consistency"""
        
        # Basic timestamp validation
        current_time = datetime.utcnow()
        entry_time = entry.timestamp
        
        # Entry shouldn't be from the future
        if entry_time > current_time + timedelta(minutes=5):
            return False
        
        # Entry shouldn't be too old without proper historical context
        if entry_time < current_time - timedelta(days=365 * 10):  # 10 years
            return False
        
        # Check sequence ordering
        entry_index = self.entry_sequence.index(entry.entry_id)
        if entry_index > 0:
            previous_entry_id = self.entry_sequence[entry_index - 1]
            previous_entry = self.audit_entries[previous_entry_id]
            
            # Timestamps should be roughly sequential
            if entry_time < previous_entry.timestamp - timedelta(minutes=1):
                return False
        
        return True
    
    async def _verify_entry_immediate(self, entry_id: str):
        """Immediate verification for critical entries"""
        
        result = await self.verify_entry_integrity(entry_id)
        
        if result.tampering_detected:
            logger.critical("AUDIT_INTEGRITY - IMMEDIATE TAMPERING DETECTED",
                           entry_id=entry_id,
                           tamper_types=[t.value for t in result.tamper_types],
                           evidence=result.tamper_evidence)
    
    async def _generate_integrity_alert(self, entry_id: str, tamper_types: List[TamperType], 
                                       tamper_evidence: Dict[str, Any]):
        """Generate integrity violation alert"""
        
        alert_id = str(uuid.uuid4())
        
        # Determine severity based on tamper types
        severity = "low"
        investigation_required = False
        
        critical_tampers = {TamperType.DELETION, TamperType.SIGNATURE_INVALID, TamperType.CHAIN_BROKEN}
        high_tampers = {TamperType.MODIFICATION, TamperType.INSERTION}
        
        if any(t in critical_tampers for t in tamper_types):
            severity = "critical"
            investigation_required = True
        elif any(t in high_tampers for t in tamper_types):
            severity = "high"
            investigation_required = True
        elif TamperType.TIMESTAMP_MANIPULATION in tamper_types:
            severity = "medium"
        
        alert = IntegrityAlert(
            alert_id=alert_id,
            entry_id=entry_id,
            tamper_types=tamper_types,
            detection_timestamp=datetime.utcnow(),
            severity=severity,
            evidence=tamper_evidence,
            investigation_required=investigation_required
        )
        
        self.integrity_alerts.append(alert)
        self.verification_stats["alerts_generated"] += 1
        
        logger.warning("AUDIT_INTEGRITY - Tampering alert generated",
                      alert_id=alert_id,
                      entry_id=entry_id,
                      severity=severity,
                      tamper_types=[t.value for t in tamper_types])
    
    def _calculate_computational_cost(self, verification_time_ms: float) -> str:
        """Calculate computational cost classification"""
        
        if verification_time_ms < 10:
            return "low"
        elif verification_time_ms < 50:
            return "medium"
        elif verification_time_ms < 200:
            return "high"
        else:
            return "very_high"
    
    def _update_verification_stats(self, result: IntegrityVerificationResult):
        """Update verification statistics"""
        
        self.verification_stats["total_verifications"] += 1
        
        if result.tampering_detected:
            self.verification_stats["failed_verifications"] += 1
        
        # Update average verification time
        total_time = (self.verification_stats["average_verification_time_ms"] * 
                     (self.verification_stats["total_verifications"] - 1) + 
                     result.verification_time_ms)
        self.verification_stats["average_verification_time_ms"] = \
            total_time / self.verification_stats["total_verifications"]
    
    def _start_background_verification(self):
        """Start background verification thread"""
        
        if not self.monitoring_active:
            return
        
        def verification_worker():
            while self.monitoring_active:
                try:
                    asyncio.run(self._background_verification_cycle())
                    time.sleep(self.verification_interval_seconds)
                except Exception as e:
                    logger.error("Background verification error", error=str(e))
                    time.sleep(60)  # Wait longer on error
        
        self.verification_thread = threading.Thread(target=verification_worker, daemon=True)
        self.verification_thread.start()
    
    async def _background_verification_cycle(self):
        """Background verification cycle"""
        
        if not self.audit_entries:
            return
        
        # Verify random sample of entries
        sample_size = min(10, len(self.audit_entries))
        sample_entry_ids = secrets.SystemRandom().sample(list(self.audit_entries.keys()), sample_size)
        
        for entry_id in sample_entry_ids:
            try:
                await self.verify_entry_integrity(entry_id)
            except Exception as e:
                logger.error("Background verification failed",
                           entry_id=entry_id,
                           error=str(e))
    
    async def verify_full_chain(self) -> Dict[str, Any]:
        """Verify integrity of entire audit chain"""
        
        verification_start = time.time()
        
        results = {
            "chain_valid": True,
            "total_entries": len(self.audit_entries),
            "verified_entries": 0,
            "compromised_entries": 0,
            "verification_errors": 0,
            "chain_breaks": [],
            "compromised_entry_ids": [],
            "verification_time_seconds": 0.0
        }
        
        # Verify each entry in sequence
        for entry_id in self.entry_sequence:
            try:
                result = await self.verify_entry_integrity(entry_id)
                
                if result.status == IntegrityStatus.VERIFIED:
                    results["verified_entries"] += 1
                elif result.status == IntegrityStatus.COMPROMISED:
                    results["compromised_entries"] += 1
                    results["compromised_entry_ids"].append(entry_id)
                    results["chain_valid"] = False
                else:
                    results["verification_errors"] += 1
                    results["chain_valid"] = False
                
                # Check for chain breaks
                if not result.chain_verified:
                    results["chain_breaks"].append(entry_id)
                    
            except Exception as e:
                results["verification_errors"] += 1
                results["chain_valid"] = False
                logger.error("Chain verification error",
                           entry_id=entry_id,
                           error=str(e))
        
        results["verification_time_seconds"] = time.time() - verification_start
        
        logger.info("AUDIT_INTEGRITY - Full chain verification completed",
                   chain_valid=results["chain_valid"],
                   total_entries=results["total_entries"],
                   compromised_entries=results["compromised_entries"],
                   verification_time=round(results["verification_time_seconds"], 2))
        
        return results
    
    async def generate_integrity_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive integrity report"""
        
        # Filter entries by date range
        period_entries = [
            entry for entry in self.audit_entries.values()
            if start_date <= entry.timestamp <= end_date
        ]
        
        # Filter verification results
        period_verifications = [
            result for result in self.verification_results.values()
            if start_date <= result.timestamp <= end_date
        ]
        
        # Filter alerts
        period_alerts = [
            alert for alert in self.integrity_alerts
            if start_date <= alert.detection_timestamp <= end_date
        ]
        
        # Calculate metrics
        total_entries = len(period_entries)
        verified_entries = len([r for r in period_verifications if r.status == IntegrityStatus.VERIFIED])
        compromised_entries = len([r for r in period_verifications if r.status == IntegrityStatus.COMPROMISED])
        
        # Tamper type breakdown
        tamper_breakdown = {}
        for alert in period_alerts:
            for tamper_type in alert.tamper_types:
                tamper_breakdown[tamper_type.value] = tamper_breakdown.get(tamper_type.value, 0) + 1
        
        # Alert severity breakdown
        alert_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for alert in period_alerts:
            alert_severity[alert.severity] = alert_severity.get(alert.severity, 0) + 1
        
        report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "integrity_summary": {
                "total_audit_entries": total_entries,
                "verified_entries": verified_entries,
                "compromised_entries": compromised_entries,
                "verification_rate": (verified_entries / total_entries * 100) if total_entries > 0 else 0,
                "integrity_score": ((total_entries - compromised_entries) / total_entries * 100) if total_entries > 0 else 100
            },
            "verification_metrics": {
                "total_verifications": len(period_verifications),
                "average_verification_time_ms": sum(r.verification_time_ms for r in period_verifications) / len(period_verifications) if period_verifications else 0,
                "verification_level": self.verification_level.value,
                "background_monitoring_active": self.monitoring_active
            },
            "tampering_analysis": {
                "total_alerts": len(period_alerts),
                "tamper_type_breakdown": tamper_breakdown,
                "alert_severity_breakdown": alert_severity,
                "investigation_required": len([a for a in period_alerts if a.investigation_required])
            },
            "compliance_status": {
                "soc2_type_ii_compliance": compromised_entries == 0,
                "hipaa_audit_trail_integrity": verified_entries / total_entries >= 0.99 if total_entries > 0 else True,
                "immutable_log_requirement": self.verification_level in [VerificationLevel.BLOCKCHAIN_STYLE, VerificationLevel.DIGITAL_SIGNATURE],
                "real_time_monitoring": self.monitoring_active
            },
            "system_performance": {
                "total_verifications_lifetime": self.verification_stats["total_verifications"],
                "failed_verifications_lifetime": self.verification_stats["failed_verifications"],
                "average_verification_time_ms_lifetime": self.verification_stats["average_verification_time_ms"],
                "alerts_generated_lifetime": self.verification_stats["alerts_generated"]
            }
        }
        
        return report
    
    def stop_monitoring(self):
        """Stop background integrity monitoring"""
        self.monitoring_active = False
        if self.verification_thread:
            self.verification_thread.join(timeout=5)

# Global audit integrity verifier
audit_integrity_verifier: Optional[AuditIntegrityVerifier] = None

def initialize_audit_integrity_verifier(verification_level: VerificationLevel = VerificationLevel.HASH_CHAIN) -> AuditIntegrityVerifier:
    """Initialize global audit integrity verifier"""
    global audit_integrity_verifier
    audit_integrity_verifier = AuditIntegrityVerifier(verification_level)
    return audit_integrity_verifier

def get_audit_integrity_verifier() -> AuditIntegrityVerifier:
    """Get global audit integrity verifier"""
    if audit_integrity_verifier is None:
        raise RuntimeError("Audit integrity verifier not initialized")
    return audit_integrity_verifier

# Convenience functions
async def add_verified_audit_entry(event_type: str, user_id: str, resource: str, 
                                  action: str, outcome: str, details: Dict[str, Any]) -> str:
    """Add audit entry with integrity protection"""
    return await get_audit_integrity_verifier().add_audit_entry(
        event_type, user_id, resource, action, outcome, details
    )

async def verify_audit_entry_integrity(entry_id: str) -> IntegrityVerificationResult:
    """Verify integrity of specific audit entry"""
    return await get_audit_integrity_verifier().verify_entry_integrity(entry_id)

async def verify_complete_audit_chain() -> Dict[str, Any]:
    """Verify integrity of complete audit chain"""
    return await get_audit_integrity_verifier().verify_full_chain()

async def generate_audit_integrity_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate audit integrity compliance report"""
    return await get_audit_integrity_verifier().generate_integrity_report(start_date, end_date)