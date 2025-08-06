"""
Consensus Engine for A2A Healthcare Platform V2.0

Advanced consensus mechanisms for medical agent collaboration with quality metrics,
safety validation, and clinical decision support. All consensus methods are
designed for healthcare compliance and audit requirements.
"""

import asyncio
import numpy as np
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from statistics import mean, stdev
from collections import defaultdict, Counter
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

# Import existing healthcare platform components
from app.core.database_unified import get_db, AuditEventType
from app.modules.audit_logger.service import audit_logger
from app.core.config import get_settings

# Import A2A schemas
from .schemas import (
    ConsensusType, ConsensusResult, AgentRecommendation, 
    CollaborationResponse, DifferentialDiagnosis, TreatmentRecommendation,
    MedicalSpecialty, ClinicalEvidence
)
from .models import A2AConsensusRecord

logger = structlog.get_logger()
settings = get_settings()

class ConsensusEngine:
    """
    Advanced consensus engine for medical agent collaboration.
    
    Implements multiple consensus mechanisms optimized for healthcare decision-making
    with emphasis on patient safety, clinical accuracy, and regulatory compliance.
    """
    
    def __init__(self):
        self.processing_start_time = None
        
        # Algorithm weights for different consensus types
        self.specialty_expertise_weights = {
            MedicalSpecialty.EMERGENCY_MEDICINE: 1.2,  # Higher weight for emergency cases
            MedicalSpecialty.CARDIOLOGY: 1.1,
            MedicalSpecialty.NEUROLOGY: 1.1,
            MedicalSpecialty.INTERNAL_MEDICINE: 1.0,
            # Add more specialty weights as needed
        }
        
        # Safety thresholds
        self.MINIMUM_CONFIDENCE_THRESHOLD = 0.3
        self.CONSENSUS_AGREEMENT_THRESHOLD = 0.6
        self.SAFETY_REVIEW_THRESHOLD = 0.5
        
    async def analyze_consensus(self, 
                              collaboration_id: str,
                              responses: List[CollaborationResponse],
                              consensus_type: ConsensusType = ConsensusType.WEIGHTED_EXPERTISE) -> ConsensusResult:
        """
        Analyze agent responses and generate consensus recommendation.
        
        Args:
            collaboration_id: Collaboration session ID
            responses: List of agent responses
            consensus_type: Type of consensus mechanism to use
            
        Returns:
            ConsensusResult: Comprehensive consensus analysis
        """
        self.processing_start_time = datetime.utcnow()
        
        try:
            logger.info("Starting consensus analysis",
                       collaboration_id=collaboration_id,
                       response_count=len(responses),
                       consensus_type=consensus_type.value)
            
            # Validate responses
            validated_responses = await self._validate_responses(responses)
            
            if len(validated_responses) < 2:
                raise ValueError("At least 2 valid responses required for consensus")
            
            # Apply consensus mechanism
            consensus_result = await self._apply_consensus_mechanism(
                collaboration_id, validated_responses, consensus_type
            )
            
            # Perform safety validation
            safety_validation = await self._validate_consensus_safety(consensus_result)
            consensus_result = await self._apply_safety_validation(consensus_result, safety_validation)
            
            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(validated_responses, consensus_result)
            consensus_result = await self._enhance_with_quality_metrics(consensus_result, quality_metrics)
            
            # Store consensus record
            await self._store_consensus_record(consensus_result)
            
            # Log consensus completion
            processing_time = (datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
            
            await audit_logger.log_event(
                event_type=AuditEventType.CONSENSUS_COMPLETED,
                user_id="consensus_engine",
                resource_type="collaboration_consensus",
                resource_id=collaboration_id,
                action="consensus_analysis_completed",
                details={
                    "consensus_type": consensus_type.value,
                    "participating_agents": len(validated_responses),
                    "consensus_reached": consensus_result.consensus_reached,
                    "agreement_level": consensus_result.agreement_level,
                    "processing_time_ms": processing_time,
                    "safety_review_required": consensus_result.requires_human_review
                }
            )
            
            logger.info("Consensus analysis completed",
                       collaboration_id=collaboration_id,
                       consensus_reached=consensus_result.consensus_reached,
                       agreement_level=consensus_result.agreement_level,
                       processing_time_ms=processing_time)
            
            return consensus_result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - self.processing_start_time).total_seconds() * 1000 if self.processing_start_time else 0
            
            logger.error("Consensus analysis failed",
                        collaboration_id=collaboration_id,
                        error=str(e),
                        processing_time_ms=processing_time)
            
            await audit_logger.log_event(
                event_type=AuditEventType.CONSENSUS_FAILED,
                user_id="consensus_engine",
                resource_type="collaboration_consensus",
                resource_id=collaboration_id,
                action="consensus_analysis_failed",
                details={"error": str(e), "processing_time_ms": processing_time}
            )
            
            raise
    
    async def _validate_responses(self, responses: List[CollaborationResponse]) -> List[CollaborationResponse]:
        """Validate agent responses for consensus analysis."""
        validated_responses = []
        
        for response in responses:
            # Check minimum confidence threshold
            if response.recommendation.overall_confidence < self.MINIMUM_CONFIDENCE_THRESHOLD:
                logger.warning("Response excluded due to low confidence",
                             agent_id=response.responding_agent,
                             confidence=response.recommendation.overall_confidence)
                continue
            
            # Check for required fields
            if not response.recommendation.primary_assessment:
                logger.warning("Response excluded due to missing assessment",
                             agent_id=response.responding_agent)
                continue
            
            # Check response timing (exclude very slow responses as potentially problematic)
            if response.processing_time_ms > 300000:  # 5 minutes
                logger.warning("Response excluded due to excessive processing time",
                             agent_id=response.responding_agent,
                             processing_time_ms=response.processing_time_ms)
                continue
            
            validated_responses.append(response)
        
        logger.info(f"Validated {len(validated_responses)} of {len(responses)} responses for consensus")
        return validated_responses
    
    async def _apply_consensus_mechanism(self, 
                                       collaboration_id: str,
                                       responses: List[CollaborationResponse],
                                       consensus_type: ConsensusType) -> ConsensusResult:
        """Apply the specified consensus mechanism."""
        
        if consensus_type == ConsensusType.SIMPLE_MAJORITY:
            return await self._simple_majority_consensus(collaboration_id, responses)
        elif consensus_type == ConsensusType.WEIGHTED_EXPERTISE:
            return await self._weighted_expertise_consensus(collaboration_id, responses)
        elif consensus_type == ConsensusType.UNANIMOUS:
            return await self._unanimous_consensus(collaboration_id, responses)
        elif consensus_type == ConsensusType.BAYESIAN_ENSEMBLE:
            return await self._bayesian_ensemble_consensus(collaboration_id, responses)
        elif consensus_type == ConsensusType.CONFIDENCE_WEIGHTED:
            return await self._confidence_weighted_consensus(collaboration_id, responses)
        elif consensus_type == ConsensusType.SPECIALIST_PRIORITY:
            return await self._specialist_priority_consensus(collaboration_id, responses)
        else:
            raise ValueError(f"Unknown consensus type: {consensus_type}")
    
    async def _weighted_expertise_consensus(self, 
                                          collaboration_id: str,
                                          responses: List[CollaborationResponse]) -> ConsensusResult:
        """Apply expertise-weighted consensus mechanism."""
        
        # Calculate expertise weights for each agent
        agent_weights = {}
        for response in responses:
            specialty = response.recommendation.specialty
            base_weight = self.specialty_expertise_weights.get(specialty, 1.0)
            
            # Adjust weight based on agent's historical performance if available
            confidence_adjustment = response.recommendation.specialist_confidence
            agent_weights[response.responding_agent] = base_weight * confidence_adjustment
        
        # Normalize weights
        total_weight = sum(agent_weights.values())
        for agent_id in agent_weights:
            agent_weights[agent_id] /= total_weight
        
        # Aggregate diagnoses with weights
        diagnosis_scores = defaultdict(float)
        treatment_scores = defaultdict(float)
        
        for response in responses:
            agent_weight = agent_weights[response.responding_agent]
            
            # Weight differential diagnoses
            for diagnosis in response.recommendation.differential_diagnoses:
                diagnosis_scores[diagnosis.condition] += diagnosis.probability * agent_weight
            
            # Weight treatment recommendations
            for treatment in response.recommendation.treatment_recommendations:
                treatment_scores[treatment.intervention] += agent_weight
        
        # Calculate weighted average confidence
        weighted_confidence = sum(
            response.recommendation.overall_confidence * agent_weights[response.responding_agent]
            for response in responses
        )
        
        # Determine consensus threshold achievement
        max_diagnosis_score = max(diagnosis_scores.values()) if diagnosis_scores else 0
        consensus_reached = max_diagnosis_score >= self.CONSENSUS_AGREEMENT_THRESHOLD
        
        # Build consensus recommendation if achieved
        consensus_recommendation = None
        if consensus_reached:
            consensus_recommendation = await self._build_consensus_recommendation(
                responses, diagnosis_scores, treatment_scores, agent_weights
            )
        
        # Identify minority opinions (significantly different from consensus)
        minority_opinions = await self._identify_minority_opinions(responses, diagnosis_scores)
        
        consensus_result = ConsensusResult(
            collaboration_id=collaboration_id,
            consensus_type=ConsensusType.WEIGHTED_EXPERTISE,
            consensus_reached=consensus_reached,
            agreement_level=max_diagnosis_score,
            participating_agents=[r.responding_agent for r in responses],
            consensus_recommendation=consensus_recommendation,
            minority_opinions=minority_opinions,
            average_confidence=mean(r.recommendation.overall_confidence for r in responses),
            confidence_standard_deviation=stdev(r.recommendation.overall_confidence for r in responses) if len(responses) > 1 else 0.0,
            weighted_confidence=weighted_confidence,
            diagnostic_consensus=dict(diagnosis_scores),
            treatment_consensus=dict(treatment_scores),
            specialty_weights=agent_weights,
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
        )
        
        return consensus_result
    
    async def _simple_majority_consensus(self, 
                                       collaboration_id: str,
                                       responses: List[CollaborationResponse]) -> ConsensusResult:
        """Apply simple majority consensus mechanism."""
        
        # Count occurrences of each diagnosis
        diagnosis_votes = Counter()
        treatment_votes = Counter()
        
        for response in responses:
            # Vote for most probable diagnosis
            if response.recommendation.differential_diagnoses:
                top_diagnosis = max(
                    response.recommendation.differential_diagnoses,
                    key=lambda dx: dx.probability
                )
                diagnosis_votes[top_diagnosis.condition] += 1
            
            # Vote for all treatment recommendations
            for treatment in response.recommendation.treatment_recommendations:
                treatment_votes[treatment.intervention] += 1
        
        # Determine majority
        total_responses = len(responses)
        majority_threshold = total_responses / 2
        
        consensus_diagnosis = None
        max_votes = 0
        if diagnosis_votes:
            most_common = diagnosis_votes.most_common(1)[0]
            if most_common[1] > majority_threshold:
                consensus_diagnosis = most_common[0]
                max_votes = most_common[1]
        
        consensus_reached = max_votes > majority_threshold
        agreement_level = max_votes / total_responses if total_responses > 0 else 0
        
        consensus_result = ConsensusResult(
            collaboration_id=collaboration_id,
            consensus_type=ConsensusType.SIMPLE_MAJORITY,
            consensus_reached=consensus_reached,
            agreement_level=agreement_level,
            participating_agents=[r.responding_agent for r in responses],
            average_confidence=mean(r.recommendation.overall_confidence for r in responses),
            confidence_standard_deviation=stdev(r.recommendation.overall_confidence for r in responses) if len(responses) > 1 else 0.0,
            weighted_confidence=mean(r.recommendation.overall_confidence for r in responses),
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
        )
        
        return consensus_result
    
    async def _confidence_weighted_consensus(self, 
                                           collaboration_id: str,
                                           responses: List[CollaborationResponse]) -> ConsensusResult:
        """Apply confidence-weighted consensus mechanism."""
        
        # Weight each response by its confidence score
        total_confidence = sum(r.recommendation.overall_confidence for r in responses)
        
        diagnosis_weighted_scores = defaultdict(float)
        treatment_weighted_scores = defaultdict(float)
        
        for response in responses:
            confidence_weight = response.recommendation.overall_confidence / total_confidence
            
            for diagnosis in response.recommendation.differential_diagnoses:
                diagnosis_weighted_scores[diagnosis.condition] += diagnosis.probability * confidence_weight
            
            for treatment in response.recommendation.treatment_recommendations:
                treatment_weighted_scores[treatment.intervention] += confidence_weight
        
        # Find highest weighted diagnosis
        max_diagnosis_score = max(diagnosis_weighted_scores.values()) if diagnosis_weighted_scores else 0
        consensus_reached = max_diagnosis_score >= self.CONSENSUS_AGREEMENT_THRESHOLD
        
        consensus_result = ConsensusResult(
            collaboration_id=collaboration_id,
            consensus_type=ConsensusType.CONFIDENCE_WEIGHTED,
            consensus_reached=consensus_reached,
            agreement_level=max_diagnosis_score,
            participating_agents=[r.responding_agent for r in responses],
            average_confidence=mean(r.recommendation.overall_confidence for r in responses),
            confidence_standard_deviation=stdev(r.recommendation.overall_confidence for r in responses) if len(responses) > 1 else 0.0,
            weighted_confidence=max_diagnosis_score,
            diagnostic_consensus=dict(diagnosis_weighted_scores),
            treatment_consensus=dict(treatment_weighted_scores),
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
        )
        
        return consensus_result
    
    async def _unanimous_consensus(self, 
                                 collaboration_id: str,
                                 responses: List[CollaborationResponse]) -> ConsensusResult:
        """Apply unanimous consensus mechanism (requires all agents to agree)."""
        
        # Check if all responses have similar primary diagnoses
        primary_diagnoses = []
        for response in responses:
            if response.recommendation.differential_diagnoses:
                top_diagnosis = max(
                    response.recommendation.differential_diagnoses,
                    key=lambda dx: dx.probability
                )
                primary_diagnoses.append(top_diagnosis.condition.lower())
        
        # Check for unanimous agreement
        unique_diagnoses = set(primary_diagnoses)
        unanimous = len(unique_diagnoses) <= 1
        
        agreement_level = 1.0 if unanimous else 0.0
        
        consensus_result = ConsensusResult(
            collaboration_id=collaboration_id,
            consensus_type=ConsensusType.UNANIMOUS,
            consensus_reached=unanimous,
            agreement_level=agreement_level,
            participating_agents=[r.responding_agent for r in responses],
            average_confidence=mean(r.recommendation.overall_confidence for r in responses),
            confidence_standard_deviation=stdev(r.recommendation.overall_confidence for r in responses) if len(responses) > 1 else 0.0,
            weighted_confidence=mean(r.recommendation.overall_confidence for r in responses),
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
        )
        
        return consensus_result
    
    async def _bayesian_ensemble_consensus(self, 
                                         collaboration_id: str,
                                         responses: List[CollaborationResponse]) -> ConsensusResult:
        """Apply Bayesian ensemble consensus mechanism."""
        
        # Implement simplified Bayesian averaging
        # In a full implementation, this would use proper Bayesian inference
        
        diagnosis_posterior = defaultdict(list)
        
        for response in responses:
            for diagnosis in response.recommendation.differential_diagnoses:
                # Use confidence as proxy for prior strength
                prior_strength = response.recommendation.overall_confidence
                diagnosis_posterior[diagnosis.condition].append(
                    diagnosis.probability * prior_strength
                )
        
        # Calculate Bayesian average for each diagnosis
        diagnosis_bayesian_scores = {}
        for condition, probabilities in diagnosis_posterior.items():
            # Simple Bayesian average
            diagnosis_bayesian_scores[condition] = mean(probabilities)
        
        max_score = max(diagnosis_bayesian_scores.values()) if diagnosis_bayesian_scores else 0
        consensus_reached = max_score >= self.CONSENSUS_AGREEMENT_THRESHOLD
        
        consensus_result = ConsensusResult(
            collaboration_id=collaboration_id,
            consensus_type=ConsensusType.BAYESIAN_ENSEMBLE,
            consensus_reached=consensus_reached,
            agreement_level=max_score,
            participating_agents=[r.responding_agent for r in responses],
            average_confidence=mean(r.recommendation.overall_confidence for r in responses),
            confidence_standard_deviation=stdev(r.recommendation.overall_confidence for r in responses) if len(responses) > 1 else 0.0,
            weighted_confidence=max_score,
            diagnostic_consensus=diagnosis_bayesian_scores,
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
        )
        
        return consensus_result
    
    async def _specialist_priority_consensus(self, 
                                           collaboration_id: str,
                                           responses: List[CollaborationResponse]) -> ConsensusResult:
        """Apply specialist priority consensus (specialist takes priority in their domain)."""
        
        # Identify the most relevant specialist for the case
        specialty_relevance = {}
        
        for response in responses:
            specialty = response.recommendation.specialty
            # Calculate relevance based on confidence and specialty match
            relevance_score = response.recommendation.specialist_confidence
            specialty_relevance[specialty] = max(
                specialty_relevance.get(specialty, 0),
                relevance_score
            )
        
        # Find the highest relevance specialist
        primary_specialist = max(specialty_relevance.keys(), key=lambda s: specialty_relevance[s])
        
        # Use primary specialist's recommendation as consensus
        specialist_response = None
        for response in responses:
            if response.recommendation.specialty == primary_specialist:
                specialist_response = response
                break
        
        consensus_reached = specialist_response is not None
        agreement_level = specialty_relevance[primary_specialist] if consensus_reached else 0.0
        
        consensus_recommendation = specialist_response.recommendation if specialist_response else None
        
        consensus_result = ConsensusResult(
            collaboration_id=collaboration_id,
            consensus_type=ConsensusType.SPECIALIST_PRIORITY,
            consensus_reached=consensus_reached,
            agreement_level=agreement_level,
            participating_agents=[r.responding_agent for r in responses],
            consensus_recommendation=consensus_recommendation,
            average_confidence=mean(r.recommendation.overall_confidence for r in responses),
            confidence_standard_deviation=stdev(r.recommendation.overall_confidence for r in responses) if len(responses) > 1 else 0.0,
            weighted_confidence=agreement_level,
            specialty_weights=specialty_relevance,
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000
        )
        
        return consensus_result
    
    async def _build_consensus_recommendation(self, 
                                            responses: List[CollaborationResponse],
                                            diagnosis_scores: Dict[str, float],
                                            treatment_scores: Dict[str, float],
                                            agent_weights: Dict[str, float]) -> AgentRecommendation:
        """Build a consensus recommendation from weighted agent responses."""
        
        # Find consensus diagnosis
        consensus_diagnosis = max(diagnosis_scores.keys(), key=lambda k: diagnosis_scores[k]) if diagnosis_scores else "No consensus diagnosis"
        
        # Build consensus differential diagnoses
        consensus_differentials = []
        for condition, score in sorted(diagnosis_scores.items(), key=lambda x: x[1], reverse=True)[:5]:  # Top 5
            consensus_differentials.append(
                DifferentialDiagnosis(
                    condition=condition,
                    probability=min(1.0, score),  # Cap at 1.0
                    supporting_evidence=[
                        ClinicalEvidence(
                            evidence_type="consensus",
                            source="agent_collaboration",
                            finding=f"Consensus score: {score:.2f}",
                            significance="Multi-agent agreement",
                            confidence_level=score
                        )
                    ]
                )
            )
        
        # Build consensus treatment recommendations
        consensus_treatments = []
        for intervention, score in sorted(treatment_scores.items(), key=lambda x: x[1], reverse=True)[:3]:  # Top 3
            consensus_treatments.append(
                TreatmentRecommendation(
                    intervention=intervention,
                    priority="routine",  # Consensus tends toward conservative approach
                    rationale=f"Multi-agent consensus (agreement score: {score:.2f})"
                )
            )
        
        # Calculate consensus confidence
        weighted_confidences = [
            response.recommendation.overall_confidence * agent_weights[response.responding_agent]
            for response in responses
        ]
        consensus_confidence = sum(weighted_confidences)
        
        # Build consensus recommendation
        consensus_recommendation = AgentRecommendation(
            agent_id="consensus_engine",
            specialty=MedicalSpecialty.INTERNAL_MEDICINE,  # Default to internal medicine for consensus
            primary_assessment=f"Consensus assessment: {consensus_diagnosis}",
            differential_diagnoses=consensus_differentials,
            treatment_recommendations=consensus_treatments,
            overall_confidence=consensus_confidence,
            specialist_confidence=consensus_confidence,
            processing_time_ms=(datetime.utcnow() - self.processing_start_time).total_seconds() * 1000,
            knowledge_sources=["Multi-agent consensus", "Collaborative medical AI"]
        )
        
        return consensus_recommendation
    
    async def _identify_minority_opinions(self, 
                                        responses: List[CollaborationResponse],
                                        diagnosis_scores: Dict[str, float]) -> List[AgentRecommendation]:
        """Identify minority opinions that significantly differ from consensus."""
        
        if not diagnosis_scores:
            return []
        
        # Find consensus diagnosis
        consensus_diagnosis = max(diagnosis_scores.keys(), key=lambda k: diagnosis_scores[k])
        
        minority_opinions = []
        
        for response in responses:
            # Check if agent's primary diagnosis differs significantly from consensus
            agent_primary = None
            if response.recommendation.differential_diagnoses:
                agent_primary = max(
                    response.recommendation.differential_diagnoses,
                    key=lambda dx: dx.probability
                ).condition
            
            # If agent's primary diagnosis is different and has low consensus score
            if (agent_primary and 
                agent_primary != consensus_diagnosis and
                diagnosis_scores.get(agent_primary, 0) < self.CONSENSUS_AGREEMENT_THRESHOLD * 0.5):
                
                minority_opinions.append(response.recommendation)
        
        return minority_opinions
    
    async def _validate_consensus_safety(self, consensus_result: ConsensusResult) -> Dict[str, Any]:
        """Validate consensus from a safety perspective."""
        
        safety_concerns = []
        requires_review = False
        
        # Check confidence levels
        if consensus_result.average_confidence < self.SAFETY_REVIEW_THRESHOLD:
            safety_concerns.append("Low average confidence across agents")
            requires_review = True
        
        # Check agreement levels
        if consensus_result.agreement_level < self.CONSENSUS_AGREEMENT_THRESHOLD:
            safety_concerns.append("Low consensus agreement level")
            requires_review = True
        
        # Check for high confidence variance (indicates uncertainty)
        if consensus_result.confidence_standard_deviation > 0.3:
            safety_concerns.append("High confidence variance between agents")
            requires_review = True
        
        # Check for significant minority opinions
        if len(consensus_result.minority_opinions) > len(consensus_result.participating_agents) * 0.3:
            safety_concerns.append("Significant minority opinions present")
            requires_review = True
        
        return {
            "safety_concerns": safety_concerns,
            "requires_human_review": requires_review,
            "safety_score": 1.0 - len(safety_concerns) * 0.2  # Reduce score for each concern
        }
    
    async def _apply_safety_validation(self, 
                                     consensus_result: ConsensusResult,
                                     safety_validation: Dict[str, Any]) -> ConsensusResult:
        """Apply safety validation results to consensus."""
        
        # Update consensus result with safety information
        consensus_result.requires_human_review = safety_validation["requires_human_review"]
        consensus_result.safety_concerns = safety_validation["safety_concerns"]
        
        # If safety concerns exist, potentially escalate
        if safety_validation["requires_human_review"]:
            consensus_result.escalation_triggered = True
            
            logger.warning("Consensus requires human review due to safety concerns",
                          collaboration_id=consensus_result.collaboration_id,
                          safety_concerns=safety_validation["safety_concerns"])
        
        return consensus_result
    
    async def _calculate_quality_metrics(self, 
                                       responses: List[CollaborationResponse],
                                       consensus_result: ConsensusResult) -> Dict[str, Any]:
        """Calculate quality metrics for the consensus."""
        
        # Inter-rater reliability (simplified Fleiss' kappa approximation)
        agreement_matrix = []
        all_diagnoses = set()
        
        for response in responses:
            for dx in response.recommendation.differential_diagnoses:
                all_diagnoses.add(dx.condition)
        
        # Calculate pairwise agreements (simplified)
        pairwise_agreements = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                response_i = responses[i]
                response_j = responses[j]
                
                # Simple agreement check on primary diagnosis
                primary_i = response_i.recommendation.differential_diagnoses[0].condition if response_i.recommendation.differential_diagnoses else None
                primary_j = response_j.recommendation.differential_diagnoses[0].condition if response_j.recommendation.differential_diagnoses else None
                
                agreement = 1.0 if primary_i == primary_j else 0.0
                pairwise_agreements.append(agreement)
        
        inter_rater_reliability = mean(pairwise_agreements) if pairwise_agreements else 0.0
        
        # Evidence strength (average evidence confidence)
        evidence_scores = []
        for response in responses:
            for dx in response.recommendation.differential_diagnoses:
                for evidence in dx.supporting_evidence:
                    evidence_scores.append(evidence.confidence_level)
        
        evidence_strength = mean(evidence_scores) if evidence_scores else 0.0
        
        return {
            "inter_rater_reliability": inter_rater_reliability,
            "evidence_strength": evidence_strength,
            "response_quality": mean(r.recommendation.overall_confidence for r in responses),
            "consensus_entropy": await self._calculate_entropy(consensus_result.diagnostic_consensus)
        }
    
    async def _calculate_entropy(self, probabilities: Dict[str, float]) -> float:
        """Calculate entropy of diagnostic probabilities."""
        if not probabilities:
            return 0.0
        
        # Normalize probabilities
        total = sum(probabilities.values())
        if total == 0:
            return 0.0
        
        normalized_probs = [p / total for p in probabilities.values()]
        
        # Calculate entropy
        entropy = -sum(p * np.log2(p + 1e-10) for p in normalized_probs if p > 0)  # Add small epsilon to avoid log(0)
        
        return entropy
    
    async def _enhance_with_quality_metrics(self, 
                                          consensus_result: ConsensusResult,
                                          quality_metrics: Dict[str, Any]) -> ConsensusResult:
        """Enhance consensus result with quality metrics."""
        
        consensus_result.inter_rater_reliability = quality_metrics["inter_rater_reliability"]
        consensus_result.evidence_strength = quality_metrics["evidence_strength"]
        consensus_result.consensus_entropy = quality_metrics["consensus_entropy"]
        
        # Calculate overall quality score
        quality_factors = [
            quality_metrics["inter_rater_reliability"],
            quality_metrics["evidence_strength"],
            consensus_result.agreement_level,
            consensus_result.average_confidence
        ]
        
        consensus_result.quality_score = mean(quality_factors)
        
        return consensus_result
    
    async def _store_consensus_record(self, consensus_result: ConsensusResult) -> None:
        """Store consensus record in database for audit and analysis."""
        
        try:
            async with get_db() as db:
                # Generate consensus hash for integrity
                consensus_data = consensus_result.model_dump_json(exclude={"consensus_hash"})
                consensus_hash = hashlib.sha256(consensus_data.encode()).hexdigest()
                
                consensus_record = A2AConsensusRecord(
                    consensus_id=consensus_result.consensus_id,
                    collaboration_id=consensus_result.collaboration_id,
                    consensus_type=consensus_result.consensus_type.value,
                    algorithm_version=consensus_result.algorithm_version,
                    participating_agents=consensus_result.participating_agents,
                    total_participants=len(consensus_result.participating_agents),
                    consensus_reached=consensus_result.consensus_reached,
                    agreement_level=consensus_result.agreement_level,
                    consensus_recommendation=consensus_result.consensus_recommendation.model_dump() if consensus_result.consensus_recommendation else None,
                    minority_opinions=[op.model_dump() for op in consensus_result.minority_opinions],
                    average_confidence=consensus_result.average_confidence,
                    confidence_standard_deviation=consensus_result.confidence_standard_deviation,
                    weighted_confidence=consensus_result.weighted_confidence,
                    evidence_strength=consensus_result.evidence_strength,
                    guideline_compliance=0.8,  # Placeholder - would be calculated based on clinical guidelines
                    risk_assessment=consensus_result.risk_assessment,
                    diagnostic_consensus=consensus_result.diagnostic_consensus,
                    treatment_consensus=consensus_result.treatment_consensus,
                    specialty_weights=consensus_result.specialty_weights,
                    inter_rater_reliability=consensus_result.inter_rater_reliability,
                    consensus_entropy=consensus_result.consensus_entropy,
                    requires_human_review=consensus_result.requires_human_review,
                    escalation_triggered=consensus_result.escalation_triggered,
                    safety_concerns=consensus_result.safety_concerns,
                    processing_time_ms=consensus_result.processing_time_ms,
                    consensus_hash=consensus_hash,
                    created_at=datetime.utcnow()
                )
                
                db.add(consensus_record)
                await db.commit()
                await db.refresh(consensus_record)
                
        except Exception as e:
            logger.error("Failed to store consensus record",
                        consensus_id=consensus_result.consensus_id,
                        error=str(e))
            # Don't raise - consensus analysis should still succeed even if storage fails