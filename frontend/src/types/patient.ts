/**
 * Patient Risk Stratification Types
 * SOC2 Type 2 Compliant - CC6.1, CC7.2, A1.2
 * 
 * Security Controls:
 * - All PHI fields marked for encryption
 * - Audit logging required for risk calculations
 * - Access controls via RBAC
 */

import { Patient, CodeableConcept, Period } from './index';

// ============================================
// RISK STRATIFICATION CORE TYPES
// ============================================

export enum RiskLevel {
  LOW = 'low',
  MODERATE = 'moderate', 
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface RiskScore {
  readonly patientId: string; // SOC2: Immutable identifier
  readonly calculatedAt: string; // SOC2: Audit timestamp
  readonly calculatedBy: string; // SOC2: User tracking
  readonly score: number; // 0-100 scale
  readonly level: RiskLevel;
  readonly factors: RiskFactor[];
  readonly recommendations: CareRecommendation[];
  readonly confidence: number; // ML model confidence 0-1
  readonly expiresAt: string; // SOC2: Data retention
  readonly auditTrail: RiskAuditEvent[];
}

export interface RiskFactor {
  readonly factorId: string;
  readonly category: RiskFactorCategory;
  readonly severity: 'low' | 'moderate' | 'high' | 'critical';
  readonly description: string;
  readonly clinicalBasis: string;
  readonly weight: number; // Impact on overall score
  readonly evidenceLevel: 'strong' | 'moderate' | 'weak';
  readonly lastUpdated: string;
}

export enum RiskFactorCategory {
  CLINICAL = 'clinical',
  BEHAVIORAL = 'behavioral',
  SOCIAL_DETERMINANTS = 'social_determinants',
  UTILIZATION = 'utilization',
  MEDICATION = 'medication',
  LABORATORY = 'laboratory'
}

// ============================================
// CLINICAL METRICS (PHI - Encrypted)
// ============================================

export interface ClinicalMetrics {
  // Diabetes Management
  readonly hba1c?: number; // @PHI: Encrypted clinical value
  readonly glucoseControl?: GlucoseControlMetrics;
  
  // Cardiovascular
  readonly bloodPressure?: BloodPressureReading;
  readonly cholesterol?: CholesterolPanel;
  readonly cardiovascularRisk?: number;
  
  // General Health
  readonly bmi?: number;
  readonly smokingStatus?: SmokingStatus;
  readonly exerciseFrequency?: ExerciseLevel;
  
  // Chronic Conditions
  readonly chronicConditions: ChronicCondition[];
  readonly medications: MedicationRecord[];
  
  // Healthcare Utilization
  readonly recentHospitalizations: number;
  readonly emergencyVisits: number;
  readonly primaryCareVisits: number;
  readonly specialistVisits: number;
  
  // Laboratory Results
  readonly lastLabDate?: string;
  readonly labResults?: LabResult[];
  
  // Social Determinants (SDOH)
  readonly socialDeterminants?: SocialDeterminantsData;
  
