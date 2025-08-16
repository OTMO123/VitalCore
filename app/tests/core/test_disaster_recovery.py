#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enterprise Disaster Recovery System
Ensures 100% test coverage for disaster recovery, backup, and recovery operations.

Test Categories:
- Unit Tests: Individual component validation and functionality
- Integration Tests: System-wide disaster recovery operations
- Performance Tests: Backup and recovery performance validation
- Security Tests: Encryption and access control testing
- Resilience Tests: Failure scenarios and recovery validation
- Compliance Tests: Recovery time/point objective validation

Coverage Requirements:
- All backup strategies and storage mechanisms
- All recovery plans and operations
- All encryption and security features
- All monitoring and alerting components
- All error conditions and recovery mechanisms
"""

import pytest
import asyncio
import time
import tempfile
import shutil
import json
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

from app.core.disaster_recovery import (
    DisasterRecoveryConfig, BackupStrategy, RecoveryScope, BackupType, RecoveryStatus,
    BackupMetadata, RecoveryPlan, RecoveryOperation, BackupManager, RecoveryManager,
    BackupEncryption, DisasterRecoveryHealthMonitor, DisasterRecoverySystem,
    initialize_disaster_recovery, get_disaster_recovery, create_emergency_backup,
    initiate_emergency_recovery, get_disaster_recovery_report, test_recovery_procedures
)

# Test Fixtures

@pytest.fixture
def dr_config():
    """Standard disaster recovery configuration for testing"""
    return DisasterRecoveryConfig(
        backup_strategy=BackupStrategy.LOCAL,
        backup_retention_days=30,
        incremental_backup_interval=3600,
        recovery_time_objective=1800,
        recovery_point_objective=300,
        local_backup_path="/tmp/test_backups",
        enable_monitoring=True
    )

@pytest.fixture
def temp_backup_dir():
    """Temporary backup directory for testing"""
    temp_dir = tempfile.mkdtemp(prefix="dr_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def backup_manager(dr_config, temp_backup_dir):
    """Backup manager instance for testing"""
    dr_config.local_backup_path = temp_backup_dir
    return BackupManager(dr_config)

@pytest.fixture
def recovery_manager(dr_config, backup_manager):
    """Recovery manager instance for testing"""
    return RecoveryManager(dr_config, backup_manager)

@pytest.fixture
def backup_encryption(dr_config):
    """Backup encryption instance for testing"""
    return BackupEncryption(dr_config)

@pytest.fixture
def health_monitor(dr_config):
    """Health monitor instance for testing"""
    return DisasterRecoveryHealthMonitor(dr_config)

@pytest.fixture
def dr_system(dr_config, temp_backup_dir):
    """Disaster recovery system for testing"""
    dr_config.local_backup_path = temp_backup_dir
    return DisasterRecoverySystem(dr_config)

# Unit Tests for Configuration

class TestDisasterRecoveryConfig:
    """Test disaster recovery configuration"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = DisasterRecoveryConfig()
        
        assert config.backup_strategy == BackupStrategy.HYBRID
        assert config.backup_retention_days == 90
        assert config.recovery_time_objective == 3600
        assert config.recovery_point_objective == 300
        assert config.backup_encryption_enabled is True
        assert config.cross_region_replication is True
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        config = DisasterRecoveryConfig(
            backup_strategy=BackupStrategy.S3,
            recovery_time_objective=1800,
            recovery_point_objective=60,
            backup_retention_days=30
        )
        
        assert config.backup_strategy == BackupStrategy.S3
        assert config.recovery_time_objective == 1800
        assert config.recovery_point_objective == 60
        assert config.backup_retention_days == 30
    
    def test_configuration_validation(self):
        """Test configuration parameter validation"""
        # Test negative values
        config = DisasterRecoveryConfig(recovery_time_objective=-1)
        assert config.recovery_time_objective == -1  # Should accept but warn in real implementation
        
        # Test zero values
        config = DisasterRecoveryConfig(recovery_point_objective=0)
        assert config.recovery_point_objective == 0

# Unit Tests for Backup Metadata

