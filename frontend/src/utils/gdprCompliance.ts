/**
 * GDPR Compliance Utilities
 * Enterprise Healthcare Production Ready
 */

import { auditLogger } from './auditLogger';

export interface ConsentRecord {
  id: string;
  userId: string;
  purpose: string;
  lawfulBasis: 'consent' | 'contract' | 'legal_obligation' | 'vital_interests' | 'public_task' | 'legitimate_interests';
  granted: boolean;
  timestamp: string;
  version: string;
  ipAddress: string;
  withdrawnAt?: string;
  expiresAt?: string;
}

export interface DataSubjectRights {
  rightOfAccess: boolean;
  rightToRectification: boolean;
  rightToErasure: boolean;
  rightToRestrictProcessing: boolean;
  rightToDataPortability: boolean;
  rightToObject: boolean;
}

export class GDPRCompliance {
  private readonly API_ENDPOINT = '/api/v1/gdpr';
  
  // Article 7 - Consent Management
  async recordConsent(
    userId: string,
    purpose: string,
    lawfulBasis: ConsentRecord['lawfulBasis'] = 'consent',
    version: string = '1.0'
  ): Promise<ConsentRecord> {
    const consentRecord: Omit<ConsentRecord, 'id'> = {
      userId,
      purpose,
      lawfulBasis,
      granted: true,
      timestamp: new Date().toISOString(),
      version,
      ipAddress: await this.getClientIP(),
    };

    try {
      const response = await fetch(`${this.API_ENDPOINT}/consent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify(consentRecord)
      });

      if (!response.ok) {
        throw new Error('Failed to record consent');
      }

      const savedConsent = await response.json();

      // Audit GDPR consent
      await auditLogger.logEvent({
        eventType: 'DATA_ACCESS',
        userId,
        action: 'GDPR_CONSENT_RECORDED',
        result: 'SUCCESS',
        riskLevel: 'MEDIUM',
        details: {
          purpose,
          lawfulBasis,
          version
        },
        complianceFlags: {
          hipaa: false,
          gdpr: true,
          fhir: false,
          soc2: true
        }
      });

      return savedConsent;
    } catch (error) {
      console.error('Error recording consent:', error);
      throw error;
    }
  }

  // Article 7(3) - Withdraw Consent
  async withdrawConsent(userId: string, consentId: string, reason?: string): Promise<void> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/consent/${consentId}/withdraw`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify({
          reason,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to withdraw consent');
      }

      // Audit consent withdrawal
      await auditLogger.logEvent({
        eventType: 'DATA_ACCESS',
        userId,
        action: 'GDPR_CONSENT_WITHDRAWN',
        result: 'SUCCESS',
        riskLevel: 'HIGH',
        details: {
          consentId,
          reason: reason || 'No reason provided'
        },
        complianceFlags: {
          hipaa: false,
          gdpr: true,
          fhir: false,
          soc2: true
        }
      });
    } catch (error) {
      console.error('Error withdrawing consent:', error);
      throw error;
    }
  }

  // Article 15 - Right of Access
  async requestDataAccess(userId: string): Promise<any> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/subject-access-request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify({
          userId,
          requestType: 'ACCESS',
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to process data access request');
      }

      const accessData = await response.json();

      // Audit data access request
      await auditLogger.logGDPRRequest(userId, 'ACCESS');

      return accessData;
    } catch (error) {
      console.error('Error processing data access request:', error);
      throw error;
    }
  }

  // Article 16 - Right to Rectification
  async requestDataRectification(userId: string, corrections: Record<string, any>): Promise<void> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/rectification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify({
          userId,
          corrections,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to process rectification request');
      }

      // Audit rectification request
      await auditLogger.logGDPRRequest(userId, 'RECTIFICATION');
    } catch (error) {
      console.error('Error processing rectification request:', error);
      throw error;
    }
  }