  // Data Quality Indicators
  readonly dataCompleteness: number; // 0-1 score
  readonly lastUpdated: string;
  readonly dataSourceReliability: 'high' | 'medium' | 'low';
}

interface GlucoseControlMetrics {
  readonly averageGlucose?: number; // @PHI
  readonly timeInRange?: number; // Percentage
  readonly hypoglycemicEvents?: number;
  readonly hyperglycemicEvents?: number;
  readonly lastReading?: string;
}

interface BloodPressureReading {
  readonly systolic: number; // @PHI
  readonly diastolic: number; // @PHI
  readonly measuredAt: string;
  readonly isControlled: boolean;
}

interface CholesterolPanel {
  readonly totalCholesterol?: number; // @PHI
  readonly ldl?: number; // @PHI  
  readonly hdl?: number; // @PHI
  readonly triglycerides?: number; // @PHI
  readonly measuredAt: string;
}

interface ChronicCondition {
  readonly conditionId: string;
  readonly icdCode: string;
  readonly description: string;
  readonly severity: 'mild' | 'moderate' | 'severe';
  readonly diagnosedDate: string;
  readonly isActive: boolean;
  readonly managementStatus: 'well_controlled' | 'partially_controlled' | 'uncontrolled';
}

interface MedicationRecord {
  readonly medicationId: string;
  readonly name: string;
  readonly dosage: string;
  readonly frequency: string;
  readonly adherenceScore?: number; // 0-1
  readonly startDate: string;
  readonly endDate?: string;
  readonly prescribedBy: string;
  readonly isActive: boolean;
}

interface LabResult {
  readonly testName: string;
  readonly value: number; // @PHI
  readonly unit: string;
  readonly referenceRange: string;
  readonly isAbnormal: boolean;
  readonly measuredAt: string;
  readonly orderedBy: string;
}

interface SocialDeterminantsData {
  readonly educationLevel?: string;
  readonly employmentStatus?: string;
  readonly housingStability?: 'stable' | 'unstable' | 'homeless';
  readonly transportationAccess?: boolean;
  readonly foodSecurity?: 'secure' | 'insecure';
  readonly socialSupport?: 'strong' | 'moderate' | 'limited';
  readonly financialStress?: 'low' | 'moderate' | 'high';
}

export enum SmokingStatus {
  NEVER = 'never',
  FORMER = 'former',
  CURRENT = 'current',
  UNKNOWN = 'unknown'
}

export enum ExerciseLevel {
  SEDENTARY = 'sedentary',
  LIGHT = 'light',
  MODERATE = 'moderate', 
  VIGOROUS = 'vigorous'
}

// ============================================
// CARE RECOMMENDATIONS
// ============================================

export interface CareRecommendation {
  readonly recommendationId: string;
  readonly priority: 'immediate' | 'urgent' | 'routine' | 'preventive';
  readonly category: CareCategory;
  readonly description: string;
  readonly clinicalRationale: string;
  readonly actionItems: ActionItem[];
  readonly timeframe: string; // e.g., "within 48 hours"
  readonly assignedTo?: string; // Care team member
  readonly status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  readonly createdAt: string;
  readonly dueDate?: string;
}

export enum CareCategory {
  MEDICATION_MANAGEMENT = 'medication_management',
  LIFESTYLE_MODIFICATION = 'lifestyle_modification',
  CLINICAL_FOLLOW_UP = 'clinical_follow_up',
  SPECIALIST_REFERRAL = 'specialist_referral',
  DIAGNOSTIC_TESTING = 'diagnostic_testing',
  PATIENT_EDUCATION = 'patient_education',
  CARE_COORDINATION = 'care_coordination',
  EMERGENCY_INTERVENTION = 'emergency_intervention'
}

interface ActionItem {
  readonly actionId: string;
  readonly description: string;
  readonly responsible: string;
  readonly dueDate?: string;
  readonly isCompleted: boolean;
  readonly completedAt?: string;
}

// ============================================
// READMISSION RISK
// ============================================

export interface ReadmissionRisk {
  readonly patientId: string;
  readonly probability: number; // 0-1
  readonly timeFrame: '30_days' | '90_days' | '1_year';
  readonly riskFactors: ReadmissionRiskFactor[];
  readonly interventions: PreventiveIntervention[];
  readonly calculatedAt: string;
  readonly model: ModelMetadata;
}

interface ReadmissionRiskFactor {
  readonly factor: string;
  readonly impact: number; // Contribution to risk
  readonly modifiable: boolean;
  readonly interventionRequired: boolean;
}

interface PreventiveIntervention {
  readonly interventionId: string;
  readonly description: string;
  readonly evidenceLevel: 'high' | 'moderate' | 'low';
  readonly costEffectiveness: number;
  readonly timeToImplement: string;
}

interface ModelMetadata {
  readonly modelVersion: string;
  readonly accuracy: number;
  readonly precision: number;
  readonly recall: number;
  readonly lastTrained: string;
  readonly trainingDataSize: number;
}

// ============================================
// POPULATION HEALTH ANALYTICS
// ============================================

export interface PopulationMetrics {
  readonly cohortId: string;
  readonly cohortName: string;
  readonly totalPatients: number;
  readonly riskDistribution: RiskDistribution;
  readonly outcomeTrends: OutcomeTrend[];
  readonly costMetrics: CostMetrics;
  readonly qualityMeasures: QualityMeasure[];
  readonly generatedAt: string;
  readonly dataRange: Period;
}

interface RiskDistribution {
  readonly low: number;
  readonly moderate: number;
  readonly high: number;
  readonly critical: number;
}

interface OutcomeTrend {
  readonly metric: string;
  readonly timePoints: TimePoint[];
  readonly trendDirection: 'improving' | 'stable' | 'declining';
  readonly significanceLevel: number;
}

interface TimePoint {
  readonly date: string;
  readonly value: number;
  readonly confidence: number;
}

interface CostMetrics {
  readonly totalCost: number;
  readonly costPerPatient: number;
  readonly costTrends: CostTrend[];
  readonly savings: CostSavings[];
}

interface CostTrend {
  readonly category: string;
  readonly currentCost: number;
  readonly previousCost: number;
  readonly percentChange: number;
}

interface CostSavings {
  readonly intervention: string;
  readonly estimatedSavings: number;
  readonly confidenceInterval: [number, number];
}

interface QualityMeasure {
  readonly measureId: string;
  readonly name: string;
  readonly description: string;
  readonly currentScore: number;
  readonly benchmark: number;
  readonly improvement: number;
  readonly measureType: 'process' | 'outcome' | 'structure';
}

// ============================================
// SOC2 AUDIT & SECURITY
// ============================================

export interface RiskAuditEvent {
  readonly eventId: string;
  readonly timestamp: string;
  readonly userId: string; // SOC2: User accountability
  readonly sessionId: string; // SOC2: Session tracking
  readonly action: RiskAuditAction;
  readonly patientId: string; // @PHI: Encrypted reference
  readonly ipAddress: string; // SOC2: Access source
  readonly userAgent: string; // SOC2: Device fingerprinting
  readonly riskLevel?: RiskLevel;
  readonly dataAccessed: string[]; // SOC2: Data access tracking
  readonly auditHash: string; // SOC2: Data integrity
}

export enum RiskAuditAction {
  RISK_CALCULATION = 'risk_calculation',
  RISK_VIEW = 'risk_view',
  RISK_EXPORT = 'risk_export',
  RISK_SHARE = 'risk_share',
  RECOMMENDATION_VIEW = 'recommendation_view',
  RECOMMENDATION_MODIFY = 'recommendation_modify',
  BATCH_PROCESSING = 'batch_processing'
}

export interface SecurityContext {
  readonly userId: string;
  readonly roles: string[];
  readonly permissions: string[];
  readonly organizationId: string;
  readonly sessionId: string;
  readonly accessLevel: 'read' | 'write' | 'admin';
  readonly dataClassification: 'public' | 'internal' | 'confidential' | 'phi';
}

// ============================================
// SERVICE INTERFACES (SOC2 Compliant)
// ============================================

export interface IRiskStratificationService {
  // Core Risk Functions
  calculateRiskScore(patient: Patient, context: SecurityContext): Promise<RiskScore>;
  calculateBatchRiskScores(patients: Patient[], context: SecurityContext): Promise<RiskScore[]>;
  identifyRiskFactors(patient: Patient, context: SecurityContext): Promise<RiskFactor[]>;
  generateCareRecommendations(patient: Patient, context: SecurityContext): Promise<CareRecommendation[]>;
  calculateReadmissionRisk(patient: Patient, context: SecurityContext): Promise<ReadmissionRisk>;
  