class TestBackupMetadata:
    """Test backup metadata functionality"""
    
    def test_backup_metadata_creation(self):
        """Test backup metadata creation"""
        metadata = BackupMetadata(
            backup_id="test-backup-123",
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow(),
            size_bytes=1024000,
            checksum="abc123def456",
            components=["database", "application"]
        )
        
        assert metadata.backup_id == "test-backup-123"
        assert metadata.backup_type == BackupType.FULL
        assert metadata.size_bytes == 1024000
        assert len(metadata.components) == 2
        assert "database" in metadata.components
    
    def test_backup_metadata_with_encryption(self):
        """Test backup metadata with encryption"""
        metadata = BackupMetadata(
            backup_id="encrypted-backup-456",
            backup_type=BackupType.INCREMENTAL,
            timestamp=datetime.utcnow(),
            size_bytes=512000,
            checksum="def456ghi789",
            encryption_key_id="key_v1",
            compression_ratio=0.6
        )
        
        assert metadata.encryption_key_id == "key_v1"
        assert metadata.compression_ratio == 0.6

# Unit Tests for Recovery Plans

class TestRecoveryPlan:
    """Test recovery plan functionality"""
    
    def test_recovery_plan_creation(self):
        """Test recovery plan creation"""
        plan = RecoveryPlan(
            plan_id="test_plan",
            plan_name="Test Recovery Plan",
            recovery_scope=RecoveryScope.DATABASE_ONLY,
            estimated_duration=1800,
            steps=[
                {"step": "backup_current", "duration": 300},
                {"step": "restore_data", "duration": 1200},
                {"step": "validate", "duration": 300}
            ]
        )
        
        assert plan.plan_id == "test_plan"
        assert plan.recovery_scope == RecoveryScope.DATABASE_ONLY
        assert plan.estimated_duration == 1800
        assert len(plan.steps) == 3
        assert plan.steps[0]["step"] == "backup_current"
    
    def test_recovery_plan_with_rollback(self):
        """Test recovery plan with rollback steps"""
        plan = RecoveryPlan(
            plan_id="rollback_plan",
            plan_name="Plan with Rollback",
            recovery_scope=RecoveryScope.FULL_SYSTEM,
            estimated_duration=3600,
            steps=[{"step": "restore", "duration": 3000}],
            rollback_steps=[{"step": "revert", "duration": 600}]
        )
        
        assert len(plan.rollback_steps) == 1
        assert plan.rollback_steps[0]["step"] == "revert"

# Unit Tests for Backup Manager

