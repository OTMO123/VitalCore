// ============================================
// SERVICES INDEX
// ============================================

export { apiClient } from './api';
export { authService } from './auth.service';
export { patientService } from './patient.service';
export { irisService } from './iris.service';
export { auditService } from './audit.service';
export { dashboardService } from './dashboard.service';
export { documentService } from './document.service';
export { doctorHistoryService } from './doctorHistory.service';

// Export services factory function to avoid circular dependency
export const getServices = async () => {
  const { authService } = await import('./auth.service');
  const { patientService } = await import('./patient.service');
  const { irisService } = await import('./iris.service');
  const { auditService } = await import('./audit.service');
  const { dashboardService } = await import('./dashboard.service');
  const { documentService } = await import('./document.service');
  const { doctorHistoryService } = await import('./doctorHistory.service');
  
  return {
    auth: authService,
    patient: patientService,
    iris: irisService,
    audit: auditService,
    dashboard: dashboardService,
    document: documentService,
    doctorHistory: doctorHistoryService,
  } as const;
};