  // Population Analytics
  generatePopulationMetrics(cohortId: string, context: SecurityContext): Promise<PopulationMetrics>;
  
  // SOC2 Compliance
  logAuditEvent(event: RiskAuditEvent): Promise<void>;
  validateDataAccess(patientId: string, context: SecurityContext): Promise<boolean>;
  encryptSensitiveData<T>(data: T): Promise<string>;
  decryptSensitiveData<T>(encryptedData: string): Promise<T>;
}

// ============================================
// API REQUEST/RESPONSE TYPES
// ============================================

export interface RiskCalculationRequest {
  readonly patientId: string;
  readonly includeRecommendations: boolean;
  readonly includeReadmissionRisk: boolean;
  readonly timeHorizon?: '30_days' | '90_days' | '1_year';
}

export interface RiskCalculationResponse {
  readonly riskScore: RiskScore;
  readonly recommendations?: CareRecommendation[];
  readonly readmissionRisk?: ReadmissionRisk;
  readonly generatedAt: string;
  readonly cacheExpiry: string;
}

export interface PopulationAnalyticsRequest {
  readonly cohortCriteria: CohortCriteria;
  readonly metricsRequested: string[];
  readonly timeRange: Period;
}

interface CohortCriteria {
  readonly ageRange?: [number, number];
  readonly genderFilter?: string[];
  readonly conditionsFilter?: string[];
  readonly riskLevelFilter?: RiskLevel[];
  readonly organizationFilter?: string[];
}

export interface PopulationAnalyticsResponse {
  readonly metrics: PopulationMetrics;
  readonly insights: PopulationInsight[];
  readonly recommendations: PopulationRecommendation[];
}

interface PopulationInsight {
  readonly type: 'trend' | 'outlier' | 'opportunity';
  readonly description: string;
  readonly significance: number;
  readonly actionable: boolean;
}

interface PopulationRecommendation {
  readonly priority: 'high' | 'medium' | 'low';
  readonly intervention: string;
  readonly expectedImpact: string;
  readonly estimatedCost: number;
  readonly evidenceLevel: string;
}

// ============================================
// ERROR HANDLING
// ============================================

export class RiskCalculationError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly patientId?: string // No PHI in error logs
  ) {
    super(message);
    this.name = 'RiskCalculationError';
  }
}

export class SOC2ComplianceError extends Error {
  constructor(
    message: string,
    public readonly controlId: string,
    public readonly severity: 'low' | 'medium' | 'high' | 'critical'
  ) {
    super(message);
    this.name = 'SOC2ComplianceError';
  }
}

// ============================================
// VALIDATION SCHEMAS
// ============================================

export interface DataValidationRule {
  readonly field: string;
  readonly required: boolean;
  readonly dataType: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object';
  readonly constraints?: ValidationConstraint[];
  readonly isPHI: boolean; // SOC2: PHI identification
}

interface ValidationConstraint {
  readonly type: 'min' | 'max' | 'pattern' | 'enum' | 'custom';
  readonly value: any;
  readonly message: string;
}