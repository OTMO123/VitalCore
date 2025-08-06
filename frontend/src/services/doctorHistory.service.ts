import { apiClient } from './api';
import { ApiResponse } from '@/types';

// ============================================
// TYPE DEFINITIONS
// ============================================

export interface EventPriority {
  CRITICAL: 'critical';
  HIGH: 'high';
  MEDIUM: 'medium';
  LOW: 'low';
  INFO: 'info';
}

export interface EventType {
  ADMISSION: 'admission';
  DISCHARGE: 'discharge';
  DIAGNOSIS: 'diagnosis';
  MEDICATION: 'medication';
  PROCEDURE: 'procedure';
  LAB_RESULT: 'lab_result';
  IMAGING: 'imaging';
  CONSULTATION: 'consultation';
  VITAL_SIGNS: 'vital_signs';
  ALLERGIES: 'allergies';
  IMMUNIZATION: 'immunization';
  CARE_PLAN: 'care_plan';
  PROGRESS_NOTE: 'progress_note';
  DISCHARGE_SUMMARY: 'discharge_summary';
}

export interface CarePhase {
  ASSESSMENT: 'assessment';
  PLANNING: 'planning';
  INTERVENTION: 'intervention';
  EVALUATION: 'evaluation';
  MAINTENANCE: 'maintenance';
  TRANSITION: 'transition';
  FOLLOW_UP: 'follow_up';
}

export interface MedicalEvent {
  event_id: string;
  event_type: keyof EventType;
  title: string;
  description?: string;
  event_date: string;
  priority: keyof EventPriority;
  provider_name?: string;
  location?: string;
  linked_events?: string[];
  parent_case_id?: string;
}

export interface LinkedTimelineEvent extends MedicalEvent {
  correlation_id?: string;
  sequence_number?: number;
  care_phase?: keyof CarePhase;
  outcome_status?: string;
  clinical_data?: Record<string, any>;
  diagnostic_codes?: string[];
  medication_data?: Record<string, any>;
  fhir_resource_type?: string;
  fhir_resource_id?: string;
}

export interface CaseSummary {
  case_id: string;
  patient_id: string;
  case_title: string;
  case_status: string;
  start_date: string;
  last_updated: string;
  primary_diagnosis?: string;
  secondary_diagnoses?: string[];
  attending_physician?: string;
  care_team?: string[];
  total_events: number;
  critical_events: number;
  last_critical_event?: string;
  length_of_stay?: number;
  admission_type?: string;
  discharge_disposition?: string;
}

export interface DoctorHistoryResponse {
  case_summary: CaseSummary;
  timeline_events: MedicalEvent[];
  patient_demographics: Record<string, any>;
  care_context: Record<string, any>;
  generated_at: string;
  total_events: number;
  date_range: {
    start: string;
    end: string;
  };
}

export interface LinkedTimelineResponse {
  case_id: string;
  patient_id: string;
  timeline_events: LinkedTimelineEvent[];
  event_correlations: Record<string, string[]>;
  care_transitions: Array<Record<string, any>>;
  critical_paths: Array<Record<string, any>>;
  timeline_start: string;
  timeline_end: string;
  total_linked_events: number;
  generated_at: string;
}

export interface CareCycle {
  cycle_id: string;
  patient_id: string;
  cycle_name: string;
  care_phase: keyof CarePhase;
  start_date: string;
  target_end_date?: string;
  actual_end_date?: string;
  assessment_data?: Record<string, any>;
  care_plan?: Record<string, any>;
  interventions?: Array<Record<string, any>>;
  outcomes?: Record<string, any>;
  completion_percentage: number;
  milestones_achieved: string[];
  pending_actions: string[];
  quality_indicators?: Record<string, any>;
  patient_satisfaction?: number;
  care_team_members: string[];
  resources_utilized?: string[];
}

export interface CareCyclesResponse {
  patient_id: string;
  active_cycles: CareCycle[];
  completed_cycles: CareCycle[];
  total_active_cycles: number;
  total_completed_cycles: number;
  average_cycle_duration?: number;
  care_complexity_score?: number;
  primary_care_areas: string[];
  care_coordination_notes?: string;
  generated_at: string;
}

export interface TimelineFilters {
  event_types?: Array<keyof EventType>;
  priority_levels?: Array<keyof EventPriority>;
  date_from?: string;
  date_to?: string;
  provider_filter?: string;
  include_linked_only?: boolean;
}

// ============================================
// DOCTOR HISTORY SERVICE
// ============================================

class DoctorHistoryService {
  private readonly BASE_PATH = '/doctor-history';

  /**
   * Get comprehensive case history for doctor review
   */
  async getCaseHistory(
    caseId: string,
    filters?: TimelineFilters
  ): Promise<ApiResponse<DoctorHistoryResponse>> {
    const params = new URLSearchParams();
    
    if (filters) {
      if (filters.event_types?.length) {
        filters.event_types.forEach(type => params.append('event_types', type));
      }
      if (filters.priority_levels?.length) {
        filters.priority_levels.forEach(priority => params.append('priority_levels', priority));
      }
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.provider_filter) params.append('provider_filter', filters.provider_filter);
    }

    const queryString = params.toString();
    const url = `${this.BASE_PATH}/history/${caseId}${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.get<DoctorHistoryResponse>(url);
  }

  /**
   * Get linked medical timeline with event correlation analysis
   */
  async getLinkedMedicalTimeline(
    caseId: string,
    filters?: TimelineFilters
  ): Promise<ApiResponse<LinkedTimelineResponse>> {
    const params = new URLSearchParams();
    
    if (filters) {
      if (filters.event_types?.length) {
        filters.event_types.forEach(type => params.append('event_types', type));
      }
      if (filters.priority_levels?.length) {
        filters.priority_levels.forEach(priority => params.append('priority_levels', priority));
      }
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.include_linked_only !== undefined) {
        params.append('include_linked_only', filters.include_linked_only.toString());
      }
    }

    const queryString = params.toString();
    const url = `${this.BASE_PATH}/timeline/${caseId}/linked${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.get<LinkedTimelineResponse>(url);
  }

