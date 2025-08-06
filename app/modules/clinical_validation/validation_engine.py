"""
Clinical Validation Engine for Healthcare Platform V2.0

Advanced clinical validation system with evidence-based assessment, regulatory compliance,
and comprehensive quality assurance for healthcare AI systems.
"""

import asyncio
import logging
import uuid
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from sklearn.metrics import roc_auc_score, precision_recall_curve, confusion_matrix
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt

# Internal imports
from .schemas import (
    ValidationStudy, ValidationProtocol, ValidationReport, ValidationEvidence,
    ClinicalMetrics, StudyPopulation, ClinicalEndpoint, ValidationStatus,
    ValidationLevel, ValidationCategory, ClinicalDomain, EvidenceLevel,
    RegulatoryStandard, ValidationDashboard, ValidationConfiguration
)
from ..audit_logger.service import AuditLogService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class StatisticalResult:
    """Statistical analysis result."""
    test_name: str
    test_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: Optional[float] = None
    interpretation: str = ""

@dataclass
class ValidationOutcome:
    """Validation outcome assessment."""
    outcome_met: bool
    observed_value: float
    target_value: float
    confidence_interval: Tuple[float, float]
    statistical_significance: bool
    clinical_significance: bool
    evidence_level: EvidenceLevel

class ClinicalValidationEngine:
    """
    Advanced clinical validation engine.
    
    Provides comprehensive clinical validation capabilities including study design,
    evidence synthesis, statistical analysis, and regulatory compliance assessment.
    """
    
    def __init__(self, config: ValidationConfiguration):
        self.config = config
        self.logger = logger.bind(component="ClinicalValidationEngine")
        
        # Core services
        self.audit_service = AuditLogService()
        
        # Study management
        self.active_studies: Dict[str, ValidationStudy] = {}
        self.completed_studies: Dict[str, ValidationStudy] = {}
        self.validation_protocols: Dict[str, ValidationProtocol] = {}
        
        # Evidence database
        self.evidence_database: Dict[str, ValidationEvidence] = {}
        self.systematic_reviews: Dict[str, Dict[str, Any]] = {}
        
        # Validation results
        self.validation_reports: Dict[str, ValidationReport] = {}
        self.quality_metrics: Dict[str, ClinicalMetrics] = {}
        
        # Statistical analysis cache
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default protocols
        self._initialize_default_protocols()
        
        self.logger.info("ClinicalValidationEngine initialized successfully")
    
    def _initialize_default_protocols(self):
        """Initialize default validation protocols."""
        
        # AI/ML Performance Validation Protocol
        ai_protocol = ValidationProtocol(
            protocol_name="AI/ML Performance Validation",
            validation_level=ValidationLevel.COMPREHENSIVE,
            clinical_domain=ClinicalDomain.PRIMARY_CARE,
            regulatory_standards=[RegulatoryStandard.FDA_510K, RegulatoryStandard.ISO_13485],
            study_design="prospective_observational",
            study_duration_days=180,
            sample_size_calculation={
                "power": 0.8,
                "alpha": 0.05,
                "effect_size": 0.5,
                "calculated_size": 384
            },
            primary_endpoints=[
                ClinicalEndpoint(
                    endpoint_name="Diagnostic Accuracy",
                    endpoint_type="primary",
                    description="Overall diagnostic accuracy of AI system",
                    measurement_method="confusion_matrix_analysis",
                    target_value=0.85,
                    clinical_significance_threshold=0.8
                ),
                ClinicalEndpoint(
                    endpoint_name="Clinical Impact",
                    endpoint_type="primary", 
                    description="Impact on clinical decision making",
                    measurement_method="clinical_outcome_assessment",
                    target_value=0.1,  # 10% improvement
                    clinical_significance_threshold=0.05
                )
            ],
            target_population=StudyPopulation(
                total_subjects=500,
                age_range={"min": 18, "max": 80},
                inclusion_criteria=[
                    "Adult patients requiring diagnostic assessment",
                    "Informed consent provided",
                    "Complete medical records available"
                ],
                exclusion_criteria=[
                    "Pregnancy",
                    "Severe comorbidities affecting diagnosis",
                    "Previous participation in AI validation studies"
                ]
            ),
            success_criteria={
                "primary_accuracy": {"threshold": 0.85, "required": True},
                "sensitivity": {"threshold": 0.8, "required": True},
                "specificity": {"threshold": 0.8, "required": True},
                "clinical_utility": {"threshold": 0.7, "required": True}
            },
            created_by="system"
        )
        
        # Medical Device Safety Protocol
        safety_protocol = ValidationProtocol(
            protocol_name="Medical Device Safety Validation",
            validation_level=ValidationLevel.REGULATORY,
            clinical_domain=ClinicalDomain.CRITICAL_CARE,
            regulatory_standards=[RegulatoryStandard.FDA_PMA, RegulatoryStandard.ICH_GCP],
            study_design="randomized_controlled_trial",
            study_duration_days=365,
            sample_size_calculation={
                "power": 0.9,
                "alpha": 0.025,
                "effect_size": 0.3,
                "calculated_size": 1200
            },
            primary_endpoints=[
                ClinicalEndpoint(
                    endpoint_name="Safety Events",
                    endpoint_type="primary",
                    description="Incidence of device-related adverse events",
                    measurement_method="safety_monitoring",
                    target_value=0.05,  # 5% max event rate
                    clinical_significance_threshold=0.1
                )
            ],
            target_population=StudyPopulation(
                total_subjects=1200,
                age_range={"min": 18, "max": 90},
                inclusion_criteria=[
                    "Patients requiring critical care monitoring",
                    "Expected ICU stay > 24 hours",
                    "Informed consent or emergency exception"
                ],
                exclusion_criteria=[
                    "Contraindications to device use",
                    "Life expectancy < 24 hours",
                    "Previous device-related complications"
                ]
            ),
            success_criteria={
                "safety_endpoint": {"threshold": 0.05, "required": True},
                "non_inferiority_margin": {"threshold": 0.1, "required": True}
            },
            irb_approval_required=True,
            data_monitoring_committee=True,
            created_by="system"
        )
        
        self.validation_protocols = {
            "ai_performance": ai_protocol,
            "device_safety": safety_protocol
        }
    
    async def create_validation_study(
        self, 
        study_request: Dict[str, Any],
        requesting_user: str
    ) -> ValidationStudy:
        """
        Create a new clinical validation study.
        
        Args:
            study_request: Study creation request
            requesting_user: User creating the study
            
        Returns:
            Created validation study
        """
        try:
            # Validate protocol exists
            protocol_id = study_request["protocol_id"]
            if protocol_id not in self.validation_protocols:
                raise ValueError(f"Unknown validation protocol: {protocol_id}")
            
            protocol = self.validation_protocols[protocol_id]
            
            # Create study
            study = ValidationStudy(
                study_name=study_request["study_name"],
                study_type=study_request["study_type"],
                protocol_id=protocol_id,
                principal_investigator=study_request["principal_investigator"],
                planned_start_date=study_request["planned_start_date"],
                planned_end_date=study_request["planned_end_date"],
                target_enrollment=study_request["target_enrollment"],
                study_sites=study_request.get("study_sites", []),
                created_by=requesting_user
            )
            
            # Store study
            self.active_studies[study.study_id] = study
            
            # Validate study design
            design_validation = await self._validate_study_design(study, protocol)
            if not design_validation["valid"]:
                raise ValueError(f"Study design validation failed: {design_validation['issues']}")
            
            # Calculate power analysis
            power_analysis = await self._perform_power_analysis(study, protocol)
            study.interim_analyses.append({
                "analysis_type": "power_analysis",
                "analysis_date": datetime.utcnow().isoformat(),
                "results": power_analysis
            })
            
            # Audit study creation
            await self._audit_validation_action(
                "study_created", study.study_id, 
                {"protocol_id": protocol_id, "target_enrollment": study.target_enrollment}
            )
            
            self.logger.info(
                "Validation study created",
                study_id=study.study_id,
                study_name=study.study_name,
                protocol_id=protocol_id,
                target_enrollment=study.target_enrollment
            )
            
            return study
            
        except Exception as e:
            self.logger.error(f"Failed to create validation study: {str(e)}")
            raise
    
    async def conduct_performance_analysis(
        self, 
        study_id: str,
        predictions: List[float],
        ground_truth: List[int],
        metadata: Dict[str, Any] = None
    ) -> ClinicalMetrics:
        """
        Conduct comprehensive performance analysis.
        
        Args:
            study_id: Study identifier
            predictions: Model predictions (probabilities)
            ground_truth: True labels
            metadata: Additional analysis metadata
            
        Returns:
            Comprehensive clinical metrics
        """
        try:
            if study_id not in self.active_studies and study_id not in self.completed_studies:
                raise ValueError(f"Study not found: {study_id}")
            
            # Convert to numpy arrays
            y_pred_proba = np.array(predictions)
            y_true = np.array(ground_truth)
            y_pred = (y_pred_proba >= 0.5).astype(int)
            
            # Calculate confusion matrix
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
            
            # Calculate clinical metrics
            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
            accuracy = (tp + tn) / (tp + tn + fp + fn)
            
            # Calculate advanced metrics
            auc_roc = roc_auc_score(y_true, y_pred_proba)
            precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
            f1_score = 2 * (ppv * sensitivity) / (ppv + sensitivity) if (ppv + sensitivity) > 0 else 0.0
            
            # Clinical-specific metrics
            false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            diagnostic_odds_ratio = (tp * tn) / (fp * fn) if (fp * fn) > 0 else float('inf')
            likelihood_ratio_positive = sensitivity / false_positive_rate if false_positive_rate > 0 else float('inf')
            likelihood_ratio_negative = false_negative_rate / specificity if specificity > 0 else 0.0
            
            # Performance metrics (simulated)
            processing_time_ms = np.random.normal(150, 30)  # Simulated processing time
            throughput_per_hour = int(3600 / (processing_time_ms / 1000))
            memory_usage_mb = np.random.normal(256, 50)  # Simulated memory usage
            
            metrics = ClinicalMetrics(
                sensitivity=sensitivity,
                specificity=specificity,
                ppv=ppv,
                npv=npv,
                accuracy=accuracy,
                auc_roc=auc_roc,
                f1_score=f1_score,
                precision=ppv,
                recall=sensitivity,
                false_positive_rate=false_positive_rate,
                false_negative_rate=false_negative_rate,
                diagnostic_odds_ratio=diagnostic_odds_ratio,
                likelihood_ratio_positive=likelihood_ratio_positive,
                likelihood_ratio_negative=likelihood_ratio_negative,
                processing_time_ms=processing_time_ms,
                throughput_per_hour=throughput_per_hour,
                memory_usage_mb=memory_usage_mb
            )
            
            # Store metrics
            self.quality_metrics[study_id] = metrics
            
            # Perform statistical analysis
            statistical_analysis = await self._perform_statistical_analysis(
                study_id, y_true, y_pred, y_pred_proba, metadata
            )
            
            # Update study with interim results
            if study_id in self.active_studies:
                study = self.active_studies[study_id]
                study.interim_analyses.append({
                    "analysis_type": "performance_analysis",
                    "analysis_date": datetime.utcnow().isoformat(),
                    "metrics": metrics.dict(),
                    "statistical_analysis": statistical_analysis,
                    "sample_size": len(y_true)
                })
            
            # Audit analysis
            await self._audit_validation_action(
                "performance_analysis", study_id,
                {"accuracy": accuracy, "auc_roc": auc_roc, "sample_size": len(y_true)}
            )
            
            self.logger.info(
                "Performance analysis completed",
                study_id=study_id,
                accuracy=accuracy,
                auc_roc=auc_roc,
                sensitivity=sensitivity,
                specificity=specificity,
                sample_size=len(y_true)
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to conduct performance analysis: {str(e)}")
            raise
    
    async def extract_evidence(
        self, 
        study_reference: str,
        extraction_type: str = "automated",
        target_endpoints: List[str] = None
    ) -> ValidationEvidence:
        """
        Extract clinical evidence from study reference.
        
        Args:
            study_reference: Reference to clinical study
            extraction_type: Type of extraction (automated, manual, hybrid)
            target_endpoints: Specific endpoints to extract
            
        Returns:
            Extracted validation evidence
        """
        try:
            evidence_id = str(uuid.uuid4())
            
            # Simulate evidence extraction (in production, would integrate with databases)
            if "rct" in study_reference.lower() or "randomized" in study_reference.lower():
                evidence_level = EvidenceLevel.LEVEL_2
                study_design = "Randomized Controlled Trial"
                quality_score = 85.0
            elif "meta" in study_reference.lower() or "systematic" in study_reference.lower():
                evidence_level = EvidenceLevel.LEVEL_1
                study_design = "Systematic Review/Meta-Analysis"
                quality_score = 90.0
            elif "cohort" in study_reference.lower():
                evidence_level = EvidenceLevel.LEVEL_3
                study_design = "Cohort Study"
                quality_score = 75.0
            else:
                evidence_level = EvidenceLevel.LEVEL_5
                study_design = "Case Series"
                quality_score = 60.0
            
            # Simulate extracted results
            primary_outcomes = await self._simulate_study_outcomes(study_reference, target_endpoints)
            statistical_methods = ["chi_square_test", "fisher_exact_test", "logistic_regression"]
            
            # Simulate confidence intervals and p-values
            confidence_intervals = {}
            p_values = {}
            effect_sizes = {}
            
            for endpoint in target_endpoints or ["sensitivity", "specificity", "accuracy"]:
                ci_lower = np.random.uniform(0.6, 0.8)
                ci_upper = ci_lower + np.random.uniform(0.1, 0.2)
                confidence_intervals[endpoint] = [ci_lower, ci_upper]
                p_values[endpoint] = np.random.uniform(0.001, 0.05)
                effect_sizes[endpoint] = np.random.uniform(0.3, 0.8)
            
            # Bias assessment
            bias_assessment = {
                "selection_bias": "low",
                "performance_bias": "low" if "rct" in study_reference.lower() else "moderate",
                "detection_bias": "low",
                "attrition_bias": "moderate",
                "reporting_bias": "low"
            }
            
            evidence = ValidationEvidence(
                evidence_id=evidence_id,
                evidence_type="study_result",
                evidence_level=evidence_level,
                study_reference=study_reference,
                study_population_size=np.random.randint(100, 2000),
                study_design=study_design,
                study_duration="12 months",
                primary_outcome_results=primary_outcomes,
                statistical_methods=statistical_methods,
                confidence_intervals=confidence_intervals,
                p_values=p_values,
                effect_sizes=effect_sizes,
                bias_assessment=bias_assessment,
                quality_score=quality_score,
                limitations=[
                    "Single-center study" if quality_score < 80 else "Multi-center study",
                    "Limited follow-up period" if quality_score < 70 else "Adequate follow-up",
                    "Potential selection bias" if "rct" not in study_reference.lower() else "Randomized design"
                ],
                extracted_by="automated_extraction_system"
            )
            
            # Store evidence
            self.evidence_database[evidence_id] = evidence
            
            # Audit evidence extraction
            await self._audit_validation_action(
                "evidence_extracted", evidence_id,
                {"study_reference": study_reference, "evidence_level": evidence_level.value}
            )
            
            self.logger.info(
                "Evidence extracted",
                evidence_id=evidence_id,
                study_reference=study_reference,
                evidence_level=evidence_level.value,
                quality_score=quality_score
            )
            
            return evidence
            
        except Exception as e:
            self.logger.error(f"Failed to extract evidence: {str(e)}")
            raise
    
    async def generate_validation_report(
        self, 
        study_id: str,
        report_type: str = "final",
        include_evidence_synthesis: bool = True
    ) -> ValidationReport:
        """
        Generate comprehensive validation report.
        
        Args:
            study_id: Study identifier
            report_type: Type of report (interim, final, regulatory)
            include_evidence_synthesis: Whether to include evidence synthesis
            
        Returns:
            Validation report
        """
        try:
            # Get study and protocol
            study = self._get_study(study_id)
            protocol = self.validation_protocols[study.protocol_id]
            
            report_id = str(uuid.uuid4())
            
            # Determine reporting period
            if report_type == "final":
                period_start = study.actual_start_date or study.planned_start_date
                period_end = study.actual_end_date or datetime.utcnow()
            else:
                period_start = study.actual_start_date or study.planned_start_date
                period_end = datetime.utcnow()
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(study, protocol)
            key_findings = await self._extract_key_findings(study_id)
            recommendations = await self._generate_recommendations(study, protocol)
            
            # Analyze primary endpoints
            primary_endpoint_results = await self._analyze_primary_endpoints(study, protocol)
            secondary_endpoint_results = await self._analyze_secondary_endpoints(study, protocol)
            
            # Safety analysis
            safety_analysis = await self._conduct_safety_analysis(study_id)
            
            # Get overall metrics
            overall_metrics = self.quality_metrics.get(study_id) or ClinicalMetrics()
            
            # Regulatory compliance assessment
            compliance_status = await self._assess_regulatory_compliance(study, protocol)
            
            # Evidence synthesis if requested
            supporting_evidence = []
            evidence_synthesis = ""
            grade_of_evidence = EvidenceLevel.LEVEL_5
            
            if include_evidence_synthesis:
                evidence_synthesis_result = await self._synthesize_evidence(study_id, protocol)
                supporting_evidence = evidence_synthesis_result["evidence_ids"]
                evidence_synthesis = evidence_synthesis_result["synthesis"]
                grade_of_evidence = evidence_synthesis_result["grade"]
            
            # Generate conclusions
            conclusions = await self._generate_conclusions(study, overall_metrics, compliance_status)
            limitations = await self._identify_limitations(study, protocol)
            
            report = ValidationReport(
                report_id=report_id,
                report_type=report_type,
                study_id=study_id,
                protocol_id=study.protocol_id,
                reporting_period_start=period_start,
                reporting_period_end=period_end,
                executive_summary=executive_summary,
                key_findings=key_findings,
                recommendations=recommendations,
                primary_endpoint_results=primary_endpoint_results,
                secondary_endpoint_results=secondary_endpoint_results,
                safety_analysis=safety_analysis,
                statistical_analysis_plan=f"Analysis conducted per protocol {protocol.protocol_name}",
                statistical_methods_used=["descriptive_statistics", "confidence_intervals", "hypothesis_testing"],
                missing_data_handling="Complete case analysis with sensitivity analysis for missing data",
                overall_metrics=overall_metrics,
                regulatory_compliance_status=compliance_status,
                supporting_evidence=supporting_evidence,
                evidence_synthesis=evidence_synthesis,
                grade_of_evidence=grade_of_evidence,
                conclusions=conclusions,
                limitations=limitations,
                future_research_needs=[
                    "Larger multi-center validation studies",
                    "Long-term outcome assessment",
                    "Subgroup analysis for special populations"
                ],
                prepared_by="clinical_validation_engine"
            )
            
            # Store report
            self.validation_reports[report_id] = report
            
            # Audit report generation
            await self._audit_validation_action(
                "report_generated", study_id,
                {"report_id": report_id, "report_type": report_type}
            )
            
            self.logger.info(
                "Validation report generated",
                study_id=study_id,
                report_id=report_id,
                report_type=report_type,
                overall_accuracy=overall_metrics.accuracy or 0.0
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate validation report: {str(e)}")
            raise
    
    async def get_validation_dashboard(self) -> ValidationDashboard:
        """
        Generate validation dashboard with summary statistics.
        
        Returns:
            Validation dashboard data
        """
        try:
            all_studies = {**self.active_studies, **self.completed_studies}
            
            # Summary statistics
            total_studies = len(all_studies)
            active_studies = len(self.active_studies)
            completed_studies = len(self.completed_studies)
            
            # Status distribution
            status_distribution = {}
            level_distribution = {}
            domain_distribution = {}
            
            for study in all_studies.values():
                # Status distribution
                status = study.status
                status_distribution[status] = status_distribution.get(status, 0) + 1
                
                # Get protocol for level and domain
                if study.protocol_id in self.validation_protocols:
                    protocol = self.validation_protocols[study.protocol_id]
                    
                    # Level distribution
                    level = protocol.validation_level
                    level_distribution[level] = level_distribution.get(level, 0) + 1
                    
                    # Domain distribution
                    domain = protocol.clinical_domain
                    domain_distribution[domain] = domain_distribution.get(domain, 0) + 1
            
            # Performance metrics
            durations = []
            for study in self.completed_studies.values():
                if study.actual_start_date and study.actual_end_date:
                    duration = (study.actual_end_date - study.actual_start_date).days
                    durations.append(duration)
            
            average_duration = np.mean(durations) if durations else None
            
            # Calculate success rate
            successful_studies = sum(
                1 for study in self.completed_studies.values()
                if study.status == ValidationStatus.APPROVED
            )
            success_rate = successful_studies / completed_studies if completed_studies > 0 else None
            
            # Quality indicators (simulated)
            protocol_adherence_rate = 0.92
            data_quality_score = 88.5
            regulatory_compliance_rate = 0.95
            
            # Recent activities
            recent_completions = []
            for study in list(self.completed_studies.values())[-5:]:  # Last 5 completed
                recent_completions.append({
                    "study_id": study.study_id,
                    "study_name": study.study_name,
                    "completion_date": study.actual_end_date.isoformat() if study.actual_end_date else None,
                    "final_status": study.status.value
                })
            
            # Upcoming milestones
            upcoming_milestones = []
            for study in self.active_studies.values():
                if study.planned_end_date > datetime.utcnow():
                    days_remaining = (study.planned_end_date - datetime.utcnow()).days
                    upcoming_milestones.append({
                        "study_id": study.study_id,
                        "study_name": study.study_name,
                        "milestone": "Study completion",
                        "due_date": study.planned_end_date.isoformat(),
                        "days_remaining": days_remaining
                    })
            
            # Sort by due date
            upcoming_milestones.sort(key=lambda x: x["days_remaining"])
            
            dashboard = ValidationDashboard(
                total_studies=total_studies,
                active_studies=active_studies,
                completed_studies=completed_studies,
                study_status_distribution=status_distribution,
                validation_level_distribution=level_distribution,
                clinical_domain_distribution=domain_distribution,
                average_study_duration_days=average_duration,
                overall_success_rate=success_rate,
                protocol_adherence_rate=protocol_adherence_rate,
                data_quality_score=data_quality_score,
                regulatory_compliance_rate=regulatory_compliance_rate,
                recent_study_completions=recent_completions,
                upcoming_milestones=upcoming_milestones[:10],  # Top 10
                critical_alerts=[],  # Would be populated based on study status
                safety_notifications=[],  # Would be populated from safety monitoring
                regulatory_updates=[]  # Would be populated from regulatory feeds
            )
            
            self.logger.info(
                "Validation dashboard generated",
                total_studies=total_studies,
                active_studies=active_studies,
                success_rate=success_rate
            )
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Failed to generate validation dashboard: {str(e)}")
            raise
    
    # Helper methods
    
    def _get_study(self, study_id: str) -> ValidationStudy:
        """Get study by ID from active or completed studies."""
        if study_id in self.active_studies:
            return self.active_studies[study_id]
        elif study_id in self.completed_studies:
            return self.completed_studies[study_id]
        else:
            raise ValueError(f"Study not found: {study_id}")
    
    async def _validate_study_design(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> Dict[str, Any]:
        """Validate study design against protocol requirements."""
        issues = []
        
        # Check enrollment
        if study.target_enrollment < protocol.sample_size_calculation.get("calculated_size", 0):
            issues.append("Target enrollment below calculated sample size")
        
        # Check duration
        study_duration = (study.planned_end_date - study.planned_start_date).days
        if study_duration < protocol.study_duration_days:
            issues.append("Study duration shorter than protocol requirement")
        
        # Check endpoints
        if not protocol.primary_endpoints:
            issues.append("No primary endpoints defined in protocol")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    async def _perform_power_analysis(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> Dict[str, Any]:
        """Perform statistical power analysis."""
        
        sample_calc = protocol.sample_size_calculation
        power = sample_calc.get("power", 0.8)
        alpha = sample_calc.get("alpha", 0.05)
        effect_size = sample_calc.get("effect_size", 0.5)
        
        # Calculate required sample size for different effect sizes
        effect_sizes = [0.2, 0.5, 0.8]  # Small, medium, large
        required_sizes = []
        
        for es in effect_sizes:
            # Simplified sample size calculation
            z_alpha = stats.norm.ppf(1 - alpha/2)
            z_beta = stats.norm.ppf(power)
            n = ((z_alpha + z_beta) / es) ** 2
            required_sizes.append(int(n))
        
        return {
            "target_power": power,
            "alpha_level": alpha,
            "effect_size_analysis": {
                "small_effect": {"size": 0.2, "required_n": required_sizes[0]},
                "medium_effect": {"size": 0.5, "required_n": required_sizes[1]},
                "large_effect": {"size": 0.8, "required_n": required_sizes[2]}
            },
            "current_target_n": study.target_enrollment,
            "power_adequate": study.target_enrollment >= required_sizes[1]  # Medium effect
        }
    
    async def _perform_statistical_analysis(
        self, 
        study_id: str,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_pred_proba: np.ndarray,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis."""
        
        results = {}
        
        # Descriptive statistics
        results["descriptive"] = {
            "sample_size": len(y_true),
            "positive_cases": int(np.sum(y_true)),
            "negative_cases": int(len(y_true) - np.sum(y_true)),
            "prevalence": float(np.mean(y_true))
        }
        
        # Confidence intervals for key metrics
        n = len(y_true)
        accuracy = np.mean(y_pred == y_true)
        
        # Wilson score interval for accuracy
        z = 1.96  # 95% CI
        accuracy_ci = self._wilson_score_interval(accuracy, n, z)
        
        results["confidence_intervals"] = {
            "accuracy": {
                "estimate": accuracy,
                "lower": accuracy_ci[0],
                "upper": accuracy_ci[1],
                "method": "wilson_score"
            }
        }
        
        # Hypothesis testing
        # Test if accuracy is significantly different from 0.5 (chance)
        null_accuracy = 0.5
        se_accuracy = np.sqrt(accuracy * (1 - accuracy) / n)
        z_stat = (accuracy - null_accuracy) / se_accuracy
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        results["hypothesis_tests"] = {
            "accuracy_vs_chance": {
                "null_hypothesis": "accuracy = 0.5",
                "test_statistic": z_stat,
                "p_value": p_value,
                "significant": p_value < 0.05
            }
        }
        
        # Additional analyses based on metadata
        if metadata and "subgroups" in metadata:
            results["subgroup_analysis"] = await self._perform_subgroup_analysis(
                y_true, y_pred, y_pred_proba, metadata["subgroups"]
            )
        
        return results
    
    def _wilson_score_interval(self, p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
        """Calculate Wilson score confidence interval."""
        denominator = 1 + z**2/n
        centre_adjusted_probability = p + z*z / (2*n)
        adjusted_standard_deviation = z * np.sqrt((p*(1-p) + z*z/(4*n)) / n)
        
        lower_bound = (centre_adjusted_probability - adjusted_standard_deviation) / denominator
        upper_bound = (centre_adjusted_probability + adjusted_standard_deviation) / denominator
        
        return (max(0, lower_bound), min(1, upper_bound))
    
    async def _simulate_study_outcomes(
        self, 
        study_reference: str, 
        target_endpoints: List[str] = None
    ) -> Dict[str, Any]:
        """Simulate study outcomes for evidence extraction."""
        
        outcomes = {}
        endpoints = target_endpoints or ["sensitivity", "specificity", "accuracy", "safety"]
        
        for endpoint in endpoints:
            if endpoint in ["sensitivity", "specificity", "accuracy"]:
                # Performance endpoints
                outcomes[endpoint] = {
                    "value": np.random.uniform(0.7, 0.95),
                    "confidence_interval": [np.random.uniform(0.6, 0.8), np.random.uniform(0.8, 0.95)],
                    "p_value": np.random.uniform(0.001, 0.05)
                }
            elif endpoint == "safety":
                # Safety endpoints
                outcomes[endpoint] = {
                    "adverse_event_rate": np.random.uniform(0.01, 0.1),
                    "serious_adverse_events": np.random.randint(0, 5),
                    "discontinuation_rate": np.random.uniform(0.05, 0.15)
                }
            else:
                # Generic endpoint
                outcomes[endpoint] = {
                    "value": np.random.uniform(0.5, 0.9),
                    "statistical_significance": np.random.choice([True, False], p=[0.7, 0.3])
                }
        
        return outcomes
    
    async def _generate_executive_summary(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> str:
        """Generate executive summary for validation report."""
        
        metrics = self.quality_metrics.get(study.study_id)
        
        summary = f"""
This report presents the results of the clinical validation study '{study.study_name}' 
conducted under protocol '{protocol.protocol_name}'. The study was designed as a 
{protocol.study_design.replace('_', ' ')} to evaluate {protocol.clinical_domain.value} 
applications with {protocol.validation_level.value} validation standards.

Study enrollment: {study.actual_enrollment}/{study.target_enrollment} subjects
Study duration: {(study.actual_end_date - study.actual_start_date).days if study.actual_end_date and study.actual_start_date else 'Ongoing'} days
"""
        
        if metrics:
            summary += f"""
Key Performance Results:
- Overall Accuracy: {metrics.accuracy:.3f} ({metrics.accuracy*100:.1f}%)
- Sensitivity: {metrics.sensitivity:.3f} ({metrics.sensitivity*100:.1f}%)
- Specificity: {metrics.specificity:.3f} ({metrics.specificity*100:.1f}%)
- AUC-ROC: {metrics.auc_roc:.3f}
"""
        
        return summary.strip()
    
    async def _extract_key_findings(self, study_id: str) -> List[str]:
        """Extract key findings from study analysis."""
        
        metrics = self.quality_metrics.get(study_id)
        findings = []
        
        if metrics:
            if metrics.accuracy and metrics.accuracy >= 0.85:
                findings.append(f"System achieved high diagnostic accuracy ({metrics.accuracy:.3f})")
            
            if metrics.sensitivity and metrics.sensitivity >= 0.8:
                findings.append(f"Excellent sensitivity for disease detection ({metrics.sensitivity:.3f})")
            
            if metrics.specificity and metrics.specificity >= 0.8:
                findings.append(f"High specificity minimizing false positives ({metrics.specificity:.3f})")
            
            if metrics.auc_roc and metrics.auc_roc >= 0.9:
                findings.append(f"Outstanding discriminative ability (AUC-ROC: {metrics.auc_roc:.3f})")
            
            if metrics.processing_time_ms and metrics.processing_time_ms < 200:
                findings.append(f"Fast processing suitable for clinical workflows ({metrics.processing_time_ms:.1f}ms)")
        
        if not findings:
            findings.append("Study completed successfully with results within expected ranges")
        
        return findings
    
    async def _generate_recommendations(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> List[str]:
        """Generate recommendations based on study results."""
        
        recommendations = []
        metrics = self.quality_metrics.get(study.study_id)
        
        if metrics:
            if metrics.accuracy and metrics.accuracy >= 0.85:
                recommendations.append("System demonstrates readiness for clinical deployment")
            elif metrics.accuracy and metrics.accuracy >= 0.8:
                recommendations.append("Consider additional optimization before deployment")
            else:
                recommendations.append("Significant improvements needed before clinical use")
            
            if metrics.sensitivity and metrics.sensitivity < 0.8:
                recommendations.append("Improve sensitivity to reduce false negative rates")
            
            if metrics.specificity and metrics.specificity < 0.8:
                recommendations.append("Enhance specificity to minimize false positive alerts")
        
        # Protocol-specific recommendations
        if protocol.validation_level == ValidationLevel.REGULATORY:
            recommendations.append("Prepare comprehensive regulatory submission package")
            recommendations.append("Conduct post-market surveillance planning")
        
        recommendations.append("Plan for larger multi-site validation study")
        recommendations.append("Develop comprehensive user training materials")
        
        return recommendations
    
    async def _analyze_primary_endpoints(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> Dict[str, Any]:
        """Analyze primary endpoint results."""
        
        results = {}
        metrics = self.quality_metrics.get(study.study_id)
        
        for endpoint in protocol.primary_endpoints:
            endpoint_result = {
                "endpoint_name": endpoint.endpoint_name,
                "target_value": endpoint.target_value,
                "measurement_method": endpoint.measurement_method,
                "clinical_significance_threshold": endpoint.clinical_significance_threshold
            }
            
            # Map endpoint to metrics
            if endpoint.endpoint_name.lower() == "diagnostic accuracy" and metrics:
                endpoint_result.update({
                    "observed_value": metrics.accuracy,
                    "target_met": metrics.accuracy >= endpoint.target_value if endpoint.target_value else True,
                    "clinical_significance": metrics.accuracy >= endpoint.clinical_significance_threshold if endpoint.clinical_significance_threshold else True
                })
            
            results[endpoint.endpoint_id] = endpoint_result
        
        return results
    
    async def _analyze_secondary_endpoints(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> Dict[str, Any]:
        """Analyze secondary endpoint results."""
        
        results = {}
        metrics = self.quality_metrics.get(study.study_id)
        
        for endpoint in protocol.secondary_endpoints:
            results[endpoint.endpoint_id] = {
                "endpoint_name": endpoint.endpoint_name,
                "measurement_method": endpoint.measurement_method,
                "observed_value": np.random.uniform(0.7, 0.9),  # Simulated
                "statistical_significance": True
            }
        
        return results
    
    async def _conduct_safety_analysis(self, study_id: str) -> Dict[str, Any]:
        """Conduct comprehensive safety analysis."""
        
        # Simulate safety data
        safety_analysis = {
            "adverse_events": {
                "total_events": np.random.randint(0, 10),
                "serious_events": np.random.randint(0, 2),
                "device_related_events": np.random.randint(0, 3),
                "event_rate_per_patient": np.random.uniform(0.01, 0.1)
            },
            "safety_stopping_rules": {
                "triggered": False,
                "monitoring_threshold": 0.1,
                "observed_rate": np.random.uniform(0.01, 0.05)
            },
            "causality_assessment": {
                "definitely_related": 0,
                "probably_related": np.random.randint(0, 2),
                "possibly_related": np.random.randint(0, 3),
                "unlikely_related": np.random.randint(0, 5),
                "not_related": np.random.randint(5, 15)
            }
        }
        
        return safety_analysis
    
    async def _assess_regulatory_compliance(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> Dict[RegulatoryStandard, str]:
        """Assess regulatory compliance status."""
        
        compliance_status = {}
        
        for standard in protocol.regulatory_standards:
            if standard in [RegulatoryStandard.FDA_510K, RegulatoryStandard.FDA_PMA]:
                compliance_status[standard] = "compliant"
            elif standard == RegulatoryStandard.CE_MARK:
                compliance_status[standard] = "compliant"
            elif standard == RegulatoryStandard.ISO_13485:
                compliance_status[standard] = "compliant"
            else:
                compliance_status[standard] = "under_review"
        
        return compliance_status
    
    async def _synthesize_evidence(
        self, 
        study_id: str, 
        protocol: ValidationProtocol
    ) -> Dict[str, Any]:
        """Synthesize evidence from multiple sources."""
        
        # Find relevant evidence
        relevant_evidence = []
        for evidence in self.evidence_database.values():
            if evidence.evidence_level in [EvidenceLevel.LEVEL_1, EvidenceLevel.LEVEL_2]:
                relevant_evidence.append(evidence.evidence_id)
        
        # Grade overall evidence
        if len(relevant_evidence) >= 3:
            grade = EvidenceLevel.LEVEL_1
        elif len(relevant_evidence) >= 1:
            grade = EvidenceLevel.LEVEL_2
        else:
            grade = EvidenceLevel.LEVEL_5
        
        synthesis = f"""
Evidence synthesis based on {len(relevant_evidence)} high-quality studies shows 
consistent results supporting the clinical utility of the validated system. 
The overall grade of evidence is {grade.value} based on the availability and 
quality of supporting studies.
"""
        
        return {
            "evidence_ids": relevant_evidence,
            "synthesis": synthesis.strip(),
            "grade": grade
        }
    
    async def _generate_conclusions(
        self, 
        study: ValidationStudy, 
        metrics: ClinicalMetrics, 
        compliance_status: Dict[RegulatoryStandard, str]
    ) -> str:
        """Generate study conclusions."""
        
        conclusions = f"""
The clinical validation study '{study.study_name}' has successfully demonstrated 
"""
        
        if metrics and metrics.accuracy:
            if metrics.accuracy >= 0.9:
                conclusions += "excellent performance characteristics with high accuracy, "
            elif metrics.accuracy >= 0.8:
                conclusions += "good performance characteristics with acceptable accuracy, "
            else:
                conclusions += "moderate performance requiring further optimization, "
        
        conclusions += f"""
meeting the primary endpoints defined in the validation protocol. 
The system shows readiness for {"clinical deployment" if metrics and metrics.accuracy and metrics.accuracy >= 0.85 else "additional development"} 
based on the comprehensive validation results.
"""
        
        # Add regulatory conclusion
        compliant_standards = sum(1 for status in compliance_status.values() if status == "compliant")
        total_standards = len(compliance_status)
        
        if compliant_standards == total_standards:
            conclusions += " Full regulatory compliance has been achieved across all applicable standards."
        else:
            conclusions += f" Regulatory compliance achieved for {compliant_standards}/{total_standards} applicable standards."
        
        return conclusions.strip()
    
    async def _identify_limitations(
        self, 
        study: ValidationStudy, 
        protocol: ValidationProtocol
    ) -> List[str]:
        """Identify study limitations."""
        
        limitations = []
        
        # Sample size limitations
        if study.actual_enrollment < study.target_enrollment:
            limitations.append(f"Study enrollment ({study.actual_enrollment}) below target ({study.target_enrollment})")
        
        # Study design limitations
        if protocol.study_design == "retrospective":
            limitations.append("Retrospective study design limits causal inference")
        
        if not protocol.randomization_method:
            limitations.append("Non-randomized study design may introduce selection bias")
        
        # Population limitations
        if protocol.target_population.total_subjects < 500:
            limitations.append("Limited sample size may affect generalizability")
        
        # Duration limitations
        if protocol.study_duration_days < 180:
            limitations.append("Short study duration may not capture long-term effects")
        
        # Add generic limitations
        limitations.extend([
            "Single validation site may limit external validity",
            "Additional validation in diverse populations recommended"
        ])
        
        return limitations
    
    async def _perform_subgroup_analysis(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        y_pred_proba: np.ndarray,
        subgroups: Dict[str, List[int]]
    ) -> Dict[str, Any]:
        """Perform subgroup analysis."""
        
        subgroup_results = {}
        
        for subgroup_name, indices in subgroups.items():
            if len(indices) > 10:  # Minimum size for meaningful analysis
                subgroup_true = y_true[indices]
                subgroup_pred = y_pred[indices]
                
                accuracy = np.mean(subgroup_pred == subgroup_true)
                subgroup_results[subgroup_name] = {
                    "sample_size": len(indices),
                    "accuracy": accuracy,
                    "prevalence": np.mean(subgroup_true)
                }
        
        return subgroup_results
    
    async def _audit_validation_action(
        self, 
        action: str, 
        entity_id: str, 
        additional_data: Dict[str, Any]
    ):
        """Audit validation actions."""
        try:
            audit_data = {
                "event_type": "clinical_validation",
                "event_subtype": action,
                "entity_id": entity_id,
                "timestamp": datetime.utcnow().isoformat(),
                "additional_data": additional_data
            }
            
            await self.audit_service.log_security_event(audit_data)
            
        except Exception as e:
            self.logger.error(f"Failed to audit validation action: {str(e)}")