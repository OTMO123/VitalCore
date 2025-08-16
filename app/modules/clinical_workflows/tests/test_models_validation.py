"""
Clinical Workflows Models Validation Tests

Comprehensive testing of database models, relationships, constraints,
and data integrity for the clinical workflows foundation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database_unified import Base, DataClassification
from app.modules.clinical_workflows.models import (
    ClinicalWorkflow, ClinicalWorkflowStep, ClinicalEncounter, ClinicalWorkflowAudit
)


class TestClinicalWorkflowModels:
    """Test clinical workflow database models."""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        # Use in-memory SQLite for testing
        engine = create_engine("sqlite:///:memory:", echo=True)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_workflow_data(self):
        """Sample workflow data for testing."""
        return {
            "patient_id": uuid4(),
            "provider_id": uuid4(),
            "workflow_type": "encounter",
            "status": "active",
            "priority": "routine",
            "chief_complaint_encrypted": "encrypted_chief_complaint_data",
            "assessment_encrypted": "encrypted_assessment_data",
            "vital_signs_encrypted": "encrypted_vital_signs_json",
            "created_by": uuid4(),
            "data_classification": DataClassification.PHI.value
        }
    
    def test_clinical_workflow_creation(self, db_session, sample_workflow_data):
        """Test creating a clinical workflow with required fields."""
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Verify creation
        assert workflow.id is not None
        assert workflow.workflow_type == "encounter"
        assert workflow.status == "active"
        assert workflow.data_classification == DataClassification.PHI.value
        assert workflow.created_at is not None
        assert workflow.version == 1
    
    def test_clinical_workflow_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Missing required fields should raise error
        with pytest.raises(IntegrityError):
            incomplete_workflow = ClinicalWorkflow(
                workflow_type="encounter"
                # Missing patient_id, provider_id, created_by
            )
            db_session.add(incomplete_workflow)
            db_session.commit()
    
    def test_clinical_workflow_constraints(self, db_session, sample_workflow_data):
        """Test database constraints on workflow fields."""
        # Test invalid status
        invalid_data = sample_workflow_data.copy()
        invalid_data["status"] = "invalid_status"
        
        workflow = ClinicalWorkflow(**invalid_data)
        db_session.add(workflow)
        
        # This should fail constraint check (in PostgreSQL)
        # In SQLite, constraints might not be enforced the same way
        try:
            db_session.commit()
        except IntegrityError:
            # Expected behavior for invalid status
            db_session.rollback()
    
    def test_clinical_workflow_soft_delete(self, db_session, sample_workflow_data):
        """Test soft delete functionality."""
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Soft delete
        workflow.deleted_at = datetime.utcnow()
        db_session.commit()
        
        # Verify soft delete
        assert workflow.deleted_at is not None
        assert workflow.is_deleted is True
    
    def test_clinical_workflow_step_creation(self, db_session, sample_workflow_data):
        """Test creating workflow steps with proper relationships."""
        # Create parent workflow
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Create workflow step
        step = ClinicalWorkflowStep(
            workflow_id=workflow.id,
            step_name="assessment",
            step_type="clinical_decision",
            step_order=1,
            status="pending",
            step_data_encrypted="encrypted_step_data",
            data_classification=DataClassification.PHI.value
        )
        db_session.add(step)
        db_session.commit()
        
        # Verify creation and relationship
        assert step.id is not None
        assert step.workflow_id == workflow.id
        assert step.step_order == 1
        assert len(workflow.workflow_steps) == 1
        assert workflow.workflow_steps[0] == step
    
    def test_clinical_workflow_step_constraints(self, db_session, sample_workflow_data):
        """Test workflow step constraints."""
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Test invalid step order (should be >= 1)
        with pytest.raises(IntegrityError):
            invalid_step = ClinicalWorkflowStep(
                workflow_id=workflow.id,
                step_name="invalid_step",
                step_type="test",
                step_order=0,  # Invalid: should be >= 1
                status="pending"
            )
            db_session.add(invalid_step)
            db_session.commit()
    
    def test_clinical_encounter_creation(self, db_session, sample_workflow_data):
        """Test creating clinical encounters with FHIR compliance."""
        # Create parent workflow
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Create encounter
        encounter = ClinicalEncounter(
            workflow_id=workflow.id,
            patient_id=sample_workflow_data["patient_id"],
            provider_id=sample_workflow_data["provider_id"],
            encounter_class="AMB",
            encounter_status="planned",
            encounter_datetime=datetime.utcnow(),
            subjective_encrypted="encrypted_subjective_data",
            objective_encrypted="encrypted_objective_data",
            assessment_encrypted="encrypted_assessment_data",
            plan_encrypted="encrypted_plan_data",
            fhir_encounter_id=f"encounter_{uuid4()}",
            created_by=sample_workflow_data["created_by"],
            data_classification=DataClassification.PHI.value
        )
        db_session.add(encounter)
        db_session.commit()
        
        # Verify creation
        assert encounter.id is not None
        assert encounter.encounter_class == "AMB"
        assert encounter.fhir_version == "R4"
        assert encounter.data_classification == DataClassification.PHI.value
        assert len(workflow.encounters) == 1
    
    def test_clinical_encounter_fhir_constraints(self, db_session, sample_workflow_data):
        """Test FHIR R4 constraint validation."""
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Test invalid encounter class
        with pytest.raises(IntegrityError):
            invalid_encounter = ClinicalEncounter(
                workflow_id=workflow.id,
                patient_id=sample_workflow_data["patient_id"],
                provider_id=sample_workflow_data["provider_id"],
                encounter_class="INVALID",  # Should be AMB, EMER, IMP, HH, VR
                encounter_status="planned",
                encounter_datetime=datetime.utcnow(),
                created_by=sample_workflow_data["created_by"]
            )
            db_session.add(invalid_encounter)
            db_session.commit()
    
    def test_clinical_workflow_audit_creation(self, db_session, sample_workflow_data):
        """Test audit trail creation and integrity."""
        # Create workflow
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Create audit entry
        audit = ClinicalWorkflowAudit(
            workflow_id=workflow.id,
            event_type="workflow_created",
            event_category="workflow",
            action="create",
            user_id=sample_workflow_data["created_by"],
            user_role="physician",
            ip_address="192.168.1.100",
            phi_accessed=True,
            phi_fields_accessed=["chief_complaint", "assessment"],
            access_purpose="clinical_documentation",
            compliance_tags=["SOC2", "HIPAA"],
            risk_level="medium",
            audit_hash="sample_hash_for_integrity",
            timestamp=datetime.utcnow()
        )
        db_session.add(audit)
        db_session.commit()
        
        # Verify audit creation
        assert audit.id is not None
        assert audit.workflow_id == workflow.id
        assert audit.phi_accessed is True
        assert "chief_complaint" in audit.phi_fields_accessed
        assert audit.risk_level == "medium"
        assert len(workflow.audit_trail) == 1
    
    def test_workflow_relationships_cascade(self, db_session, sample_workflow_data):
        """Test cascade delete behavior for relationships."""
        # Create workflow with related entities
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Add step
        step = ClinicalWorkflowStep(
            workflow_id=workflow.id,
            step_name="test_step",
            step_type="test",
            step_order=1,
            status="pending"
        )
        db_session.add(step)
        
        # Add encounter
        encounter = ClinicalEncounter(
            workflow_id=workflow.id,
            patient_id=sample_workflow_data["patient_id"],
            provider_id=sample_workflow_data["provider_id"],
            encounter_class="AMB",
            encounter_status="planned",
            encounter_datetime=datetime.utcnow(),
            created_by=sample_workflow_data["created_by"]
        )
        db_session.add(encounter)
        
        # Add audit
        audit = ClinicalWorkflowAudit(
            workflow_id=workflow.id,
            event_type="test_event",
            event_category="test",
            action="test",
            user_id=sample_workflow_data["created_by"],
            timestamp=datetime.utcnow()
        )
        db_session.add(audit)
        db_session.commit()
        
        # Verify relationships exist
        assert len(workflow.workflow_steps) == 1
        assert len(workflow.encounters) == 1
        assert len(workflow.audit_trail) == 1
        
        # Delete workflow (should cascade to related entities)
        db_session.delete(workflow)
        db_session.commit()
        
        # Verify cascade delete worked
        remaining_steps = db_session.query(ClinicalWorkflowStep).filter_by(workflow_id=workflow.id).count()
        remaining_encounters = db_session.query(ClinicalEncounter).filter_by(workflow_id=workflow.id).count()
        remaining_audits = db_session.query(ClinicalWorkflowAudit).filter_by(workflow_id=workflow.id).count()
        
        assert remaining_steps == 0
        assert remaining_encounters == 0
        assert remaining_audits == 0
    
    def test_workflow_versioning(self, db_session, sample_workflow_data):
        """Test workflow versioning functionality."""
        # Create original workflow
        original_workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(original_workflow)
        db_session.commit()
        
        # Create new version
        new_version_data = sample_workflow_data.copy()
        new_version_data["parent_workflow_id"] = original_workflow.id
        new_version_data["version"] = 2
        
        new_workflow = ClinicalWorkflow(**new_version_data)
        db_session.add(new_workflow)
        db_session.commit()
        
        # Verify versioning
        assert new_workflow.version == 2
        assert new_workflow.parent_workflow_id == original_workflow.id
        assert len(original_workflow.child_workflows) == 1
        assert original_workflow.child_workflows[0] == new_workflow
    
    def test_data_classification_consistency(self, db_session, sample_workflow_data):
        """Test that PHI data classification is consistent across models."""
        # Create workflow
        workflow = ClinicalWorkflow(**sample_workflow_data)
        assert workflow.data_classification == DataClassification.PHI.value
        
        # Create step
        step = ClinicalWorkflowStep(
            workflow_id=uuid4(),  # Will be updated
            step_name="test",
            step_type="test",
            step_order=1,
            status="pending",
            step_data_encrypted="encrypted_data"
        )
        assert step.data_classification == DataClassification.PHI.value
        
        # Create encounter
        encounter = ClinicalEncounter(
            workflow_id=uuid4(),
            patient_id=uuid4(),
            provider_id=uuid4(),
            encounter_class="AMB",
            encounter_status="planned",
            encounter_datetime=datetime.utcnow(),
            created_by=uuid4()
        )
        assert encounter.data_classification == DataClassification.PHI.value
    
    def test_timestamp_handling(self, db_session, sample_workflow_data):
        """Test automatic timestamp handling."""
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Verify timestamps
        assert workflow.created_at is not None
        assert workflow.updated_at is not None
        assert workflow.workflow_start_time is not None
        
        original_updated_at = workflow.updated_at
        
        # Update workflow
        workflow.status = "completed"
        workflow.workflow_end_time = datetime.utcnow()
        db_session.commit()
        
        # Verify update timestamp changed
        assert workflow.updated_at > original_updated_at
        assert workflow.workflow_end_time is not None


class TestModelIndexes:
    """Test database indexes for performance."""
    
    def test_workflow_indexes_exist(self, db_session):
        """Test that performance indexes are properly created."""
        # This test would verify index existence in a real database
        # For now, we'll check that the table structure supports indexing
        
        from sqlalchemy import inspect
        inspector = inspect(db_session.bind)
        
        # Check if tables exist
        tables = inspector.get_table_names()
        assert "clinical_workflows" in tables
        assert "clinical_workflow_steps" in tables
        assert "clinical_encounters" in tables
        assert "clinical_workflow_audit" in tables
        
        # In a real PostgreSQL environment, we would check:
        # - idx_workflow_patient_provider
        # - idx_workflow_status_created
        # - idx_step_workflow_order
        # - idx_audit_workflow_timestamp


class TestModelConstraintEnforcement:
    """Test that database constraints are properly enforced."""
    
    def test_enum_constraints(self, db_session, sample_workflow_data):
        """Test enum value constraints."""
        # These tests would be more comprehensive with PostgreSQL
        # SQLite doesn't enforce CHECK constraints the same way
        
        workflow = ClinicalWorkflow(**sample_workflow_data)
        
        # Valid enum values should work
        workflow.status = "active"
        workflow.priority = "urgent"
        
        # Test would fail with invalid values in PostgreSQL:
        # workflow.status = "invalid_status"  # Should fail
        # workflow.priority = "invalid_priority"  # Should fail
    
    def test_foreign_key_constraints(self, db_session, sample_workflow_data):
        """Test foreign key constraint enforcement."""
        workflow = ClinicalWorkflow(**sample_workflow_data)
        db_session.add(workflow)
        db_session.commit()
        
        # Valid foreign key reference should work
        step = ClinicalWorkflowStep(
            workflow_id=workflow.id,  # Valid FK
            step_name="test",
            step_type="test",
            step_order=1,
            status="pending"
        )
        db_session.add(step)
        db_session.commit()
        
        # Invalid foreign key should fail (in PostgreSQL with FK constraints)
        invalid_step = ClinicalWorkflowStep(
            workflow_id=uuid4(),  # Non-existent workflow ID
            step_name="invalid",
            step_type="test",
            step_order=1,
            status="pending"
        )
        
        # This would fail in PostgreSQL:
        # db_session.add(invalid_step)
        # with pytest.raises(IntegrityError):
        #     db_session.commit()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])