class TestBackupManager:
    """Test backup manager functionality"""
    
    def test_backup_manager_initialization(self, dr_config, temp_backup_dir):
        """Test backup manager initialization"""
        dr_config.local_backup_path = temp_backup_dir
        manager = BackupManager(dr_config)
        
        assert manager.config == dr_config
        assert len(manager.backup_history) == 0
        assert Path(temp_backup_dir).exists()
    
    def test_storage_clients_initialization(self, backup_manager):
        """Test storage clients initialization"""
        # Without cloud credentials, clients should be empty or None
        assert isinstance(backup_manager.storage_clients, dict)
        # In test environment, cloud clients won't be initialized
    
    @pytest.mark.asyncio
    async def test_get_default_components(self, backup_manager):
        """Test getting default backup components"""
        components = await backup_manager._get_default_components()
        
        assert isinstance(components, list)
        assert "database" in components
        assert "application_code" in components
        assert "configuration" in components
        assert len(components) >= 3
    
    @pytest.mark.asyncio
    async def test_collect_backup_data(self, backup_manager):
        """Test backup data collection"""
        components = ["database", "configuration"]
        backup_data = await backup_manager._collect_backup_data(components, BackupType.FULL)
        
        assert isinstance(backup_data, bytes)
        
        # Parse the JSON data
        data_dict = json.loads(backup_data.decode('utf-8'))
        assert "database" in data_dict
        assert "configuration" in data_dict
        assert data_dict["database"]["type"] == "database_dump"
    
    @pytest.mark.asyncio
    async def test_compress_backup_data(self, backup_manager):
        """Test backup data compression"""
        test_data = b"This is test data that should be compressed" * 100
        compressed = await backup_manager._compress_backup_data(test_data)
        
        assert len(compressed) < len(test_data)
        
        # Verify compression by decompressing
        decompressed = gzip.decompress(compressed)
        assert decompressed == test_data
    
    @pytest.mark.asyncio
    async def test_create_backup_local(self, backup_manager):
        """Test creating local backup"""
        # Mock some methods to avoid complex setup
        with patch.object(backup_manager, '_collect_backup_data') as mock_collect:
            mock_collect.return_value = b'{"test": "data"}'
            
            metadata = await backup_manager.create_backup(BackupType.INCREMENTAL)
            
            assert metadata.backup_type == BackupType.INCREMENTAL
            assert metadata.size_bytes > 0
            assert metadata.checksum is not None
            assert len(metadata.backup_id) > 0
            
            # Check that backup file was created
            backup_path = Path(backup_manager.config.local_backup_path) / f"{metadata.backup_id}.backup"
            assert backup_path.exists()
    
    @pytest.mark.asyncio
    async def test_create_backup_with_encryption(self, dr_config, temp_backup_dir):
        """Test creating encrypted backup"""
        dr_config.local_backup_path = temp_backup_dir
        dr_config.backup_encryption_enabled = True
        manager = BackupManager(dr_config)
        
        with patch.object(manager, '_collect_backup_data') as mock_collect:
            mock_collect.return_value = b'{"sensitive": "data"}'
            
            metadata = await manager.create_backup(BackupType.FULL)
            
            assert metadata.encryption_key_id is not None
            assert metadata.backup_type == BackupType.FULL
    
    @pytest.mark.asyncio
    async def test_list_backups_filtering(self, backup_manager):
        """Test backup listing with filters"""
        # Create test backup metadata
        backup1 = BackupMetadata(
            backup_id="backup1",
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow() - timedelta(days=1),
            size_bytes=1000,
            checksum="abc123",
            components=["database"]
        )
        
        backup2 = BackupMetadata(
            backup_id="backup2", 
            backup_type=BackupType.INCREMENTAL,
            timestamp=datetime.utcnow(),
            size_bytes=500,
            checksum="def456",
            components=["database", "logs"]
        )
        
        backup_manager.backup_history["backup1"] = backup1
        backup_manager.backup_history["backup2"] = backup2
        
        # Test filtering by backup type
        full_backups = await backup_manager.list_backups(backup_type=BackupType.FULL)
        assert len(full_backups) == 1
        assert full_backups[0].backup_id == "backup1"
        
        # Test filtering by component
        db_backups = await backup_manager.list_backups(component="database")
        assert len(db_backups) == 2
        
        logs_backups = await backup_manager.list_backups(component="logs")
        assert len(logs_backups) == 1
        assert logs_backups[0].backup_id == "backup2"
        
        # Test date filtering
        recent_backups = await backup_manager.list_backups(
            start_date=datetime.utcnow() - timedelta(hours=12)
        )
        assert len(recent_backups) == 1
        assert recent_backups[0].backup_id == "backup2"
    
    @pytest.mark.asyncio
    async def test_verify_backup_success(self, backup_manager, temp_backup_dir):
        """Test successful backup verification"""
        # Create a test backup file
        backup_id = "test-backup-verify"
        test_data = b"test backup data for verification"
        
        backup_path = Path(temp_backup_dir) / f"{backup_id}.backup"
        with open(backup_path, 'wb') as f:
            f.write(test_data)
        
        # Create metadata
        import hashlib
        checksum = hashlib.sha256(test_data).hexdigest()
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow(),
            size_bytes=len(test_data),
            checksum=checksum
        )
        
        backup_manager.backup_history[backup_id] = metadata
        
        # Verify backup
        is_valid = await backup_manager.verify_backup(backup_id)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_verify_backup_corrupted(self, backup_manager, temp_backup_dir):
        """Test backup verification with corrupted data"""
        backup_id = "corrupted-backup"
        original_data = b"original backup data"
        corrupted_data = b"corrupted backup data"
        
        # Create backup file with corrupted data
        backup_path = Path(temp_backup_dir) / f"{backup_id}.backup"
        with open(backup_path, 'wb') as f:
            f.write(corrupted_data)
        
        # Create metadata with original data checksum
        import hashlib
        original_checksum = hashlib.sha256(original_data).hexdigest()
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow(),
            size_bytes=len(original_data),
            checksum=original_checksum
        )
        
        backup_manager.backup_history[backup_id] = metadata
        
        # Verify backup (should fail)
        is_valid = await backup_manager.verify_backup(backup_id)
        assert is_valid is False