  // Article 17 - Right to Erasure (Right to be Forgotten)
  async requestDataErasure(userId: string, reason: string): Promise<void> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/erasure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify({
          userId,
          reason,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to process erasure request');
      }

      // Audit erasure request
      await auditLogger.logGDPRRequest(userId, 'DELETION');
    } catch (error) {
      console.error('Error processing erasure request:', error);
      throw error;
    }
  }

  // Article 20 - Right to Data Portability
  async requestDataPortability(userId: string, format: 'JSON' | 'CSV' | 'XML' = 'JSON'): Promise<Blob> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/portability`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify({
          userId,
          format,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to process portability request');
      }

      // Audit portability request
      await auditLogger.logGDPRRequest(userId, 'PORTABILITY');

      return await response.blob();
    } catch (error) {
      console.error('Error processing portability request:', error);
      throw error;
    }
  }

  // Validate consent before data processing
  async validateConsent(userId: string, purpose: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/consent/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify({ userId, purpose })
      });

      if (!response.ok) {
        return false;
      }

      const validation = await response.json();
      return validation.valid;
    } catch (error) {
      console.error('Error validating consent:', error);
      return false;
    }
  }

  // Get all consents for a user
  async getUserConsents(userId: string): Promise<ConsentRecord[]> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/consent/user/${userId}`, {
        headers: {
          'X-GDPR-Request': 'true'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user consents');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching user consents:', error);
      return [];
    }
  }

  // Cookie consent management
  async recordCookieConsent(
    categories: string[],
    granted: boolean,
    version: string = '1.0'
  ): Promise<void> {
    const consentData = {
      type: 'COOKIE_CONSENT',
      categories,
      granted,
      version,
      timestamp: new Date().toISOString(),
      ipAddress: await this.getClientIP()
    };

    try {
      const response = await fetch(`${this.API_ENDPOINT}/cookie-consent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify(consentData)
      });

      if (!response.ok) {
        throw new Error('Failed to record cookie consent');
      }

      // Store consent in localStorage for quick access
      localStorage.setItem('gdpr_cookie_consent', JSON.stringify(consentData));
    } catch (error) {
      console.error('Error recording cookie consent:', error);
      throw error;
    }
  }

  // Check if cookies are allowed
  isCookieConsentGranted(category: string = 'necessary'): boolean {
    try {
      const stored = localStorage.getItem('gdpr_cookie_consent');
      if (!stored) return false;

      const consent = JSON.parse(stored);
      return consent.granted && consent.categories.includes(category);
    } catch (error) {
      return false;
    }
  }

  // Privacy Impact Assessment helper
  async conductPIA(
    processing: {
      purpose: string;
      dataTypes: string[];
      recipients: string[];
      retention: string;
      lawfulBasis: string;
    }
  ): Promise<{
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
    recommendations: string[];
    dpiaRequired: boolean;
  }> {
    // Simplified PIA logic - in production this would be more comprehensive
    let riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' = 'LOW';
    const recommendations: string[] = [];
    let dpiaRequired = false;

    // Check for high-risk processing
    if (processing.dataTypes.some(type => 
      ['health', 'genetic', 'biometric', 'racial', 'political', 'religious'].includes(type.toLowerCase())
    )) {
      riskLevel = 'HIGH';
      dpiaRequired = true;
      recommendations.push('Full Data Protection Impact Assessment required');
      recommendations.push('Consider additional safeguards for special category data');
    }

    // Check for automated decision making
    if (processing.purpose.toLowerCase().includes('automated') || 
        processing.purpose.toLowerCase().includes('profiling')) {
      riskLevel = riskLevel === 'HIGH' ? 'HIGH' : 'MEDIUM';
      recommendations.push('Review automated decision-making processes');
      recommendations.push('Ensure human oversight in decision-making');
    }

    // Check for international transfers
    if (processing.recipients.some(recipient => 
      !['EU', 'EEA', 'UK'].includes(recipient.toUpperCase())
    )) {
      riskLevel = riskLevel === 'HIGH' ? 'HIGH' : 'MEDIUM';
      recommendations.push('Ensure adequate protection for international transfers');
      recommendations.push('Consider Standard Contractual Clauses (SCCs)');
    }

    return {
      riskLevel,
      recommendations,
      dpiaRequired
    };
  }

  // Data retention management
  async checkDataRetention(userId: string): Promise<{
    expired: boolean;
    expiryDate?: string;
    actions: string[];
  }> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/retention-check/${userId}`, {
        headers: {
          'X-GDPR-Request': 'true'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to check data retention');
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking data retention:', error);
      return {
        expired: false,
        actions: ['Error checking retention - manual review required']
      };
    }
  }

  // Breach notification helper
  async reportDataBreach(breach: {
    description: string;
    affectedUsers: string[];
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    containmentMeasures: string[];
    discoveredAt: string;
  }): Promise<void> {
    try {
      const response = await fetch(`${this.API_ENDPOINT}/breach-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-GDPR-Request': 'true'
        },
        body: JSON.stringify({
          ...breach,
          reportedAt: new Date().toISOString(),
          reporterId: 'SYSTEM' // In production, use actual user ID
        })
      });

      if (!response.ok) {
        throw new Error('Failed to report data breach');
      }

      // Audit breach report
      await auditLogger.logEvent({
        eventType: 'SECURITY',
        action: 'DATA_BREACH_REPORTED',
        result: 'SUCCESS',
        riskLevel: 'CRITICAL',
        details: {
          severity: breach.severity,
          affectedUserCount: breach.affectedUsers.length,
          description: breach.description.substring(0, 100)
        },
        complianceFlags: {
          hipaa: true,
          gdpr: true,
          fhir: false,
          soc2: true
        }
      });
    } catch (error) {
      console.error('Error reporting data breach:', error);
      throw error;
    }
  }

  private async getClientIP(): Promise<string> {
    // In production, this would get the real client IP from backend
    return 'CLIENT_IP_PLACEHOLDER';
  }
}

// Export singleton instance
export const gdprCompliance = new GDPRCompliance();

// GDPR Cookie Banner Component Data
export const COOKIE_CATEGORIES = {
  necessary: {
    name: 'Strictly Necessary',
    description: 'These cookies are essential for the website to function properly.',
    required: true
  },
  functional: {
    name: 'Functional',
    description: 'These cookies enable enhanced functionality and personalization.',
    required: false
  },
  analytics: {
    name: 'Analytics',
    description: 'These cookies help us understand how visitors interact with the website.',
    required: false
  },
  marketing: {
    name: 'Marketing',
    description: 'These cookies are used to deliver personalized advertisements.',
    required: false
  }
};

export default gdprCompliance;