"""
Clinical Workflows Service Unit Tests

Comprehensive unit testing for service layer with role-based scenarios.
Tests every function, edge case, and error condition in isolation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, Mock, patch, call

from sqlalchemy.exc import IntegrityError
from app.modules.clinical_workflows.service import ClinicalWorkflowService
from app.modules.clinical_workflows.schemas import (
    ClinicalWorkflowCreate, ClinicalWorkflowUpdate, ClinicalWorkflowResponse,
    ClinicalWorkflowStepCreate, ClinicalWorkflowStepUpdate,
    ClinicalEncounterCreate, ClinicalWorkflowSearchFilters,
    WorkflowType, WorkflowStatus, WorkflowPriority, StepStatus, EncounterClass
)
from app.modules.clinical_workflows.exceptions import (
    WorkflowNotFoundError, InvalidWorkflowStatusError,
    ProviderAuthorizationError, WorkflowValidationError
)


class TestClinicalWorkflowServiceCreation:
    """Test workflow creation with different user roles and scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.physician
    async def test_create_workflow_physician_success(
        self, clinical_workflow_service, valid_workflow_data, physician_user,
        db_session, mock_encryption_service, mock_audit_service, mock_event_bus
    ):
        """Test successful workflow creation by physician."""
        # Mock security validations
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.verify_clinical_consent = AsyncMock(
            return_value=(True, "consent_123")
        )
        clinical_workflow_service.security.calculate_risk_score = Mock(return_value=25)
        clinical_workflow_service.security.encrypt_clinical_field = AsyncMock(
            return_value="encrypted_data"
        )
        
        # Mock database workflow creation
        with patch('app.modules.clinical_workflows.service.ClinicalWorkflow') as mock_workflow:
            mock_instance = Mock()
            mock_instance.id = uuid4()
            mock_instance.patient_id = valid_workflow_data["patient_id"]
            mock_instance.provider_id = physician_user.id
            mock_instance.workflow_type = WorkflowType.ENCOUNTER.value
            mock_instance.status = WorkflowStatus.ACTIVE.value
            mock_instance.priority = WorkflowPriority.ROUTINE.value
            mock_instance.created_at = datetime.utcnow()
            mock_instance.updated_at = datetime.utcnow()
            mock_instance.version = 1
            mock_instance.risk_score = 25
            mock_instance.consent_id = "consent_123"
            mock_workflow.return_value = mock_instance
            
            # Create workflow
            workflow_create = ClinicalWorkflowCreate(**valid_workflow_data)
            result = await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=physician_user.id,
                session=db_session
            )
            
            # Assertions
            assert isinstance(result, ClinicalWorkflowResponse)
            assert result.patient_id == valid_workflow_data["patient_id"]
            assert result.workflow_type == WorkflowType.ENCOUNTER
            assert result.status == WorkflowStatus.ACTIVE
            
            # Verify security checks were called
            clinical_workflow_service.security.validate_provider_permissions.assert_called_once()
            clinical_workflow_service.security.verify_clinical_consent.assert_called_once()
            
            # Verify PHI encryption was called for sensitive fields
            assert mock_encryption_service.encrypt.call_count >= 2  # At least chief_complaint and history
            
            # Verify audit logging
            mock_audit_service.log_event.assert_called_with(
                event_type="CLINICAL_WORKFLOW_CREATED",
                user_id=str(physician_user.id),
                additional_data={
                    "workflow_id": str(mock_instance.id),
                    "patient_id": str(valid_workflow_data["patient_id"]),
                    "workflow_type": WorkflowType.ENCOUNTER.value,
                    "risk_score": 25,
                    "consent_id": "consent_123"
                }
            )
            
            # Verify event bus publishing
            mock_event_bus.publish.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.nurse
    async def test_create_workflow_nurse_limited_access(
        self, clinical_workflow_service, valid_workflow_data, nurse_user, db_session
    ):
        """Test workflow creation by nurse with limited permissions."""
        # Mock permission denial for specific actions
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=False)
        
        workflow_create = ClinicalWorkflowCreate(**valid_workflow_data)
        
        with pytest.raises(Exception):  # Should raise permission error
            await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=nurse_user.id,
                session=db_session
            )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.unauthorized
    async def test_create_workflow_unauthorized_user(
        self, clinical_workflow_service, valid_workflow_data, unauthorized_user, db_session
    ):
        """Test workflow creation by unauthorized user."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=False)
        
        workflow_create = ClinicalWorkflowCreate(**valid_workflow_data)
        
        with pytest.raises(Exception):
            await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=unauthorized_user.id,
                session=db_session
            )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_workflow_consent_denied(
        self, clinical_workflow_service, valid_workflow_data, physician_user, db_session
    ):
        """Test workflow creation when patient consent is denied."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.verify_clinical_consent = AsyncMock(
            return_value=(False, None)
        )
        
        workflow_create = ClinicalWorkflowCreate(**valid_workflow_data)
        
        with pytest.raises(Exception):
            await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=physician_user.id,
                session=db_session
            )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_workflow_encryption_failure(
        self, clinical_workflow_service, valid_workflow_data, physician_user, db_session
    ):
        """Test workflow creation when PHI encryption fails."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.verify_clinical_consent = AsyncMock(
            return_value=(True, "consent_123")
        )
        clinical_workflow_service.security.encrypt_clinical_field = AsyncMock(
            side_effect=Exception("Encryption service unavailable")
        )
        
        workflow_create = ClinicalWorkflowCreate(**valid_workflow_data)
        
        with pytest.raises(Exception):
            await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=physician_user.id,
                session=db_session
            )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_emergency_workflow_high_risk(
        self, clinical_workflow_service, physician_user, db_session, patient_id
    ):
        """Test emergency workflow creation with high risk score."""
        # Create emergency workflow data
        emergency_data = {
            "patient_id": patient_id,
            "provider_id": physician_user.id,
            "workflow_type": WorkflowType.EMERGENCY,
            "priority": WorkflowPriority.EMERGENCY,
            "chief_complaint": "Cardiac arrest, CPR in progress",
            "location": "Emergency Department",
            "department": "Emergency Medicine"
        }
        
        # Mock high risk score for emergency
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.verify_clinical_consent = AsyncMock(
            return_value=(True, "emergency_consent")
        )
        clinical_workflow_service.security.calculate_risk_score = Mock(return_value=95)
        clinical_workflow_service.security.encrypt_clinical_field = AsyncMock(
            return_value="encrypted_emergency_data"
        )
        
        with patch('app.modules.clinical_workflows.service.ClinicalWorkflow') as mock_workflow:
            mock_instance = Mock()
            mock_instance.id = uuid4()
            mock_instance.risk_score = 95
            mock_workflow.return_value = mock_instance
            
            workflow_create = ClinicalWorkflowCreate(**emergency_data)
            result = await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=physician_user.id,
                session=db_session
            )
            
            # Verify high risk score calculation
            clinical_workflow_service.security.calculate_risk_score.assert_called_once()
            call_args = clinical_workflow_service.security.calculate_risk_score.call_args[0][0]
            assert call_args["priority"] == WorkflowPriority.EMERGENCY.value
            assert call_args["workflow_type"] == WorkflowType.EMERGENCY.value


class TestClinicalWorkflowServiceRetrieval:
    """Test workflow retrieval with different access patterns."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.physician
    async def test_get_workflow_physician_full_access(
        self, clinical_workflow_service, active_workflow, physician_user, db_session
    ):
        """Test workflow retrieval by physician with full PHI access."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.decrypt_clinical_field = AsyncMock(
            return_value="decrypted_clinical_data"
        )
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            
            result = await clinical_workflow_service.get_workflow(
                workflow_id=active_workflow.id,
                user_id=physician_user.id,
                session=db_session,
                decrypt_phi=True
            )
            
            assert isinstance(result, ClinicalWorkflowResponse)
            assert result.id == active_workflow.id
            
            # Verify PHI decryption was attempted
            clinical_workflow_service.security.decrypt_clinical_field.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.admin
    async def test_get_workflow_admin_analytics_access(
        self, clinical_workflow_service, active_workflow, clinical_admin_user, db_session
    ):
        """Test workflow retrieval by admin for analytics (no PHI)."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            
            result = await clinical_workflow_service.get_workflow(
                workflow_id=active_workflow.id,
                user_id=clinical_admin_user.id,
                session=db_session,
                decrypt_phi=False,  # Admin access without PHI
                access_purpose="analytics"
            )
            
            assert isinstance(result, ClinicalWorkflowResponse)
            # Verify no PHI decryption for analytics access
            clinical_workflow_service.security.decrypt_clinical_field.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_workflow_not_found(
        self, clinical_workflow_service, physician_user, db_session
    ):
        """Test workflow retrieval when workflow doesn't exist."""
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = None
            
            with pytest.raises(WorkflowNotFoundError):
                await clinical_workflow_service.get_workflow(
                    workflow_id=uuid4(),
                    user_id=physician_user.id,
                    session=db_session
                )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.unauthorized
    async def test_get_workflow_unauthorized_access(
        self, clinical_workflow_service, active_workflow, unauthorized_user, db_session
    ):
        """Test workflow retrieval by unauthorized user."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=False)
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            
            with pytest.raises(Exception):
                await clinical_workflow_service.get_workflow(
                    workflow_id=active_workflow.id,
                    user_id=unauthorized_user.id,
                    session=db_session
                )


class TestClinicalWorkflowServiceUpdates:
    """Test workflow updates with transition validation."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_workflow_valid_transition(
        self, clinical_workflow_service, active_workflow, physician_user, db_session
    ):
        """Test valid workflow status transition."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.validate_workflow_transition = AsyncMock(
            return_value=(True, None)
        )
        clinical_workflow_service.security.encrypt_clinical_field = AsyncMock(
            return_value="encrypted_update_data"
        )
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            
            update_data = ClinicalWorkflowUpdate(
                status=WorkflowStatus.COMPLETED,
                completion_percentage=100,
                assessment="Patient stable, symptoms resolved"
            )
            
            # Mock get_workflow for return value
            clinical_workflow_service.get_workflow = AsyncMock(
                return_value=ClinicalWorkflowResponse(
                    id=active_workflow.id,
                    patient_id=active_workflow.patient_id,
                    provider_id=active_workflow.provider_id,
                    workflow_type=WorkflowType.ENCOUNTER,
                    status=WorkflowStatus.COMPLETED,
                    priority=WorkflowPriority.ROUTINE,
                    completion_percentage=100,
                    created_at=active_workflow.created_at,
                    updated_at=datetime.utcnow(),
                    access_count=0,
                    version=active_workflow.version + 1
                )
            )
            
            result = await clinical_workflow_service.update_workflow(
                workflow_id=active_workflow.id,
                update_data=update_data,
                user_id=physician_user.id,
                session=db_session
            )
            
            assert isinstance(result, ClinicalWorkflowResponse)
            clinical_workflow_service.security.validate_workflow_transition.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_workflow_invalid_transition(
        self, clinical_workflow_service, completed_workflow, physician_user, db_session
    ):
        """Test invalid workflow status transition."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.validate_workflow_transition = AsyncMock(
            return_value=(False, "Cannot transition from COMPLETED to ACTIVE")
        )
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = completed_workflow
            
            update_data = ClinicalWorkflowUpdate(status=WorkflowStatus.ACTIVE)
            
            with pytest.raises(InvalidWorkflowStatusError):
                await clinical_workflow_service.update_workflow(
                    workflow_id=completed_workflow.id,
                    update_data=update_data,
                    user_id=physician_user.id,
                    session=db_session
                )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_complete_workflow_success(
        self, clinical_workflow_service, active_workflow, physician_user, db_session
    ):
        """Test successful workflow completion."""
        # Mock update_workflow method
        expected_response = ClinicalWorkflowResponse(
            id=active_workflow.id,
            patient_id=active_workflow.patient_id,
            provider_id=active_workflow.provider_id,
            workflow_type=WorkflowType.ENCOUNTER,
            status=WorkflowStatus.COMPLETED,
            priority=WorkflowPriority.ROUTINE,
            completion_percentage=100,
            created_at=active_workflow.created_at,
            updated_at=datetime.utcnow(),
            access_count=0,
            version=active_workflow.version + 1
        )
        
        clinical_workflow_service.update_workflow = AsyncMock(return_value=expected_response)
        
        result = await clinical_workflow_service.complete_workflow(
            workflow_id=active_workflow.id,
            user_id=physician_user.id,
            session=db_session,
            completion_notes="Workflow completed successfully"
        )
        
        assert isinstance(result, ClinicalWorkflowResponse)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.completion_percentage == 100
        
        # Verify update_workflow was called with correct parameters
        clinical_workflow_service.update_workflow.assert_called_once()
        call_args = clinical_workflow_service.update_workflow.call_args[1]
        assert call_args["update_data"].status == WorkflowStatus.COMPLETED
        assert call_args["update_data"].completion_percentage == 100