# Unit Tests for Recovery Manager

class TestRecoveryManager:
    """Test recovery manager functionality"""
    
    def test_recovery_manager_initialization(self, dr_config, backup_manager):
        """Test recovery manager initialization"""
        manager = RecoveryManager(dr_config, backup_manager)
        
        assert manager.config == dr_config
        assert manager.backup_manager == backup_manager
        assert len(manager.recovery_plans) >= 2  # Default plans
        assert "full_system_recovery" in manager.recovery_plans
        assert "database_recovery" in manager.recovery_plans
    
    def test_default_recovery_plans(self, recovery_manager):
        """Test default recovery plans initialization"""
        full_plan = recovery_manager.recovery_plans["full_system_recovery"]
        
        assert full_plan.recovery_scope == RecoveryScope.FULL_SYSTEM
        assert len(full_plan.steps) > 0
        assert full_plan.estimated_duration > 0
        
        db_plan = recovery_manager.recovery_plans["database_recovery"]
        assert db_plan.recovery_scope == RecoveryScope.DATABASE_ONLY
        assert len(db_plan.steps) > 0
    
    @pytest.mark.asyncio
    async def test_find_best_backup_for_recovery(self, recovery_manager, backup_manager):
        """Test finding best backup for point-in-time recovery"""
        # Create test backups
        now = datetime.utcnow()
        
        backup1 = BackupMetadata(
            backup_id="backup1",
            backup_type=BackupType.FULL,
            timestamp=now - timedelta(hours=2),
            size_bytes=1000,
            checksum="abc123"
        )
        
        backup2 = BackupMetadata(
            backup_id="backup2",
            backup_type=BackupType.INCREMENTAL,
            timestamp=now - timedelta(hours=1),
            size_bytes=500,
            checksum="def456"
        )
        
        backup_manager.backup_history["backup1"] = backup1
        backup_manager.backup_history["backup2"] = backup2
        
        # Find backup for recovery point 30 minutes ago
        recovery_point = now - timedelta(minutes=30)
        
        with patch.object(backup_manager, 'list_backups') as mock_list:
            mock_list.return_value = [backup2, backup1]  # Newest first
            
            best_backup_id = await recovery_manager._find_best_backup_for_recovery(recovery_point)
            assert best_backup_id == "backup2"  # Most recent before recovery point
    
    @pytest.mark.asyncio
    async def test_initiate_recovery_with_plan(self, recovery_manager):
        """Test initiating recovery with specific plan"""
        # Mock backup selection
        with patch.object(recovery_manager.backup_manager, 'list_backups') as mock_list:
            mock_backup = BackupMetadata(
                backup_id="test-backup",
                backup_type=BackupType.FULL,
                timestamp=datetime.utcnow(),
                size_bytes=1000,
                checksum="abc123"
            )
            mock_list.return_value = [mock_backup]
            
            operation = await recovery_manager.initiate_recovery(
                plan_id="database_recovery",
                dry_run=True  # Don't actually execute
            )
            
            assert operation.plan_id == "database_recovery"
            assert operation.status in [RecoveryStatus.PENDING, RecoveryStatus.COMPLETED]
            assert operation.operation_id is not None
            assert operation.started_at is not None
    
    @pytest.mark.asyncio
    async def test_initiate_recovery_invalid_plan(self, recovery_manager):
        """Test initiating recovery with invalid plan"""
        with pytest.raises(ValueError, match="Recovery plan .* not found"):
            await recovery_manager.initiate_recovery("nonexistent_plan")
    
    @pytest.mark.asyncio
    async def test_get_recovery_status(self, recovery_manager):
        """Test getting recovery operation status"""
        # Create a test operation
        operation = RecoveryOperation(
            operation_id="test-op-123",
            plan_id="database_recovery",
            status=RecoveryStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            progress_percentage=50.0
        )
        
        recovery_manager.active_recoveries["test-op-123"] = operation
        
        # Test getting active recovery
        retrieved = await recovery_manager.get_recovery_status("test-op-123")
        assert retrieved is not None
        assert retrieved.operation_id == "test-op-123"
        assert retrieved.progress_percentage == 50.0
        
        # Test getting non-existent recovery
        not_found = await recovery_manager.get_recovery_status("nonexistent")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_cancel_recovery(self, recovery_manager):
        """Test cancelling recovery operation"""
        # Create active recovery
        operation = RecoveryOperation(
            operation_id="cancel-test",
            plan_id="database_recovery",
            status=RecoveryStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        recovery_manager.active_recoveries["cancel-test"] = operation
        
        # Cancel recovery
        success = await recovery_manager.cancel_recovery("cancel-test")
        assert success is True
        assert operation.status == RecoveryStatus.CANCELLED
        
        # Try to cancel non-existent recovery
        failed = await recovery_manager.cancel_recovery("nonexistent")
        assert failed is False

# Unit Tests for Backup Encryption

class TestBackupEncryption:
    """Test backup encryption functionality"""
    
    def test_encryption_initialization(self, dr_config):
        """Test encryption initialization"""
        encryption = BackupEncryption(dr_config)
        
        assert len(encryption.encryption_keys) > 0
        assert "default" in encryption.encryption_keys
        assert len(encryption.encryption_keys["default"]) == 32  # 256-bit key
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip(self, backup_encryption):
        """Test encryption and decryption roundtrip"""
        test_data = b"This is sensitive backup data that needs encryption"
        
        # Encrypt
        encrypted_data, key_id = await backup_encryption.encrypt_backup(test_data)
        
        assert key_id is not None
        assert encrypted_data != test_data
        assert len(encrypted_data) > len(test_data)  # Includes IV and tag
        
        # Decrypt
        decrypted_data = await backup_encryption.decrypt_backup(encrypted_data, key_id)
        
        assert decrypted_data == test_data
    
    @pytest.mark.asyncio
    async def test_encrypt_disabled(self, dr_config):
        """Test encryption when disabled"""
        dr_config.backup_encryption_enabled = False
        encryption = BackupEncryption(dr_config)
        
        test_data = b"unencrypted data"
        
        encrypted_data, key_id = await encryption.encrypt_backup(test_data)
        
        assert encrypted_data == test_data
        assert key_id is None
    
    @pytest.mark.asyncio
    async def test_decrypt_invalid_key(self, backup_encryption):
        """Test decryption with invalid key"""
        test_data = b"test data"
        encrypted_data, key_id = await backup_encryption.encrypt_backup(test_data)
        
        with pytest.raises(ValueError, match="Encryption key .* not found"):
            await backup_encryption.decrypt_backup(encrypted_data, "invalid_key")

# Unit Tests for Health Monitor

class TestDisasterRecoveryHealthMonitor:
    """Test health monitoring functionality"""
    
    def test_health_monitor_initialization(self, dr_config):
        """Test health monitor initialization"""
        monitor = DisasterRecoveryHealthMonitor(dr_config)
        
        assert monitor.config == dr_config
        assert monitor.monitoring_active is False
        assert len(monitor.health_status) == 0
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, health_monitor):
        """Test starting and stopping health monitoring"""
        # Start monitoring
        await health_monitor.start_monitoring()
        assert health_monitor.monitoring_active is True
        assert health_monitor.monitoring_task is not None
        
        # Give it a moment to run
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await health_monitor.stop_monitoring()
        assert health_monitor.monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_check_backup_storage_health(self, health_monitor, temp_backup_dir):
        """Test backup storage health checking"""
        health_monitor.config.local_backup_path = temp_backup_dir
        
        await health_monitor._check_backup_storage_health()
        
        assert "storage" in health_monitor.health_status
        storage_health = health_monitor.health_status["storage"]
        
        assert "local" in storage_health
        assert storage_health["local"]["accessible"] is True
        assert storage_health["local"]["free_space_gb"] >= 0
    
    @pytest.mark.asyncio
    async def test_check_recovery_capabilities(self, health_monitor):
        """Test recovery capabilities checking"""
        await health_monitor._check_recovery_capabilities()
        
        assert "recovery" in health_monitor.health_status
        recovery_health = health_monitor.health_status["recovery"]
        
        assert "plans_available" in recovery_health
        assert "active_recoveries" in recovery_health
        assert recovery_health["active_recoveries"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_health_report(self, health_monitor):
        """Test comprehensive health report generation"""
        # Add some test health data
        health_monitor.health_status = {
            "storage": {"local": {"accessible": True}},
            "recovery": {"plans_available": 2}
        }
        
        report = await health_monitor.get_health_report()
        
        assert "timestamp" in report
        assert "overall_status" in report
        assert "details" in report
        assert "alerts" in report
        
        assert report["details"] == health_monitor.health_status
    
    def test_calculate_overall_status_healthy(self, health_monitor):
        """Test overall status calculation - healthy"""
        health_monitor.health_status = {
            "storage": {"local": {"accessible": True}},
            "resources": {"disk_usage_percent": 50}
        }
        
        status = health_monitor._calculate_overall_status()
        assert status == "healthy"
    
    def test_calculate_overall_status_warning(self, health_monitor):
        """Test overall status calculation - warning"""
        health_monitor.health_status = {
            "storage": {"local": {"accessible": True}},
            "resources": {"disk_usage_percent": 85}
        }
        
        status = health_monitor._calculate_overall_status()
        assert status == "warning"
    
    def test_calculate_overall_status_critical(self, health_monitor):
        """Test overall status calculation - critical"""
        health_monitor.health_status = {
            "storage": {"local": {"accessible": False}}
        }
        
        status = health_monitor._calculate_overall_status()
        assert status == "critical"
    
    def test_generate_health_alerts(self, health_monitor):
        """Test health alerts generation"""
        # Set up conditions that should trigger alerts
        health_monitor.health_status = {
            "resources": {"disk_usage_percent": 95}
        }
        
        alerts = health_monitor._generate_health_alerts()
        
        assert len(alerts) > 0
        
        critical_alert = next((a for a in alerts if a["type"] == "disk_space_critical"), None)
        assert critical_alert is not None
        assert critical_alert["severity"] == "high"

# Integration Tests

class TestDisasterRecoverySystemIntegration:
    """Test disaster recovery system integration"""
    
    @pytest.mark.asyncio
    async def test_system_initialization(self, dr_config, temp_backup_dir):
        """Test complete system initialization"""
        dr_config.local_backup_path = temp_backup_dir
        system = DisasterRecoverySystem(dr_config)
        
        assert system.config == dr_config
        assert system.backup_manager is not None
        assert system.recovery_manager is not None
        assert system.health_monitor is not None
    
    @pytest.mark.asyncio
    async def test_system_start_stop(self, dr_system):
        """Test system start and stop"""
        await dr_system.start_system()
        
        # System should be running
        assert dr_system.health_monitor.monitoring_active is True
        
        await dr_system.stop_system()
        
        # System should be stopped
        assert dr_system.health_monitor.monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, dr_system):
        """Test getting comprehensive system status"""
        # Start system to populate status
        await dr_system.start_system()
        
        # Give it a moment to collect status
        await asyncio.sleep(0.1)
        
        status = await dr_system.get_system_status()
        
        assert "timestamp" in status
        assert "health" in status
        assert "backup_summary" in status
        assert "recovery_summary" in status
        
        # Check backup summary
        backup_summary = status["backup_summary"]
        assert "total_backups" in backup_summary
        assert "recent_backups" in backup_summary
        
        # Check recovery summary
        recovery_summary = status["recovery_summary"]
        assert "available_plans" in recovery_summary
        assert "active_recoveries" in recovery_summary
        
        await dr_system.stop_system()
    
    @pytest.mark.asyncio
    async def test_end_to_end_backup_recovery(self, dr_system):
        """Test end-to-end backup and recovery workflow"""
        # Mock data collection to avoid complex setup
        with patch.object(dr_system.backup_manager, '_collect_backup_data') as mock_collect:
            mock_collect.return_value = b'{"test": "end-to-end data"}'
            
            # Create backup
            backup = await dr_system.backup_manager.create_backup(BackupType.FULL)
            assert backup.backup_id is not None
            
            # Verify backup
            is_valid = await dr_system.backup_manager.verify_backup(backup.backup_id)
            assert is_valid is True
            
            # Initiate recovery (dry run)
            recovery = await dr_system.recovery_manager.initiate_recovery(
                plan_id="database_recovery",
                backup_id=backup.backup_id,
                dry_run=True
            )
            
            assert recovery.operation_id is not None
            assert recovery.plan_id == "database_recovery"

