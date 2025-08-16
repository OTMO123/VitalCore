#!/usr/bin/env python3
"""
Comprehensive Test Suite for Clinical Decision Support System
Tests clinical decision rules, quality measures, and healthcare analytics.

Test Categories:
- Unit Tests: Individual component testing
- Integration Tests: Cross-component workflow testing  
- Security Tests: PHI protection and audit compliance
- Performance Tests: System performance under load
- Clinical Validation Tests: Medical accuracy and evidence compliance
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock

# Import the clinical decision support system
from app.core.clinical_decision_support import (
    ClinicalDecisionSupportEngine,
    ClinicalAnalyticsEngine,
    ClinicalQualityMeasure,
    ClinicalAlert,
    ClinicalProtocol,
    ClinicalRule,
    ClinicalEvidence,
    ClinicalRiskLevel,
    DecisionSupportType,
    CQMCategory,
    EvidenceLevel
)

# Test Fixtures

@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "id": "patient_001",
        "age": 55,
        "gender": "male",
        "diagnosis_codes": ["E11.9", "I10"],  # Type 2 diabetes, essential hypertension
        "last_hba1c_value": 8.5,
        "days_since_last_hba1c": 45,
        "last_systolic_bp": 145,
        "last_diastolic_bp": 92,
        "medications": ["metformin", "lisinopril"],
        "medications_documented": True,
        "flu_vaccine_current_year": False,
        "last_visit_date": "2025-07-20"
    }

@pytest.fixture  
def sample_diabetic_population():
    """Sample population with diabetes for CQM testing"""
    return [
        {
            "id": "patient_001",
            "age": 55,
            "diagnosis_codes": ["E11.9"],
            "last_hba1c_value": 6.8,  # Good control
            "medications_documented": True
        },
        {
            "id": "patient_002", 
            "age": 62,
            "diagnosis_codes": ["E11.9"],
            "last_hba1c_value": 9.5,  # Poor control
            "medications_documented": True
        },
        {
            "id": "patient_003",
            "age": 70,
            "diagnosis_codes": ["E11.9"],
            "last_hba1c_value": 7.2,  # Acceptable control
            "medications_documented": False
        },
        {
            "id": "patient_004",
            "age": 45,
            "diagnosis_codes": ["E10.9"],  # Type 1 diabetes
            "last_hba1c_value": 10.2,  # Very poor control
            "medications_documented": True
        }
    ]

@pytest.fixture
def cds_engine():
    """Clinical decision support engine fixture"""
    return ClinicalDecisionSupportEngine()

@pytest.fixture
def clinical_analytics():
    """Clinical analytics engine fixture"""
    return ClinicalAnalyticsEngine()

# Unit Tests for Clinical Decision Support Engine

class TestClinicalDecisionSupportEngine:
    """Test suite for clinical decision support engine"""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, cds_engine):
        """Test CDS engine initializes correctly"""
        assert cds_engine is not None
        assert isinstance(cds_engine.rules, dict)
        assert isinstance(cds_engine.protocols, dict)
        assert isinstance(cds_engine.quality_measures, dict)
        assert isinstance(cds_engine.active_alerts, dict)
        
        # Wait for async initialization to complete
        await asyncio.sleep(0.1)
        
        # Check that default rules are loaded
        assert len(cds_engine.rules) > 0
        assert len(cds_engine.quality_measures) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_patient_diabetes_rule(self, cds_engine, sample_patient_data):
        """Test diabetes monitoring rule evaluation"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Modify patient data to trigger diabetes rule
        patient_data = sample_patient_data.copy()
        patient_data["days_since_last_hba1c"] = 100  # Overdue for testing
        
        alerts = await cds_engine.evaluate_patient(patient_data)
        
        # Should trigger diabetes monitoring alert
        diabetes_alerts = [a for a in alerts if "diabetes" in a.title.lower() or "hba1c" in a.message.lower()]
        assert len(diabetes_alerts) > 0
        
        alert = diabetes_alerts[0]
        assert alert.patient_id == patient_data["id"]
        assert alert.alert_type in [DecisionSupportType.QUALITY_MEASURE, DecisionSupportType.REMINDER]
        assert "hba1c" in alert.message.lower()
    
    @pytest.mark.asyncio
    async def test_evaluate_patient_hypertension_rule(self, cds_engine, sample_patient_data):
        """Test hypertension management rule evaluation"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Patient data already has elevated BP (145/92)
        alerts = await cds_engine.evaluate_patient(sample_patient_data)
        
        # Should trigger hypertension management alert
        htn_alerts = [a for a in alerts if "hypertension" in a.title.lower() or "blood pressure" in a.message.lower()]
        assert len(htn_alerts) > 0
        
        alert = htn_alerts[0]
        assert alert.patient_id == sample_patient_data["id"]
        assert alert.severity in [ClinicalRiskLevel.MODERATE, ClinicalRiskLevel.HIGH]
    
    @pytest.mark.asyncio
    async def test_evaluate_patient_drug_interaction(self, cds_engine):
        """Test drug interaction alert"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        patient_data = {
            "id": "patient_interaction",
            "age": 65,
            "medications": ["warfarin", "aspirin"],  # Dangerous combination
            "diagnosis_codes": ["I48"]  # Atrial fibrillation
        }
        
        alerts = await cds_engine.evaluate_patient(patient_data)
        
        # Should trigger drug interaction alert
        interaction_alerts = [a for a in alerts if "interaction" in a.message.lower()]
        assert len(interaction_alerts) > 0
        
        alert = interaction_alerts[0]
        assert alert.severity == ClinicalRiskLevel.CRITICAL
        assert "warfarin" in alert.message.lower()
        assert "aspirin" in alert.message.lower()
    
    @pytest.mark.asyncio
    async def test_get_patient_alerts(self, cds_engine, sample_patient_data):
        """Test retrieving active alerts for patient"""
        
        # Wait for initialization and evaluate patient
        await asyncio.sleep(0.1)
        await cds_engine.evaluate_patient(sample_patient_data)
        
        # Get active alerts
        patient_id = sample_patient_data["id"]
        active_alerts = await cds_engine.get_patient_alerts(patient_id)
        
        assert isinstance(active_alerts, list)
        # Should have alerts from evaluation
        assert len(active_alerts) > 0
        
        for alert in active_alerts:
            assert alert.patient_id == patient_id
            assert alert.acknowledged_at is None  # Should be unacknowledged
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, cds_engine, sample_patient_data):
        """Test alert acknowledgment functionality"""
        
        # Wait for initialization and evaluate patient
        await asyncio.sleep(0.1)
        alerts = await cds_engine.evaluate_patient(sample_patient_data)
        
        if alerts:
            alert_id = alerts[0].id
            clinician_id = "dr_smith"
            
            # Acknowledge the alert
            success = await cds_engine.acknowledge_alert(alert_id, clinician_id)
            assert success
            
            # Verify acknowledgment
            patient_alerts = await cds_engine.get_patient_alerts(sample_patient_data["id"])
            acknowledged_alert = None
            
            for patient_id, alert_list in cds_engine.active_alerts.items():
                for alert in alert_list:
                    if alert.id == alert_id:
                        acknowledged_alert = alert
                        break
            
            assert acknowledged_alert is not None
            assert acknowledged_alert.acknowledged_at is not None
            assert acknowledged_alert.acknowledged_by == clinician_id

