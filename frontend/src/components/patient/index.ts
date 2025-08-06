/**
 * Patient Management Components Export Index
 * Advanced Health Tech UI Components
 */

export { default as RiskScoreCard } from './RiskScoreCard';
export { default as PatientTableAdvanced } from './PatientTableAdvanced';
export { default as AdvancedSearchComponent } from './AdvancedSearchComponent';
export { default as PopulationHealthDashboard } from './PopulationHealthDashboard';

// Export types for convenience
export type {
  RiskLevel,
  RiskScore,
  RiskFactor,
  CareRecommendation,
  PopulationMetrics,
  ReadmissionRisk,
  SecurityContext,
  IRiskStratificationService
} from '../../types/patient';