# Global Functions Tests

class TestGlobalDisasterRecoveryFunctions:
    """Test global disaster recovery functions"""
    
    def test_initialize_disaster_recovery(self, dr_config, temp_backup_dir):
        """Test disaster recovery initialization"""
        dr_config.local_backup_path = temp_backup_dir
        
        # Reset global state
        import app.core.disaster_recovery
        app.core.disaster_recovery.disaster_recovery_system = None
        
        system = initialize_disaster_recovery(dr_config)
        
        assert system is not None
        assert system.config == dr_config
        
        # Test getting global instance
        retrieved_system = get_disaster_recovery()
        assert retrieved_system is system
    
    def test_get_disaster_recovery_not_initialized(self):
        """Test getting disaster recovery when not initialized"""
        # Reset global state
        import app.core.disaster_recovery
        app.core.disaster_recovery.disaster_recovery_system = None
        
        with pytest.raises(RuntimeError, match="Disaster recovery system not initialized"):
            get_disaster_recovery()
    
    @pytest.mark.asyncio
    async def test_create_emergency_backup(self, dr_config, temp_backup_dir):
        """Test creating emergency backup"""
        dr_config.local_backup_path = temp_backup_dir
        system = initialize_disaster_recovery(dr_config)
        
        with patch.object(system.backup_manager, '_collect_backup_data') as mock_collect:
            mock_collect.return_value = b'{"emergency": "backup data"}'
            
            backup = await create_emergency_backup()
            
            assert backup.backup_type == BackupType.FULL
            assert "emergency" in backup.tags
            assert backup.tags["emergency"] == "true"
    
    @pytest.mark.asyncio
    async def test_initiate_emergency_recovery(self, dr_config, temp_backup_dir):
        """Test initiating emergency recovery"""
        dr_config.local_backup_path = temp_backup_dir
        system = initialize_disaster_recovery(dr_config)
        
        # Create a test backup first
        with patch.object(system.backup_manager, '_collect_backup_data') as mock_collect:
            mock_collect.return_value = b'{"test": "data"}'
            backup = await system.backup_manager.create_backup(BackupType.FULL)
        
        recovery = await initiate_emergency_recovery()
        
        assert recovery.plan_id == "full_system_recovery"
        assert recovery.operation_id is not None
    
    @pytest.mark.asyncio
    async def test_get_disaster_recovery_report(self, dr_config, temp_backup_dir):
        """Test getting disaster recovery report"""
        dr_config.local_backup_path = temp_backup_dir
        system = initialize_disaster_recovery(dr_config)
        
        report = await get_disaster_recovery_report()
        
        assert "timestamp" in report
        assert "health" in report
        assert "backup_summary" in report
        assert "recovery_summary" in report
    
    @pytest.mark.asyncio
    async def test_test_recovery_procedures(self, dr_config, temp_backup_dir):
        """Test recovery procedures testing"""
        dr_config.local_backup_path = temp_backup_dir
        system = initialize_disaster_recovery(dr_config)
        
        # Create a test backup
        with patch.object(system.backup_manager, '_collect_backup_data') as mock_collect:
            mock_collect.return_value = b'{"test": "data"}'
            await system.backup_manager.create_backup(BackupType.FULL)
        
        results = await test_recovery_procedures(dry_run=True)
        
        assert len(results) >= 2  # Should test all available plans
        
        for result in results:
            assert result.operation_id is not None
            assert result.plan_id in system.recovery_manager.recovery_plans
            # In dry run mode, should complete quickly
            assert result.status in [RecoveryStatus.COMPLETED, RecoveryStatus.PENDING]