# Unit Tests for Clinical Quality Measures (CQM)

class TestClinicalQualityMeasures:
    """Test suite for clinical quality measures"""
    
    @pytest.mark.asyncio
    async def test_calculate_diabetes_cqm(self, cds_engine, sample_diabetic_population):
        """Test diabetes HbA1c control CQM calculation"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        results = await cds_engine.calculate_quality_measures(sample_diabetic_population)
        
        # Should have diabetes CQM results
        diabetes_cqm_results = None
        for cqm_id, result in results.items():
            if "diabetes" in result.get("cqm_name", "").lower():
                diabetes_cqm_results = result
                break
        
        assert diabetes_cqm_results is not None
        assert diabetes_cqm_results["denominator_count"] == 4  # All 4 patients have diabetes
        assert diabetes_cqm_results["eligible_population"] >= 0
        assert 0 <= diabetes_cqm_results["compliance_rate"] <= 100
    
    @pytest.mark.asyncio
    async def test_calculate_hypertension_cqm(self, cds_engine):
        """Test hypertension control CQM calculation"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        hypertension_population = [
            {
                "id": "htn_001",
                "age": 60,
                "diagnosis_codes": ["I10"],
                "last_systolic_bp": 135,
                "last_diastolic_bp": 85  # Controlled
            },
            {
                "id": "htn_002",
                "age": 55,
                "diagnosis_codes": ["I10"],
                "last_systolic_bp": 155,
                "last_diastolic_bp": 95  # Uncontrolled
            }
        ]
        
        results = await cds_engine.calculate_quality_measures(hypertension_population)
        
        # Should have hypertension CQM results
        htn_cqm_results = None
        for cqm_id, result in results.items():
            if "blood pressure" in result.get("cqm_name", "").lower():
                htn_cqm_results = result
                break
        
        assert htn_cqm_results is not None
        assert htn_cqm_results["denominator_count"] == 2
        assert htn_cqm_results["numerator_count"] == 1  # Only one controlled
        assert htn_cqm_results["compliance_rate"] == 50.0

