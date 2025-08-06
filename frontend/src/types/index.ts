// ============================================
// CORE API TYPES
// ============================================

export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
  status?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================
// AUTHENTICATION TYPES
// ============================================

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface UserRole {
  id: string;
  name: string;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role_id?: string;
}

// ============================================
// PATIENT & HEALTHCARE TYPES
// ============================================

export interface Patient {
  resourceType: 'Patient';
  id: string;
  identifier: PatientIdentifier[];
  active: boolean;
  name: PatientName[];
  telecom?: ContactPoint[];
  gender?: 'male' | 'female' | 'other' | 'unknown';
  birthDate?: string;
  address?: Address[];
  consent_status: string;
  consent_types: string[];
  organization_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PatientIdentifier {
  use?: string;
  type?: CodeableConcept;
  system?: string;
  value: string;
}

export interface PatientName {
  use?: 'usual' | 'official' | 'temp' | 'nickname' | 'anonymous' | 'old' | 'maiden';
  family?: string;
  given?: string[];
  prefix?: string[];
  suffix?: string[];
}

export interface ContactPoint {
  system?: 'phone' | 'fax' | 'email' | 'pager' | 'url' | 'sms' | 'other';
  value?: string;
  use?: 'home' | 'work' | 'temp' | 'old' | 'mobile';
}

export interface Address {
  use?: 'home' | 'work' | 'temp' | 'old' | 'billing';
  type?: 'postal' | 'physical' | 'both';
  text?: string;
  line?: string[];
  city?: string;
  district?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}

export interface CodeableConcept {
  coding?: Coding[];
  text?: string;
}

export interface Coding {
  system?: string;
  version?: string;
  code?: string;
  display?: string;
  userSelected?: boolean;
}

export interface ClinicalDocument {
  id: string;
  patient_id: string;
  document_type: string;
  content: any;
  created_by: string;
  created_at: string;
  updated_at?: string;
  status: 'draft' | 'active' | 'inactive' | 'entered-in-error';
}

export interface Consent {
  id: string;
  patient_id: string;
  status: 'active' | 'inactive' | 'entered-in-error' | 'proposed' | 'rejected';
  scope: CodeableConcept;
  category: CodeableConcept[];
  provision?: ConsentProvision;
  created_at: string;
  updated_at?: string;
}

export interface ConsentProvision {
  type?: 'deny' | 'permit';
  period?: Period;
  actor?: ConsentActor[];
  action?: CodeableConcept[];
  purpose?: CodeableConcept[];
  data?: ConsentData[];
}

export interface ConsentActor {
  role: CodeableConcept;
  reference: Reference;
}

export interface ConsentData {
  meaning: 'instance' | 'related' | 'dependents' | 'authoredby';
  reference: Reference;
}

export interface Reference {
  reference?: string;
  type?: string;
  identifier?: PatientIdentifier;
  display?: string;
}

export interface Period {
  start?: string;
  end?: string;
}

// ============================================
// IRIS API TYPES
// ============================================

export interface IRISEndpoint {
  id: string;
  name: string;
  url: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  last_check: string;
  response_time?: number;
  error_count: number;
  success_rate: number;
}

export interface SyncResult {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  records_processed: number;
  records_failed: number;
  error_message?: string;
}

export interface HealthCheckResponse {
  endpoint_id: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  response_time: number;
  timestamp: string;
  error?: string;
}

export interface SystemHealthResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  total_endpoints: number;
  healthy_endpoints: number;
  degraded_endpoints: number;
  unhealthy_endpoints: number;
  avg_response_time: number;
  last_updated: string;
}

// ============================================
// AUDIT & COMPLIANCE TYPES
// ============================================

export interface AuditLog {
  id: string;
  event_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  user_id?: string;
  resource_type?: string;
  resource_id?: string;
  action: string;
  outcome: 'success' | 'failure' | 'unknown';
  timestamp: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
}