  /**
   * Get patient care cycles for comprehensive care management
   */
  async getPatientCareCycles(
    patientId: string,
    includeCompleted: boolean = true
  ): Promise<ApiResponse<CareCyclesResponse>> {
    const params = new URLSearchParams();
    params.append('include_completed', includeCompleted.toString());
    
    const url = `${this.BASE_PATH}/care-cycles/${patientId}?${params.toString()}`;
    
    return apiClient.get<CareCyclesResponse>(url);
  }

  /**
   * Get care performance analytics for quality improvement
   */
  async getCarePerformanceAnalytics(
    dateFrom?: string,
    dateTo?: string
  ): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    const queryString = params.toString();
    const url = `${this.BASE_PATH}/analytics/care-performance${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.get(url);
  }

  /**
   * Get population health insights from care cycle data
   */
  async getPopulationHealthInsights(
    careArea?: string
  ): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    
    if (careArea) params.append('care_area', careArea);
    
    const queryString = params.toString();
    const url = `${this.BASE_PATH}/insights/population-health${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.get(url);
  }

  /**
   * Health check for doctor history service
   */
  async healthCheck(): Promise<ApiResponse<any>> {
    return apiClient.get(`${this.BASE_PATH}/health`);
  }

  // ============================================
  // UTILITY METHODS
  // ============================================

  /**
   * Format event date for display
   */
  formatEventDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Get priority color for UI display
   */
  getPriorityColor(priority: keyof EventPriority): string {
    const colorMap = {
      CRITICAL: 'text-red-600 bg-red-50 border-red-200',
      HIGH: 'text-orange-600 bg-orange-50 border-orange-200',
      MEDIUM: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      LOW: 'text-blue-600 bg-blue-50 border-blue-200',
      INFO: 'text-gray-600 bg-gray-50 border-gray-200'
    };
    
    return colorMap[priority] || colorMap.INFO;
  }

  /**
   * Get event type icon
   */
  getEventTypeIcon(eventType: keyof EventType): string {
    const iconMap = {
      ADMISSION: '🏥',
      DISCHARGE: '🚪',
      DIAGNOSIS: '🔍',
      MEDICATION: '💊',
      PROCEDURE: '🔧',
      LAB_RESULT: '🧪',
      IMAGING: '📷',
      CONSULTATION: '👨‍⚕️',
      VITAL_SIGNS: '💓',
      ALLERGIES: '⚠️',
      IMMUNIZATION: '💉',
      CARE_PLAN: '📋',
      PROGRESS_NOTE: '📝',
      DISCHARGE_SUMMARY: '📄'
    };
    
    return iconMap[eventType] || '📋';
  }

  /**
   * Calculate care cycle completion percentage
   */
  calculateCompletionPercentage(careCycle: CareCycle): number {
    if (!careCycle.actual_end_date && !careCycle.target_end_date) {
      return careCycle.completion_percentage || 0;
    }
    
    const now = new Date();
    const startDate = new Date(careCycle.start_date);
    const targetDate = careCycle.target_end_date ? new Date(careCycle.target_end_date) : now;
    
    const totalDuration = targetDate.getTime() - startDate.getTime();
    const elapsed = now.getTime() - startDate.getTime();
    
    const percentage = Math.min(100, Math.max(0, (elapsed / totalDuration) * 100));
    
    return Math.round(percentage);
  }

  /**
   * Group events by correlation for timeline visualization
   */
  groupEventsByCorrelation(events: LinkedTimelineEvent[]): Record<string, LinkedTimelineEvent[]> {
    return events.reduce((groups, event) => {
      const correlationId = event.correlation_id || 'uncorrelated';
      if (!groups[correlationId]) {
        groups[correlationId] = [];
      }
      groups[correlationId].push(event);
      return groups;
    }, {} as Record<string, LinkedTimelineEvent[]>);
  }

  /**
   * Extract care pathways from timeline events
   */
  extractCarePathways(events: LinkedTimelineEvent[]): Array<{
    pathway: LinkedTimelineEvent[];
    startEvent: LinkedTimelineEvent;
    endEvent: LinkedTimelineEvent;
    duration: number;
  }> {
    const pathways: Array<{
      pathway: LinkedTimelineEvent[];
      startEvent: LinkedTimelineEvent;
      endEvent: LinkedTimelineEvent;
      duration: number;
    }> = [];

    // Group events by correlation
    const correlatedGroups = this.groupEventsByCorrelation(events);

    // Process each correlation group to extract pathways
    Object.values(correlatedGroups).forEach(group => {
      if (group.length > 1) {
        // Sort by sequence number or date
        const sortedEvents = group.sort((a, b) => {
          if (a.sequence_number && b.sequence_number) {
            return a.sequence_number - b.sequence_number;
          }
          return new Date(a.event_date).getTime() - new Date(b.event_date).getTime();
        });

        const startEvent = sortedEvents[0];
        const endEvent = sortedEvents[sortedEvents.length - 1];
        const duration = new Date(endEvent.event_date).getTime() - new Date(startEvent.event_date).getTime();

        pathways.push({
          pathway: sortedEvents,
          startEvent,
          endEvent,
          duration
        });
      }
    });

    return pathways.sort((a, b) => b.duration - a.duration); // Sort by duration, longest first
  }
}

// ============================================
// SINGLETON INSTANCE
// ============================================

export const doctorHistoryService = new DoctorHistoryService();
export default doctorHistoryService;