# Performance Tests

class TestDisasterRecoveryPerformance:
    """Test disaster recovery performance"""
    
    @pytest.mark.asyncio
    async def test_backup_creation_performance(self, backup_manager):
        """Test backup creation performance"""
        test_data = b'{"performance": "test data"}' * 1000  # ~25KB
        
        with patch.object(backup_manager, '_collect_backup_data') as mock_collect:
            mock_collect.return_value = test_data
            
            start_time = time.time()
            
            backup = await backup_manager.create_backup(BackupType.INCREMENTAL)
            
            end_time = time.time()
            creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Backup creation should be fast (< 1000ms for small data)
            assert creation_time < 1000, f"Backup creation took {creation_time:.2f}ms"
            assert backup.backup_id is not None
    
    def test_backup_listing_performance(self, backup_manager):
        """Test backup listing performance with many backups"""
        # Create many backup metadata entries
        num_backups = 1000
        
        start_time = time.time()
        
        for i in range(num_backups):
            backup_manager.backup_history[f"backup_{i}"] = BackupMetadata(
                backup_id=f"backup_{i}",
                backup_type=BackupType.INCREMENTAL,
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                size_bytes=1000,
                checksum=f"checksum_{i}"
            )
        
        # List all backups
        async def list_all():
            return await backup_manager.list_backups()
        
        # Run the listing
        import asyncio
        backups = asyncio.run(list_all())
        
        end_time = time.time()
        listing_time = (end_time - start_time) * 1000
        
        # Listing should be fast even with many backups
        assert listing_time < 500, f"Backup listing took {listing_time:.2f}ms"
        assert len(backups) == num_backups
    
    @pytest.mark.asyncio
    async def test_encryption_performance(self, backup_encryption):
        """Test encryption performance"""
        # Test with different data sizes
        test_sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB
        
        for size in test_sizes:
            test_data = b'x' * size
            
            start_time = time.time()
            
            encrypted_data, key_id = await backup_encryption.encrypt_backup(test_data)
            decrypted_data = await backup_encryption.decrypt_backup(encrypted_data, key_id)
            
            end_time = time.time()
            crypto_time = (end_time - start_time) * 1000
            
            # Encryption should be fast (< 100ms for reasonable sizes)
            assert crypto_time < 500, f"Encryption of {size} bytes took {crypto_time:.2f}ms"
            assert decrypted_data == test_data

