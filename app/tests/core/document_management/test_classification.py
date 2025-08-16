"""
Tests for Document Classification System

Tests rule-based, ML-based, and ensemble classification approaches.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

# Test the classification system
from app.core.database_unified import DocumentType
from app.modules.document_management.classification.classifier import (
    DocumentClassifier, ClassificationResult, RuleBasedClassifier,
    get_document_classifier
)
from app.modules.document_management.classification.ml_classifier import (
    MLClassifier, SimpleNaiveBayesClassifier, get_ml_classifier
)


class TestRuleBasedClassifier:
    """Test rule-based document classifier."""
    
    @pytest.fixture
    def rule_classifier(self):
        """Create rule-based classifier."""
        return RuleBasedClassifier()
    
    @pytest.mark.asyncio
    async def test_classify_lab_result(self, rule_classifier):
        """Test classification of lab result document."""
        text = """
        Laboratory Report
        
        Patient: John Doe
        Test: Complete Blood Count (CBC)
        
        Results:
        Hemoglobin: 14.2 g/dL (Reference Range: 13.5-17.5)
        White Blood Cell Count: 6,800/uL (Reference Range: 4,500-11,000)
        Platelet Count: 250,000/uL (Reference Range: 150,000-450,000)
        
        All values within normal range.
        """
        
        result = await rule_classifier.classify_document(
            text=text,
            filename="cbc_results.pdf",
            mime_type="application/pdf"
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.success is True
        assert result.document_type == DocumentType.LAB_RESULT
        assert result.confidence > 0.8
        assert result.classification_method == "rule_based"
        assert "blood_work" in result.category or "laboratory" in result.category
    
    @pytest.mark.asyncio
    async def test_classify_imaging_report(self, rule_classifier):
        """Test classification of imaging report."""
        text = """
        RADIOLOGY REPORT
        
        Study: CT Chest without contrast
        
        Clinical History: Shortness of breath
        
        Technique: Axial CT images of the chest were obtained without contrast.
        
        Findings:
        - Lungs are clear bilaterally
        - No pleural effusion
        - Heart size is normal
        
        Impression: Normal CT chest examination
        """
        
        result = await rule_classifier.classify_document(
            text=text,
            filename="ct_chest_report.pdf",
            mime_type="application/pdf"
        )
        
        assert result.success is True
        assert result.document_type == DocumentType.IMAGING
        assert result.confidence > 0.7
        assert "ct" in result.tags or "ct_scan" in result.category
    
    @pytest.mark.asyncio
    async def test_classify_clinical_note(self, rule_classifier):
        """Test classification of clinical note."""
        text = """
        PROGRESS NOTE
        
        Patient: Jane Smith
        Date: 2024-01-15
        
        Chief Complaint: Follow-up for hypertension
        
        History of Present Illness:
        Patient returns for routine follow-up of hypertension. Reports good compliance with medications.
        
        Physical Examination:
        Vital Signs: BP 130/80, HR 72, Temp 98.6°F
        General: Well-appearing
        
        Assessment and Plan:
        1. Hypertension - continue current medications
        2. Return in 3 months
        """
        
        result = await rule_classifier.classify_document(
            text=text,
            filename="progress_note.pdf",
            mime_type="application/pdf"
        )
        
        assert result.success is True
        assert result.document_type == DocumentType.CLINICAL_NOTE
        assert result.confidence > 0.7
        assert "progress_note" in result.category or "clinical" in result.category
    
    @pytest.mark.asyncio
    async def test_classify_prescription(self, rule_classifier):
        """Test classification of prescription."""
        text = """
        PRESCRIPTION
        
        Patient: Robert Johnson
        DOB: 01/01/1970
        
        Rx: Lisinopril 10mg tablets
        Quantity: 90 tablets
        Directions: Take 1 tablet daily
        Refills: 5
        
        Prescriber: Dr. Smith
        DEA #: AS1234567
        """
        
        result = await rule_classifier.classify_document(
            text=text,
            filename="prescription_lisinopril.pdf",
            mime_type="application/pdf"
        )
        
        assert result.success is True
        assert result.document_type == DocumentType.PRESCRIPTION
        assert result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_classify_unknown_document(self, rule_classifier):
        """Test classification of unknown document type."""
        text = """
        This is a generic document with no specific medical content.
        It contains general information that doesn't match any specific
        medical document type patterns.
        """
        
        result = await rule_classifier.classify_document(
            text=text,
            filename="generic_document.txt",
            mime_type="text/plain"
        )
        
        assert result.success is True
        assert result.document_type == DocumentType.OTHER
        assert result.category == "unknown"
    
    def test_confidence_threshold(self, rule_classifier):
        """Test confidence threshold setting."""
        threshold = rule_classifier.get_confidence_threshold()
        assert isinstance(threshold, float)
        assert 0.0 <= threshold <= 1.0


class TestMLClassifier:
    """Test ML-based document classifier."""
    
    @pytest.fixture
    def ml_classifier(self):
        """Create ML classifier."""
        return MLClassifier()
    
    @pytest.fixture
    def simple_nb_classifier(self):
        """Create simple Naive Bayes classifier."""
        return SimpleNaiveBayesClassifier()
    
    def test_simple_nb_initialization(self, simple_nb_classifier):
        """Test simple Naive Bayes classifier initialization."""
        assert simple_nb_classifier.trained is True
        assert len(simple_nb_classifier.vocabulary) > 0
        assert len(simple_nb_classifier.class_counts) > 0
        assert DocumentType.LAB_RESULT in simple_nb_classifier.class_counts
    
    def test_feature_extraction(self, simple_nb_classifier):
        """Test feature extraction from text."""
        text = "This is a laboratory test result with blood work analysis."
        features = simple_nb_classifier._extract_features(text)
        
        assert isinstance(features, dict)
        # Should extract medical terms
        medical_terms = ["laboratory", "test", "result", "blood", "analysis"]
        for term in medical_terms:
            if term in simple_nb_classifier.vocabulary:
                assert term in features or term not in text.lower()
    
    def test_simple_nb_prediction(self, simple_nb_classifier):
        """Test simple Naive Bayes prediction."""
        lab_text = "Laboratory blood test results with hemoglobin and glucose levels reference range normal"
        
        predicted_type, confidence, feature_scores = simple_nb_classifier.predict(lab_text)
        
        assert isinstance(predicted_type, DocumentType)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert isinstance(feature_scores, dict)
        
        # Should predict lab result with reasonable confidence
        if predicted_type == DocumentType.LAB_RESULT:
            assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_ml_classify_lab_result(self, ml_classifier):
        """Test ML classification of lab result."""
        text = """
        Blood Chemistry Panel
        Glucose: 95 mg/dL (normal range 70-100)
        Hemoglobin: 14.5 g/dL (normal range 13.5-17.5)
        Cholesterol: 180 mg/dL (normal range <200)
        """
        
        result = await ml_classifier.classify_document(
            text=text,
            filename="blood_chemistry.pdf",
            mime_type="application/pdf"
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.success is True
        assert result.classification_method == "ml_based"
        assert result.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_ml_classify_imaging(self, ml_classifier):
        """Test ML classification of imaging report."""
        text = """
        MRI Brain Report
        Technique: Axial and sagittal images obtained
        Findings: No acute intracranial abnormality
        Impression: Normal MRI brain study
        """
        
        result = await ml_classifier.classify_document(
            text=text,
            filename="mri_brain.pdf",
            mime_type="application/pdf"
        )
        
        assert result.success is True
        assert result.classification_method == "ml_based"
    
    def test_ml_confidence_threshold(self, ml_classifier):
        """Test ML classifier confidence threshold."""
        threshold = ml_classifier.get_confidence_threshold()
        assert isinstance(threshold, float)
        assert threshold >= 0.0


class TestDocumentClassifier:
    """Test main document classifier orchestration."""
    
    @pytest.fixture
    def mock_rule_classifier(self):
        """Mock rule-based classifier."""
        classifier = Mock()
        classifier.classify_document = AsyncMock(return_value=ClassificationResult(
            document_type=DocumentType.LAB_RESULT,
            confidence=0.85,
            category="laboratory",
            subcategory=None,
            tags=["blood_work"],
            metadata={"engine": "rule_based"},
            classification_method="rule_based",
            processing_time_ms=100,
            success=True
        ))
        classifier.get_confidence_threshold = Mock(return_value=0.6)
        return classifier
    
    @pytest.fixture
    def mock_ml_classifier(self):
        """Mock ML classifier."""
        classifier = Mock()
        classifier.classify_document = AsyncMock(return_value=ClassificationResult(
            document_type=DocumentType.LAB_RESULT,
            confidence=0.75,
            category="laboratory",
            subcategory=None,
            tags=["ml_classified"],
            metadata={"engine": "ml_based"},
            classification_method="ml_based",
            processing_time_ms=150,
            success=True
        ))
        classifier.get_confidence_threshold = Mock(return_value=0.5)
        return classifier
    
    @pytest.fixture
    def document_classifier(self, mock_rule_classifier, mock_ml_classifier):
        """Create document classifier with mocked engines."""
        return DocumentClassifier([mock_rule_classifier, mock_ml_classifier])
    
    @pytest.mark.asyncio
    async def test_single_engine_classification(self):
        """Test classification with single engine."""
        rule_classifier = RuleBasedClassifier()
        classifier = DocumentClassifier([rule_classifier])
        
        text = "Laboratory test results with blood work and reference ranges"
        
        result = await classifier.classify_document(
            text=text,
            filename="lab_test.pdf",
            mime_type="application/pdf"
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_ensemble_classification(self, document_classifier):
        """Test ensemble classification with multiple engines."""
        text = "Test document for ensemble classification"
        
        result = await document_classifier.classify_document(
            text=text,
            filename="test.pdf",
            mime_type="application/pdf"
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.success is True
        assert "ensemble_classification" in result.metadata
        assert result.metadata["engines_used"] == 2
    
    @pytest.mark.asyncio
    async def test_batch_classification(self, document_classifier):
        """Test batch classification of multiple documents."""
        documents = [
            ("Lab test results with blood work", "lab1.pdf", "application/pdf"),
            ("CT scan imaging report", "imaging1.pdf", "application/pdf"),
            ("Clinical progress note", "note1.pdf", "application/pdf")
        ]
        
        results = await document_classifier.batch_classify(documents)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, ClassificationResult)
    
    @pytest.mark.asyncio
    async def test_classification_error_handling(self, document_classifier):
        """Test error handling in classification."""
        # Mock engines to raise exceptions
        for engine in document_classifier.engines:
            engine.classify_document = AsyncMock(side_effect=Exception("Engine failed"))
        
        result = await document_classifier.classify_document(
            text="test",
            filename="test.txt",
            mime_type="text/plain"
        )
        
        assert isinstance(result, ClassificationResult)
        # Should return fallback result
        assert result.document_type == DocumentType.OTHER
    
    @pytest.mark.asyncio
    async def test_health_check(self, document_classifier):
        """Test classifier health check."""
        health = await document_classifier.health_check()
        
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "engines_count" in health
        assert health["engines_count"] == 2
    
    def test_supported_document_types(self, document_classifier):
        """Test getting supported document types."""
        types = document_classifier.get_supported_document_types()
        
        assert isinstance(types, list)
        assert len(types) > 0
        assert DocumentType.LAB_RESULT in types
        assert DocumentType.IMAGING in types


class TestIntegration:
    """Integration tests for classification system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_classification(self):
        """Test complete classification pipeline."""
        classifier = get_document_classifier()
        
        # Test with real medical text
        lab_text = """
        Complete Blood Count (CBC)
        Patient: Test Patient
        
        White Blood Cells: 7,500/µL (Normal: 4,500-11,000)
        Red Blood Cells: 4.8 million/µL (Normal: 4.2-5.4)
        Hemoglobin: 15.2 g/dL (Normal: 13.5-17.5)
        Hematocrit: 45% (Normal: 38-48)
        Platelets: 300,000/µL (Normal: 150,000-450,000)
        
        Interpretation: All values within normal limits.
        """
        
        result = await classifier.classify_document(
            text=lab_text,
            filename="cbc_report.pdf",
            mime_type="application/pdf"
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.success is True
        assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_classification_with_ml_fallback(self):
        """Test classification with ML fallback."""
        ml_classifier = get_ml_classifier()
        classifier = DocumentClassifier([ml_classifier])
        
        text = "Radiology report with CT scan findings and imaging results"
        
        result = await classifier.classify_document(
            text=text,
            filename="radiology.pdf",
            mime_type="application/pdf"
        )
        
        assert result.success is True
        assert result.classification_method == "ml_based"
    
    def test_factory_functions(self):
        """Test factory functions create proper instances."""
        classifier = get_document_classifier()
        assert isinstance(classifier, DocumentClassifier)
        
        ml_classifier = get_ml_classifier()
        assert isinstance(ml_classifier, MLClassifier)


if __name__ == "__main__":
    # Run specific tests for debugging
    pytest.main([__file__, "-v", "-s"])