# Unit Tests for Clinical Analytics Engine

class TestClinicalAnalyticsEngine:
    """Test suite for clinical analytics engine"""
    
    @pytest.mark.asyncio
    async def test_generate_population_health_report(self, clinical_analytics, sample_diabetic_population):
        """Test population health report generation"""
        
        report = await clinical_analytics.generate_population_health_report(sample_diabetic_population)
        
        assert report is not None
        assert "report_id" in report
        assert "generated_at" in report
        assert report["population_size"] == 4
        
        # Check demographics section
        assert "demographics" in report
        demographics = report["demographics"]
        assert "age_statistics" in demographics
        assert "age_distribution" in demographics
        
        # Check risk stratification
        assert "risk_stratification" in report
        risk_levels = report["risk_stratification"]
        assert all(level in risk_levels for level in ["low", "moderate", "high", "critical"])
        
        # Check quality compliance
        assert "quality_compliance" in report
        quality = report["quality_compliance"]
        assert "diabetes_control" in quality
        
        # Check recommendations
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_demographics(self, clinical_analytics):
        """Test demographic analysis functionality"""
        
        test_population = [
            {"age": 25, "gender": "female"},
            {"age": 45, "gender": "male"},
            {"age": 65, "gender": "female"},
            {"age": 75, "gender": "male"}
        ]
        
        report = await clinical_analytics.generate_population_health_report(test_population)
        demographics = report["demographics"]
        
        # Check age statistics
        age_stats = demographics["age_statistics"]
        assert age_stats["mean"] == 52.5  # (25+45+65+75)/4
        assert age_stats["min"] == 25
        assert age_stats["max"] == 75
        
        # Check age distribution
        age_dist = demographics["age_distribution"]
        assert age_dist["0-17"] == 0
        assert age_dist["18-64"] == 2  # Ages 25, 45
        assert age_dist["65+"] == 2    # Ages 65, 75
    
    @pytest.mark.asyncio
    async def test_identify_care_gaps(self, clinical_analytics):
        """Test care gap identification"""
        
        test_population = [
            {
                "id": "gap_001",
                "age": 60,
                "diagnosis_codes": ["E11.9"],
                "days_since_last_hba1c": 120,  # Overdue
                "flu_vaccine_current_year": False
            },
            {
                "id": "gap_002", 
                "age": 70,
                "diagnosis_codes": ["I10"],
                "flu_vaccine_current_year": False  # Elderly without flu vaccine
            }
        ]
        
        report = await clinical_analytics.generate_population_health_report(test_population)
        care_gaps = report["care_gaps"]
        
        assert isinstance(care_gaps, list)
        assert len(care_gaps) > 0
        
        # Should identify HbA1c overdue gap
        hba1c_gap = next((gap for gap in care_gaps if "hba1c" in gap["gap_type"]), None)
        assert hba1c_gap is not None
        assert hba1c_gap["affected_patients"] == 1
        
        # Should identify flu vaccine gap
        flu_gap = next((gap for gap in care_gaps if "flu" in gap["gap_type"]), None)
        assert flu_gap is not None
        assert flu_gap["affected_patients"] == 1  # Only elderly patient without vaccine

# Integration Tests