export interface ComplianceReport {
  id: string;
  report_type: 'soc2' | 'hipaa' | 'gdpr' | 'custom';
  period_start: string;
  period_end: string;
  status: 'generating' | 'completed' | 'failed';
  generated_at?: string;
  summary: ComplianceReportSummary;
  findings: ComplianceFinding[];
}

export interface ComplianceReportSummary {
  total_events: number;
  security_events: number;
  phi_access_events: number;
  compliance_violations: number;
  overall_score: number;
}

export interface ComplianceFinding {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
  recommendation?: string;
  affected_resources: string[];
}

// ============================================
// DATA ANONYMIZATION TYPES
// ============================================

export interface AnonymizationRequest {
  request_id: string;
  dataset_type: string;
  privacy_level: 'k_anonymity_5' | 'k_anonymity_10' | 'differential_privacy';
  fields_to_anonymize: string[];
  preserve_fields?: string[];
  batch_size?: number;
}

export interface AnonymizationResponse {
  request_id: string;
  status: 'processing' | 'completed' | 'failed';
  records_processed?: number;
  anonymized_data?: any[];
  utility_metrics?: UtilityMetrics;
  message?: string;
}

export interface UtilityMetrics {
  record_count: number;
  field_completeness: Record<string, number>;
  value_diversity: Record<string, number>;
  information_loss: number;
  data_quality_score: number;
}

// ============================================
// AI AGENT TYPES (Future)
// ============================================

export interface AIAgent {
  id: string;
  name: string;
  type: 'diagnostic' | 'predictive' | 'compliance' | 'patient_navigator';
  version: string;
  status: 'deployed' | 'deploying' | 'stopped' | 'error';
  deployment_target: 'edge' | 'cloud' | 'hybrid';
  capabilities: string[];
  performance_metrics: AgentPerformanceMetrics;
  created_at: string;
  last_updated: string;
}

export interface AgentPerformanceMetrics {
  accuracy: number;
  latency_ms: number;
  requests_per_second: number;
  error_rate: number;
  uptime: number;
}

export interface AgentDeploymentConfig {
  agent_type: string;
  deployment_target: 'edge' | 'cloud' | 'hybrid';
  privacy_level: string;
  resource_requirements: ResourceRequirements;
  model_version: string;
}

export interface ResourceRequirements {
  cpu_cores: number;
  memory_gb: number;
  gpu_required: boolean;
  storage_gb: number;
}

// ============================================
// SYSTEM MONITORING TYPES
// ============================================

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: ComponentHealth[];
  uptime: number;
  version: string;
  last_updated: string;
}

export interface ComponentHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  message?: string;
  metrics?: Record<string, number>;
}

export interface DashboardMetrics {
  total_patients: number;
  active_users: number;
  api_requests_today: number;
  compliance_score: number;
  system_uptime: number;
  recent_activities: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: 'patient_created' | 'user_login' | 'sync_completed' | 'audit_event';
  description: string;
  timestamp: string;
  user?: string;
  severity?: 'info' | 'warning' | 'error';
}

// ============================================
// FHIR VALIDATION TYPES
// ============================================

export interface FHIRValidationRequest {
  resource_type: string;
  resource_data: any;
  profile_url?: string;
}

export interface FHIRValidationResponse {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  profile_conformance: ProfileConformance;
}

export interface ValidationError {
  path: string;
  message: string;
  severity: 'error' | 'warning' | 'information';
}

export interface ValidationWarning {
  path: string;
  message: string;
  suggestion?: string;
}

export interface ProfileConformance {
  profile_url: string;
  conformance_level: 'full' | 'partial' | 'none';
  missing_elements: string[];
  extra_elements: string[];
}

// ============================================
// UTILITY TYPES
// ============================================

export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed';

export interface RequestState<T = any> {
  data: T | null;
  loading: LoadingState;
  error: string | null;
}

export interface FilterOptions {
  search?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  status?: string;
  type?: string;
  [key: string]: any;
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}