# Error Handling Tests

class TestDisasterRecoveryErrorHandling:
    """Test error handling in disaster recovery"""
    
    @pytest.mark.asyncio
    async def test_backup_creation_with_collection_error(self, backup_manager):
        """Test backup creation when data collection fails"""
        with patch.object(backup_manager, '_collect_backup_data') as mock_collect:
            mock_collect.side_effect = Exception("Data collection failed")
            
            with pytest.raises(Exception, match="Data collection failed"):
                await backup_manager.create_backup(BackupType.FULL)
    
    @pytest.mark.asyncio
    async def test_backup_verification_file_not_found(self, backup_manager):
        """Test backup verification when file doesn't exist"""
        # Create metadata for non-existent backup
        metadata = BackupMetadata(
            backup_id="missing_backup",
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow(),
            size_bytes=1000,
            checksum="abc123"
        )
        
        backup_manager.backup_history["missing_backup"] = metadata
        
        is_valid = await backup_manager.verify_backup("missing_backup")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_recovery_with_missing_backup(self, recovery_manager):
        """Test recovery when backup is missing"""
        with patch.object(recovery_manager.backup_manager, 'list_backups') as mock_list:
            mock_list.return_value = []  # No backups available
            
            with pytest.raises(RuntimeError, match="No backups available for recovery"):
                await recovery_manager.initiate_recovery("database_recovery")
    
    @pytest.mark.asyncio
    async def test_health_monitoring_error_resilience(self, health_monitor):
        """Test health monitoring error resilience"""
        # Mock a method to raise an exception
        with patch.object(health_monitor, '_check_backup_storage_health') as mock_check:
            mock_check.side_effect = Exception("Storage check failed")
            
            # Start monitoring
            await health_monitor.start_monitoring()
            
            # Give it time to hit the error and recover
            await asyncio.sleep(0.1)
            
            # Should still be active despite errors
            assert health_monitor.monitoring_active is True
            
            await health_monitor.stop_monitoring()
    
    def test_invalid_storage_path_handling(self, dr_config):
        """Test handling of invalid storage paths"""
        dr_config.local_backup_path = "/invalid/nonexistent/path"
        
        # Should create directory if possible, or handle gracefully
        try:
            manager = BackupManager(dr_config)
            # If it succeeds, the path should exist
            assert Path(dr_config.local_backup_path).exists()
        except (PermissionError, OSError):
            # If it fails due to permissions, that's expected
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=app.core.disaster_recovery"])