class TestClinicalDecisionSupportIntegration:
    """Integration tests for complete clinical workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_clinical_workflow(self, cds_engine, clinical_analytics):
        """Test complete clinical decision support workflow"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Define a complex patient scenario
        complex_patient = {
            "id": "complex_001",
            "age": 65,
            "gender": "male", 
            "diagnosis_codes": ["E11.9", "I10", "I25.10"],  # Diabetes, HTN, CAD
            "last_hba1c_value": 9.2,  # Poor control
            "days_since_last_hba1c": 200,  # Very overdue
            "last_systolic_bp": 165,
            "last_diastolic_bp": 98,
            "medications": ["metformin", "insulin", "lisinopril", "aspirin"],
            "medications_documented": True,
            "flu_vaccine_current_year": False,
            "smoking_status": "current_smoker"
        }
        
        # Step 1: Evaluate patient for clinical alerts
        alerts = await cds_engine.evaluate_patient(complex_patient)
        assert len(alerts) > 0
        
        # Should have multiple high-priority alerts
        high_priority_alerts = [a for a in alerts if a.severity in [ClinicalRiskLevel.HIGH, ClinicalRiskLevel.CRITICAL]]
        assert len(high_priority_alerts) > 0
        
        # Step 2: Calculate quality measures for population
        population = [complex_patient]
        cqm_results = await cds_engine.calculate_quality_measures(population)
        assert len(cqm_results) > 0
        
        # Should show poor compliance due to uncontrolled diabetes
        diabetes_cqm = None
        for cqm_id, result in cqm_results.items():
            if "diabetes" in result.get("cqm_name", "").lower() and "poor control" in result.get("cqm_name", "").lower():
                diabetes_cqm = result
                break
        
        if diabetes_cqm:
            assert diabetes_cqm["numerator_count"] == 1  # Patient has poor control (HbA1c > 9%)
        
        # Step 3: Generate population health analytics
        population_report = await clinical_analytics.generate_population_health_report(population)
        assert population_report["population_size"] == 1
        
        # Should identify high-risk patient
        risk_strat = population_report["risk_stratification"]
        assert risk_strat["high"] + risk_strat["critical"] >= 1
        
        # Should identify care gaps
        care_gaps = population_report["care_gaps"]
        assert len(care_gaps) > 0
    
    @pytest.mark.asyncio
    async def test_multi_patient_population_analysis(self, cds_engine, clinical_analytics):
        """Test population-level analysis with multiple patients"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Create diverse patient population
        population = [
            {
                "id": "pop_001",
                "age": 45,
                "diagnosis_codes": ["E11.9"],
                "last_hba1c_value": 6.9,  # Good control
                "last_systolic_bp": 125,
                "last_diastolic_bp": 80,
                "medications_documented": True
            },
            {
                "id": "pop_002",
                "age": 55,
                "diagnosis_codes": ["I10"],
                "last_systolic_bp": 155,  # Uncontrolled HTN
                "last_diastolic_bp": 95,
                "medications_documented": True
            },
            {
                "id": "pop_003",
                "age": 70,
                "diagnosis_codes": ["E11.9", "I10"],
                "last_hba1c_value": 10.5,  # Very poor control
                "last_systolic_bp": 170,
                "last_diastolic_bp": 100,
                "days_since_last_hba1c": 150,
                "medications_documented": False
            }
        ]
        
        # Generate individual alerts for each patient
        all_alerts = []
        for patient in population:
            patient_alerts = await cds_engine.evaluate_patient(patient)
            all_alerts.extend(patient_alerts)
        
        assert len(all_alerts) > 0
        
        # Calculate population-level quality measures
        cqm_results = await cds_engine.calculate_quality_measures(population)
        assert len(cqm_results) > 0
        
        # Generate population health report
        population_report = await clinical_analytics.generate_population_health_report(population)
        
        # Verify comprehensive analysis
        assert population_report["population_size"] == 3
        assert len(population_report["recommendations"]) > 0
        
        # Should identify quality improvement opportunities
        quality_compliance = population_report["quality_compliance"]
        if "diabetes_control" in quality_compliance:
            # Should show mixed compliance rates
            assert 0 <= quality_compliance["diabetes_control"]["compliance_rate"] <= 100

# Security and Compliance Tests

class TestClinicalDecisionSupportSecurity:
    """Security and compliance tests for clinical decision support"""
    
    @pytest.mark.asyncio
    async def test_phi_data_handling(self, cds_engine):
        """Test PHI data is handled securely"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        phi_patient_data = {
            "id": "phi_patient",
            "age": 45,
            "ssn": "123-45-6789",  # PHI data
            "phone": "555-1234",   # PHI data
            "diagnosis_codes": ["E11.9"],
            "last_hba1c_value": 8.0
        }
        
        # Evaluate patient - should work without exposing PHI in logs
        alerts = await cds_engine.evaluate_patient(phi_patient_data)
        
        # Verify alerts are generated but don't contain raw PHI
        for alert in alerts:
            assert "123-45-6789" not in alert.message  # SSN should not appear in alert
            assert "555-1234" not in alert.message     # Phone should not appear in alert
    
    @pytest.mark.asyncio
    async def test_audit_logging_compliance(self, cds_engine, sample_patient_data):
        """Test that all clinical decisions are properly audited"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        with patch('structlog.get_logger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            mock_log.info = AsyncMock()
            mock_log.error = AsyncMock()
            
            # Create new engine with mocked logger
            test_engine = ClinicalDecisionSupportEngine()
            test_engine.logger = mock_log
            
            # Evaluate patient
            await test_engine.evaluate_patient(sample_patient_data)
            
            # Verify audit logging occurred
            mock_log.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_access_control_validation(self, cds_engine):
        """Test access control for clinical decision support functions"""
        
        # Test that invalid patient data is handled gracefully
        invalid_patient_data = {}
        
        alerts = await cds_engine.evaluate_patient(invalid_patient_data)
        
        # Should handle gracefully without crashing
        assert isinstance(alerts, list)
    
    @pytest.mark.asyncio
    async def test_data_validation_and_sanitization(self, cds_engine):
        """Test input validation and sanitization"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Test with malicious input
        malicious_patient_data = {
            "id": "<script>alert('xss')</script>",
            "age": "malicious_age",
            "diagnosis_codes": ["'; DROP TABLE patients; --"],
            "last_hba1c_value": "not_a_number"
        }
        
        # Should handle malicious input gracefully
        try:
            alerts = await cds_engine.evaluate_patient(malicious_patient_data)
            # Should return empty list or handle gracefully
            assert isinstance(alerts, list)
        except Exception:
            # Acceptable to throw validation exception
            pass