class TestClinicalWorkflowServiceSearch:
    """Test workflow search with different filter scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_workflows_by_patient(
        self, clinical_workflow_service, physician_user, patient_id, db_session
    ):
        """Test searching workflows by patient ID."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        
        # Mock database query
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_workflows = [Mock(id=uuid4(), patient_id=patient_id) for _ in range(3)]
            mock_query.return_value.filter.return_value.filter.return_value.count.return_value = 3
            mock_query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_workflows
            
            filters = ClinicalWorkflowSearchFilters(patient_id=patient_id)
            workflows, total_count = await clinical_workflow_service.search_workflows(
                filters=filters,
                user_id=physician_user.id,
                session=db_session
            )
            
            assert len(workflows) == 3
            assert total_count == 3
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_workflows_unauthorized_patient(
        self, clinical_workflow_service, unauthorized_user, patient_id, db_session
    ):
        """Test searching workflows for unauthorized patient access."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=False)
        
        filters = ClinicalWorkflowSearchFilters(patient_id=patient_id)
        workflows, total_count = await clinical_workflow_service.search_workflows(
            filters=filters,
            user_id=unauthorized_user.id,
            session=db_session
        )
        
        assert len(workflows) == 0
        assert total_count == 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_workflows_with_filters(
        self, clinical_workflow_service, physician_user, db_session
    ):
        """Test searching workflows with multiple filters."""
        # Mock complex query with filters
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_workflows = [Mock(id=uuid4()) for _ in range(5)]
            mock_query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 5
            mock_query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_workflows
            
            filters = ClinicalWorkflowSearchFilters(
                workflow_type=WorkflowType.ENCOUNTER,
                status=[WorkflowStatus.ACTIVE, WorkflowStatus.COMPLETED],
                priority=[WorkflowPriority.URGENT],
                page=1,
                page_size=10
            )
            
            workflows, total_count = await clinical_workflow_service.search_workflows(
                filters=filters,
                user_id=physician_user.id,
                session=db_session
            )
            
            assert len(workflows) == 5
            assert total_count == 5


class TestClinicalWorkflowServiceSteps:
    """Test workflow step management."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_add_workflow_step_success(
        self, clinical_workflow_service, active_workflow, physician_user, db_session
    ):
        """Test successful workflow step addition."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.encrypt_clinical_field = AsyncMock(
            return_value="encrypted_step_data"
        )
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            
            with patch('app.modules.clinical_workflows.service.ClinicalWorkflowStep') as mock_step:
                mock_step_instance = Mock()
                mock_step_instance.id = uuid4()
                mock_step_instance.workflow_id = active_workflow.id
                mock_step_instance.step_name = "patient_assessment"
                mock_step_instance.step_type = "clinical_evaluation"
                mock_step_instance.step_order = 1
                mock_step_instance.status = StepStatus.PENDING.value
                mock_step_instance.created_at = datetime.utcnow()
                mock_step_instance.updated_at = datetime.utcnow()
                mock_step.return_value = mock_step_instance
                
                step_data = ClinicalWorkflowStepCreate(
                    workflow_id=active_workflow.id,
                    step_name="patient_assessment",
                    step_type="clinical_evaluation",
                    step_order=1,
                    notes="Initial patient assessment"
                )
                
                result = await clinical_workflow_service.add_workflow_step(
                    workflow_id=active_workflow.id,
                    step_data=step_data,
                    user_id=physician_user.id,
                    session=db_session
                )
                
                assert result.step_name == "patient_assessment"
                assert result.step_order == 1
                clinical_workflow_service.security.encrypt_clinical_field.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_complete_workflow_step_success(
        self, clinical_workflow_service, physician_user, db_session
    ):
        """Test successful workflow step completion."""
        # Create mock step and workflow
        mock_step = Mock()
        mock_step.id = uuid4()
        mock_step.workflow_id = uuid4()
        mock_step.step_name = "assessment"
        mock_step.step_type = "clinical"
        mock_step.step_order = 1
        mock_step.status = StepStatus.PENDING.value
        
        mock_workflow = Mock()
        mock_workflow.patient_id = uuid4()
        
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.encrypt_clinical_field = AsyncMock(
            return_value="encrypted_completion_notes"
        )
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            # Setup query chain for step and workflow
            mock_query.return_value.filter_by.side_effect = [
                Mock(first=Mock(return_value=mock_step)),  # For step query
                Mock(first=Mock(return_value=mock_workflow))  # For workflow query
            ]
            
            completion_data = ClinicalWorkflowStepUpdate(
                status=StepStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                actual_duration_minutes=30,
                quality_score=95,
                notes="Step completed successfully"
            )
            
            # Mock the event bus publish
            clinical_workflow_service.event_bus.publish = AsyncMock()
            
            result = await clinical_workflow_service.complete_workflow_step(
                step_id=mock_step.id,
                completion_data=completion_data,
                user_id=physician_user.id,
                session=db_session
            )
            
            # Verify event was published
            clinical_workflow_service.event_bus.publish.assert_called_once()


class TestClinicalWorkflowServiceAnalytics:
    """Test analytics generation with role-based access."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.admin
    async def test_get_workflow_analytics_admin_access(
        self, clinical_workflow_service, clinical_admin_user, db_session
    ):
        """Test analytics generation for admin user."""
        # Mock database queries for analytics
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            # Mock count queries
            mock_query.return_value.filter.return_value.count.side_effect = [
                100,  # total_workflows
                85,   # completed_workflows
                60,   # encounter workflows
                25,   # care_plan workflows
                15,   # consultation workflows
                85,   # completed status
                10,   # active status
                5     # cancelled status
            ]
            
            # Mock workflows with duration
            mock_workflows = [Mock(actual_duration_minutes=90) for _ in range(10)]
            mock_query.return_value.filter.return_value.all.return_value = mock_workflows
            
            filters = ClinicalWorkflowSearchFilters()
            analytics = await clinical_workflow_service.get_workflow_analytics(
                filters=filters,
                user_id=clinical_admin_user.id,
                session=db_session
            )
            
            assert analytics.total_workflows == 100
            assert analytics.completed_workflows == 85
            assert analytics.completion_rate == 0.85
            assert analytics.average_duration_minutes == 90.0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.ai_researcher
    async def test_collect_training_data_ai_researcher(
        self, clinical_workflow_service, ai_researcher_user, active_workflow, db_session
    ):
        """Test AI training data collection by authorized researcher."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            
            result = await clinical_workflow_service.collect_training_data(
                workflow_id=active_workflow.id,
                data_type="clinical_reasoning",
                user_id=ai_researcher_user.id,
                session=db_session,
                anonymization_level="full"
            )
            
            assert result["workflow_type"] == active_workflow.workflow_type
            assert result["anonymization_level"] == "full"
            assert "collection_timestamp" in result
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.unauthorized
    async def test_collect_training_data_unauthorized(
        self, clinical_workflow_service, unauthorized_user, active_workflow, db_session
    ):
        """Test AI training data collection by unauthorized user."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=False)
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            
            with pytest.raises(Exception):
                await clinical_workflow_service.collect_training_data(
                    workflow_id=active_workflow.id,
                    data_type="clinical_reasoning",
                    user_id=unauthorized_user.id,
                    session=db_session
                )


class TestClinicalWorkflowServiceErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_database_connection_failure(
        self, clinical_workflow_service, physician_user, valid_workflow_data
    ):
        """Test handling of database connection failures."""
        # Mock database session that raises exception
        mock_session = Mock()
        mock_session.add.side_effect = Exception("Database connection lost")
        
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.verify_clinical_consent = AsyncMock(
            return_value=(True, "consent_123")
        )
        
        workflow_create = ClinicalWorkflowCreate(**valid_workflow_data)
        
        with pytest.raises(WorkflowValidationError):
            await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=physician_user.id,
                session=mock_session
            )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_workflow_update(
        self, clinical_workflow_service, active_workflow, physician_user, db_session
    ):
        """Test handling of concurrent workflow updates."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.validate_workflow_transition = AsyncMock(
            return_value=(True, None)
        )
        
        # Mock optimistic locking conflict
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter_by.return_value.first.return_value = active_workflow
            db_session.commit.side_effect = IntegrityError("", "", "")
            
            update_data = ClinicalWorkflowUpdate(status=WorkflowStatus.COMPLETED)
            
            with pytest.raises(WorkflowValidationError):
                await clinical_workflow_service.update_workflow(
                    workflow_id=active_workflow.id,
                    update_data=update_data,
                    user_id=physician_user.id,
                    session=db_session
                )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_workflow_data(
        self, clinical_workflow_service, physician_user, db_session
    ):
        """Test handling of invalid workflow data."""
        clinical_workflow_service.security.validate_provider_permissions = AsyncMock(return_value=True)
        clinical_workflow_service.security.verify_clinical_consent = AsyncMock(
            return_value=(True, "consent_123")
        )
        
        # Create workflow with invalid data (missing required fields)
        invalid_data = {"workflow_type": WorkflowType.ENCOUNTER}
        
        with pytest.raises(Exception):  # Should raise validation error
            workflow_create = ClinicalWorkflowCreate(**invalid_data)
            await clinical_workflow_service.create_workflow(
                workflow_data=workflow_create,
                user_id=physician_user.id,
                session=db_session
            )