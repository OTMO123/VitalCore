/**
 * Patient Risk Stratification Service Tests
 * TDD Implementation for High-ROI Risk Analytics
 * SOC2 Type 2 Compliant Testing
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PatientRiskService } from '../patientRiskService';
import { 
  Patient, 
  RiskLevel, 
  RiskScore, 
  SecurityContext, 
  RiskCalculationError, 
  SOC2ComplianceError 
} from '../../types/patient';

// Extend Vitest matchers
declare global {
  namespace Vi {
    interface Matchers<T> {
      toBeOneOf(expected: any[]): T;
    }
  }
}

// Add custom matcher
expect.extend({
  toBeOneOf(received, expected) {
    const pass = expected.includes(received);
    return {
      message: () => `expected ${received} to be one of ${expected.join(', ')}`,
      pass,
    };
  },
});

describe('PatientRiskService - SOC2 Compliant', () => {
  let riskService: PatientRiskService;
  let mockPatient: Patient;
  let mockSecurityContext: SecurityContext;

  beforeEach(() => {
    riskService = new PatientRiskService();
    
    // Mock FHIR-compliant patient
    mockPatient = {
      resourceType: 'Patient',
      id: 'patient-123',
      identifier: [
        {
          use: 'usual',
          system: 'http://hospital.smarthealthit.org',
          value: 'MRN123456'
        }
      ],
      active: true,
      name: [
        {
          use: 'official',
          family: 'Doe',
          given: ['John']
        }
      ],
      gender: 'male',
      birthDate: '1970-01-01',
      consent_status: 'active',
      consent_types: ['treatment', 'research'],
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-12-01T00:00:00Z'
    };

    // Mock SOC2-compliant security context
    mockSecurityContext = {
      userId: 'user-456',
      roles: ['clinician'],
      permissions: ['patient_risk_read', 'phi_access'],
      organizationId: 'org-789',
      sessionId: 'session-123',
      accessLevel: 'read',
      dataClassification: 'phi'
    };

    // Mock security methods
    vi.spyOn(riskService as any, 'getCurrentSecurityContext')
      .mockResolvedValue(mockSecurityContext);
    vi.spyOn(riskService, 'logAuditEvent').mockResolvedValue();
    vi.spyOn(riskService, 'validateDataAccess').mockResolvedValue(true);
    vi.spyOn(riskService as any, 'getClientIpAddress').mockResolvedValue('127.0.0.1');
    vi.spyOn(riskService as any, 'getClientUserAgent').mockResolvedValue('Test-Agent');
  });

  describe('calculateRiskScore - Core Functionality', () => {
    it('should calculate risk score with proper SOC2 audit trail', async () => {
      // Act
      const riskScore = await riskService.calculateRiskScore(mockPatient, mockSecurityContext);

      // Assert - Basic functionality
      expect(riskScore).toBeDefined();
      expect(riskScore.patientId).toBe(mockPatient.id);
      expect(riskScore.calculatedBy).toBe(mockSecurityContext.userId);
      expect(riskScore.score).toBeGreaterThanOrEqual(0);
      expect(riskScore.score).toBeLessThanOrEqual(100);
      expect(riskScore.level).toBeOneOf([RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]);
      
      // Assert - Risk assessment components
      expect(Array.isArray(riskScore.factors)).toBe(true);
      expect(Array.isArray(riskScore.recommendations)).toBe(true);
      expect(riskScore.confidence).toBeGreaterThanOrEqual(0);
      expect(riskScore.confidence).toBeLessThanOrEqual(1);
      
      // Assert - SOC2 compliance (CC7.2: System Monitoring)
      expect(riskService.logAuditEvent).toHaveBeenCalledTimes(2); // Start and completion
      expect(riskService.validateDataAccess).toHaveBeenCalledWith(mockPatient.id, mockSecurityContext);
      
      // Assert - Data integrity
      expect(riskScore.calculatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/); // ISO timestamp
      expect(riskScore.expiresAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/); // ISO timestamp
    });

    it('should identify clinical risk factors correctly', async () => {
      // Act
      const riskFactors = await riskService.identifyRiskFactors(mockPatient, mockSecurityContext);

      // Assert
      expect(Array.isArray(riskFactors)).toBe(true);
      expect(riskFactors.length).toBeGreaterThan(0);
      
      // Verify risk factor structure
      riskFactors.forEach(factor => {
        expect(factor.factorId).toBeDefined();
        expect(factor.category).toBeDefined();
        expect(factor.severity).toBeOneOf(['low', 'moderate', 'high', 'critical']);
        expect(factor.description).toBeDefined();
        expect(factor.clinicalBasis).toBeDefined();
        expect(factor.weight).toBeGreaterThan(0);
        expect(factor.evidenceLevel).toBeOneOf(['strong', 'moderate', 'weak']);
      });
    });

    it('should generate evidence-based care recommendations', async () => {
      // Act
      const recommendations = await riskService.generateCareRecommendations(mockPatient, mockSecurityContext);

      // Assert
      expect(Array.isArray(recommendations)).toBe(true);
      expect(recommendations.length).toBeGreaterThan(0);
      
      // Verify recommendation structure
      recommendations.forEach(rec => {
        expect(rec.recommendationId).toBeDefined();
        expect(rec.priority).toBeOneOf(['immediate', 'urgent', 'routine', 'preventive']);
        expect(rec.category).toBeDefined();
        expect(rec.description).toBeDefined();
        expect(rec.clinicalRationale).toBeDefined();
        expect(Array.isArray(rec.actionItems)).toBe(true);
        expect(rec.status).toBeOneOf(['pending', 'in_progress', 'completed', 'overdue']);
      });
    });

    it('should calculate readmission risk with model metadata', async () => {
      // Act
      const readmissionRisk = await riskService.calculateReadmissionRisk(mockPatient, mockSecurityContext);

      // Assert
      expect(readmissionRisk).toBeDefined();
      expect(readmissionRisk.patientId).toBe(mockPatient.id);
      expect(readmissionRisk.probability).toBeGreaterThanOrEqual(0);
      expect(readmissionRisk.probability).toBeLessThanOrEqual(1);
      expect(readmissionRisk.timeFrame).toBeOneOf(['30_days', '90_days', '1_year']);
      expect(Array.isArray(readmissionRisk.riskFactors)).toBe(true);
      expect(Array.isArray(readmissionRisk.interventions)).toBe(true);
      
      // Verify model metadata for transparency
      expect(readmissionRisk.model).toBeDefined();
      expect(readmissionRisk.model.modelVersion).toBeDefined();
      expect(readmissionRisk.model.accuracy).toBeGreaterThan(0);
      expect(readmissionRisk.model.accuracy).toBeLessThanOrEqual(1);
    });

    it('should handle invalid patient data gracefully', async () => {
      // Arrange
      const invalidPatient = { ...mockPatient, id: '' };

      // Act & Assert
      await expect(riskService.calculateRiskScore(invalidPatient as any, mockSecurityContext))
        .rejects.toThrow(RiskCalculationError);
    });
  });

  describe('SOC2 Security Controls', () => {
    it('should enforce access controls (CC6.1)', async () => {
      // Arrange - Mock insufficient permissions
      const restrictedContext = {
        ...mockSecurityContext,
        permissions: ['basic_read'] // Missing patient_risk_read
      };
      
      vi.spyOn(riskService, 'validateDataAccess')
        .mockRejectedValue(new SOC2ComplianceError('Insufficient permissions', 'CC6.1', 'high'));

      // Act & Assert
      await expect(riskService.calculateRiskScore(mockPatient, restrictedContext))
        .rejects.toThrow(SOC2ComplianceError);
    });

    it('should log all data access for audit trail (CC7.2)', async () => {
      // Act
      await riskService.calculateRiskScore(mockPatient, mockSecurityContext);

      // Assert - Verify comprehensive audit logging
      expect(riskService.logAuditEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          userId: mockSecurityContext.userId,
          sessionId: mockSecurityContext.sessionId,
          patientId: mockPatient.id,
          action: 'risk_calculation',
          ipAddress: '127.0.0.1',
          userAgent: 'Test-Agent'
        })
      );
    });

    it('should not expose PHI in error messages', async () => {
      // Arrange
      const patientWithPHI = {
        ...mockPatient,
        name: [{ given: ['John'], family: 'Smith' }]
      };
      
      vi.spyOn(riskService as any, 'extractClinicalMetrics')
        .mockRejectedValue(new Error('Clinical data extraction failed'));

      // Act & Assert
      try {
        await riskService.calculateRiskScore(patientWithPHI, mockSecurityContext);
        expect.fail('Expected error to be thrown');
      } catch (error: any) {
        // Verify no PHI in error message
        expect(error.message).not.toContain('John');
        expect(error.message).not.toContain('Smith');
        expect(error.message).not.toContain(mockPatient.id);
      }
    });

    it('should fail securely when audit logging fails (CC7.2)', async () => {
      // Arrange
      vi.spyOn(riskService, 'logAuditEvent')
        .mockRejectedValue(new Error('Audit system unavailable'));

      // Act & Assert
      await expect(riskService.calculateRiskScore(mockPatient, mockSecurityContext))
        .rejects.toThrow(SOC2ComplianceError);
    });
  });

  describe('Performance and Availability (A1.2)', () => {
    it('should complete risk calculation within performance threshold', async () => {
      // Arrange
      const startTime = Date.now();

      // Act
      await riskService.calculateRiskScore(mockPatient, mockSecurityContext);

      // Assert
      const executionTime = Date.now() - startTime;
      expect(executionTime).toBeLessThan(1000); // < 1 second
    });

    it('should handle batch processing efficiently', async () => {
      // Arrange
      const patients = Array(10).fill(null).map((_, index) => ({
        ...mockPatient,
        id: `patient-${index}`,
        identifier: [{ value: `MRN${index}` }]
      }));

      const startTime = Date.now();

      // Act
      const results = await riskService.calculateBatchRiskScores(patients, mockSecurityContext);

      // Assert
      const executionTime = Date.now() - startTime;
      expect(results).toHaveLength(10);
      expect(executionTime).toBeLessThan(5000); // < 5 seconds for 10 patients
      
      // Verify all results are valid
      results.forEach(result => {
        expect(result.patientId).toMatch(/^patient-\d+$/);
        expect(result.score).toBeGreaterThanOrEqual(0);
        expect(result.level).toBeOneOf([RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]);
      });
    });

    it('should reject oversized batch requests', async () => {
      // Arrange
      const largePatientBatch = Array(1001).fill(mockPatient); // Exceeds 1000 limit

      // Act & Assert
      await expect(riskService.calculateBatchRiskScores(largePatientBatch, mockSecurityContext))
        .rejects.toThrow(RiskCalculationError);
    });
  });

  describe('Data Quality and Clinical Accuracy', () => {
    it('should provide confidence scores for risk assessments', async () => {
      // Act
      const riskScore = await riskService.calculateRiskScore(mockPatient, mockSecurityContext);

      // Assert
      expect(riskScore.confidence).toBeGreaterThan(0);
      expect(riskScore.confidence).toBeLessThanOrEqual(1);
      
      // Higher confidence expected when more evidence-based factors present
      const strongEvidenceFactors = riskScore.factors.filter(f => f.evidenceLevel === 'strong');
      if (strongEvidenceFactors.length > 0) {
        expect(riskScore.confidence).toBeGreaterThan(0.5);
      }
    });

    it('should maintain clinical accuracy in risk stratification', async () => {
      // Act
      const riskScore = await riskService.calculateRiskScore(mockPatient, mockSecurityContext);

      // Assert - Risk factors should align with clinical evidence
      const clinicalFactors = riskScore.factors.filter(f => f.category === 'clinical');
      expect(clinicalFactors.length).toBeGreaterThan(0);
      
      // Verify clinical rationale exists for each factor
      clinicalFactors.forEach(factor => {
        expect(factor.clinicalBasis).toBeDefined();
        expect(factor.clinicalBasis.length).toBeGreaterThan(10); // Meaningful explanation
      });
    });

    it('should generate actionable care recommendations', async () => {
      // Act
      const recommendations = await riskService.generateCareRecommendations(mockPatient, mockSecurityContext);

      // Assert
      expect(recommendations.length).toBeGreaterThan(0);
      
      recommendations.forEach(rec => {
        // Each recommendation should have actionable items
        expect(rec.actionItems.length).toBeGreaterThan(0);
        
        // Should have appropriate timeframes
        expect(rec.timeframe).toBeDefined();
        
        // Should have due dates for urgent/immediate items
        if (rec.priority === 'immediate' || rec.priority === 'urgent') {
          expect(rec.dueDate).toBeDefined();
        }
      });
    });
  });

  describe('Integration and Error Handling', () => {
    it('should handle service dependencies gracefully', async () => {
      // Arrange - Mock service dependency failure
      vi.spyOn(riskService as any, 'getCurrentSecurityContext')
        .mockRejectedValue(new Error('Authentication service unavailable'));

      // Act & Assert
      await expect(riskService.calculateRiskScore(mockPatient))
        .rejects.toThrow(SOC2ComplianceError);
    });

    it('should maintain data consistency across operations', async () => {
      // Act
      const riskScore1 = await riskService.calculateRiskScore(mockPatient, mockSecurityContext);
      const riskScore2 = await riskService.calculateRiskScore(mockPatient, mockSecurityContext);

      // Assert - Same patient should get consistent results (within cache period)
      expect(riskScore1.patientId).toBe(riskScore2.patientId);
      expect(riskScore1.level).toBe(riskScore2.level);
      // Note: Score might vary slightly due to timestamps, but should be close
      expect(Math.abs(riskScore1.score - riskScore2.score)).toBeLessThan(5);
    });
  });
});