# Performance Tests

class TestClinicalDecisionSupportPerformance:
    """Performance tests for clinical decision support system"""
    
    @pytest.mark.asyncio
    async def test_large_population_performance(self, cds_engine, clinical_analytics):
        """Test performance with large patient populations"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Generate large patient population
        large_population = []
        for i in range(100):  # 100 patients
            patient = {
                "id": f"perf_patient_{i:03d}",
                "age": 30 + (i % 50),
                "diagnosis_codes": ["E11.9"] if i % 3 == 0 else ["I10"],
                "last_hba1c_value": 6.0 + (i % 5),
                "last_systolic_bp": 120 + (i % 40),
                "last_diastolic_bp": 70 + (i % 20),
                "medications_documented": i % 2 == 0
            }
            large_population.append(patient)
        
        # Measure performance of population analysis
        start_time = datetime.utcnow()
        
        # Calculate quality measures for large population
        cqm_results = await cds_engine.calculate_quality_measures(large_population)
        
        # Generate population health report
        population_report = await clinical_analytics.generate_population_health_report(large_population)
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (< 5 seconds for 100 patients)
        assert processing_time < 5.0
        
        # Verify results are comprehensive
        assert len(cqm_results) > 0
        assert population_report["population_size"] == 100
        assert len(population_report["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_patient_evaluation(self, cds_engine):
        """Test concurrent evaluation of multiple patients"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Create multiple patient evaluation tasks
        patients = []
        for i in range(10):
            patient = {
                "id": f"concurrent_patient_{i}",
                "age": 40 + i,
                "diagnosis_codes": ["E11.9", "I10"],
                "last_hba1c_value": 7.0 + i * 0.5,
                "last_systolic_bp": 130 + i * 2,
                "last_diastolic_bp": 80 + i,
                "medications": ["metformin", "lisinopril"]
            }
            patients.append(patient)
        
        # Execute concurrent evaluations
        start_time = datetime.utcnow()
        
        tasks = [cds_engine.evaluate_patient(patient) for patient in patients]
        results = await asyncio.gather(*tasks)
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Should complete quickly with concurrent processing
        assert processing_time < 2.0
        
        # Verify all evaluations completed
        assert len(results) == 10
        for result in results:
            assert isinstance(result, list)

# Error Handling and Edge Cases

class TestClinicalDecisionSupportErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_patient_data(self, cds_engine):
        """Test handling of empty patient data"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        empty_data = {}
        alerts = await cds_engine.evaluate_patient(empty_data)
        
        # Should handle gracefully
        assert isinstance(alerts, list)
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, cds_engine):
        """Test handling of missing required fields"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        incomplete_data = {
            "id": "incomplete_patient"
            # Missing age, diagnosis codes, vital signs
        }
        
        alerts = await cds_engine.evaluate_patient(incomplete_data)
        
        # Should handle gracefully without crashing
        assert isinstance(alerts, list)
    
    @pytest.mark.asyncio
    async def test_invalid_data_types(self, cds_engine):
        """Test handling of invalid data types"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        invalid_data = {
            "id": "invalid_patient",
            "age": "not_a_number",
            "last_hba1c_value": "invalid_hba1c",
            "last_systolic_bp": None,
            "diagnosis_codes": "not_a_list"
        }
        
        # Should handle invalid data gracefully
        alerts = await cds_engine.evaluate_patient(invalid_data)
        assert isinstance(alerts, list)
    
    @pytest.mark.asyncio
    async def test_nonexistent_alert_acknowledgment(self, cds_engine):
        """Test acknowledgment of nonexistent alert"""
        
        fake_alert_id = "nonexistent_alert_123"
        clinician_id = "dr_test"
        
        success = await cds_engine.acknowledge_alert(fake_alert_id, clinician_id)
        
        # Should return False for nonexistent alert
        assert success is False

# Clinical Validation Tests

class TestClinicalValidation:
    """Tests for clinical accuracy and evidence-based recommendations"""
    
    @pytest.mark.asyncio 
    async def test_diabetes_guidelines_compliance(self, cds_engine):
        """Test compliance with ADA diabetes management guidelines"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Patient with poor diabetes control
        diabetic_patient = {
            "id": "diabetes_validation",
            "age": 55,
            "diagnosis_codes": ["E11.9"],
            "last_hba1c_value": 9.5,  # Poor control per ADA guidelines
            "days_since_last_hba1c": 100
        }
        
        alerts = await cds_engine.evaluate_patient(diabetic_patient)
        
        # Should trigger evidence-based diabetes management alerts
        diabetes_alerts = [a for a in alerts if "diabetes" in a.title.lower() or "hba1c" in a.message.lower()]
        assert len(diabetes_alerts) > 0
        
        # Check that recommendations align with clinical guidelines
        for alert in diabetes_alerts:
            assert len(alert.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_hypertension_guidelines_compliance(self, cds_engine):
        """Test compliance with AHA/ACC hypertension guidelines"""
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Patient with stage 2 hypertension
        hypertensive_patient = {
            "id": "hypertension_validation",
            "age": 60,
            "diagnosis_codes": ["I10"],
            "last_systolic_bp": 165,  # Stage 2 HTN per AHA/ACC guidelines
            "last_diastolic_bp": 105
        }
        
        alerts = await cds_engine.evaluate_patient(hypertensive_patient)
        
        # Should trigger hypertension management alerts
        htn_alerts = [a for a in alerts if "hypertension" in a.title.lower() or "blood pressure" in a.message.lower()]
        assert len(htn_alerts) > 0
        
        # Should have high severity for stage 2 hypertension
        high_severity_alerts = [a for a in htn_alerts if a.severity in [ClinicalRiskLevel.HIGH, ClinicalRiskLevel.CRITICAL]]
        assert len(high_severity_alerts) > 0

if __name__ == "__main__":
    # Run the test suite
    pytest.main([__file__, "-v", "--tb=short"])