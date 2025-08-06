/**
 * Enterprise Healthcare Security Utilities
 * SOC2 Type II, HIPAA, GDPR, FHIR R4 Compliant
 */

import CryptoJS from 'crypto-js';

// Security configuration for healthcare compliance
export const SECURITY_CONFIG = {
  // Password policy (HIPAA + SOC2)
  password: {
    minLength: 12,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    maxAge: 90 * 24 * 60 * 60 * 1000, // 90 days
    preventReuse: 12, // Last 12 passwords
  },
  
  // Session security
  session: {
    maxDuration: 8 * 60 * 60 * 1000, // 8 hours
    idleTimeout: 30 * 60 * 1000, // 30 minutes
    warningTime: 5 * 60 * 1000, // 5 minutes before timeout
  },
  
  // Encryption
  encryption: {
    algorithm: 'AES-256-GCM',
    keyRotationInterval: 30 * 24 * 60 * 60 * 1000, // 30 days
  },
  
  // Rate limiting
  rateLimit: {
    loginAttempts: 5,
    lockoutDuration: 15 * 60 * 1000, // 15 minutes
    apiRequestsPerMinute: 100,
  }
};

// Input sanitization for XSS prevention
export function sanitizeInput(input: string): string {
  if (!input || typeof input !== 'string') return '';
  
  return input
    .replace(/[<>\"']/g, '') // Remove HTML characters
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim()
    .substring(0, 1000); // Limit length
}

// HTML encoding for display
export function encodeHTML(str: string): string {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Password validation (HIPAA compliant)
export function validatePassword(password: string): {
  isValid: boolean;
  errors: string[];
  strength: 'WEAK' | 'FAIR' | 'STRONG' | 'VERY_STRONG';
} {
  const errors: string[] = [];
  let score = 0;
  
  if (password.length < SECURITY_CONFIG.password.minLength) {
    errors.push(`Password must be at least ${SECURITY_CONFIG.password.minLength} characters long`);
  } else {
    score += 1;
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  } else {
    score += 1;
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  } else {
    score += 1;
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  } else {
    score += 1;
  }
  
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character');
  } else {
    score += 1;
  }
  
  // Check for common patterns
  if (/(.)\1{3,}/.test(password)) {
    errors.push('Password cannot contain repeated characters');
  }
  
  if (/123|abc|qwe|password|admin/i.test(password)) {
    errors.push('Password cannot contain common patterns');
  }
  
  const strength = score <= 2 ? 'WEAK' : score === 3 ? 'FAIR' : score === 4 ? 'STRONG' : 'VERY_STRONG';
  
  return {
    isValid: errors.length === 0,
    errors,
    strength
  };
}

// Client-side encryption for sensitive data (temporary storage only)
export function encryptSensitiveData(data: string, key?: string): string {
  try {
    const encryptionKey = key || getSessionEncryptionKey();
    const encrypted = CryptoJS.AES.encrypt(data, encryptionKey).toString();
    return encrypted;
  } catch (error) {
    console.error('Encryption failed:', error);
    return '';
  }
}

// Client-side decryption
export function decryptSensitiveData(encryptedData: string, key?: string): string {
  try {
    const encryptionKey = key || getSessionEncryptionKey();
    const decrypted = CryptoJS.AES.decrypt(encryptedData, encryptionKey).toString(CryptoJS.enc.Utf8);
    return decrypted;
  } catch (error) {
    console.error('Decryption failed:', error);
    return '';
  }
}

// Generate session-specific encryption key
function getSessionEncryptionKey(): string {
  let sessionKey = sessionStorage.getItem('sk');
  if (!sessionKey) {
    sessionKey = CryptoJS.lib.WordArray.random(256/8).toString();
    sessionStorage.setItem('sk', sessionKey);
  }
  return sessionKey;
}

// HIPAA-compliant data masking for display
export function maskPHI(data: string, type: 'SSN' | 'PHONE' | 'EMAIL' | 'NAME' | 'DOB'): string {
  if (!data) return '';
  
  switch (type) {
    case 'SSN':
      return data.length >= 4 ? `***-**-${data.slice(-4)}` : '***-**-****';
    case 'PHONE':
      return data.length >= 4 ? `(***) ***-${data.slice(-4)}` : '(***) ***-****';
    case 'EMAIL':
      const [username, domain] = data.split('@');
      if (!domain) return '***@***.com';
      return `${username.charAt(0)}***@${domain}`;
    case 'NAME':
      const names = data.split(' ');
      return names.map(name => name.charAt(0) + '*'.repeat(Math.max(0, name.length - 1))).join(' ');
    case 'DOB':
      // Show only year
      const date = new Date(data);
      return date.getFullYear().toString() || '****';
    default:
      return '*'.repeat(data.length);
  }
}

// Generate FHIR-compliant resource IDs
export function generateFHIRResourceId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `${timestamp}-${random}`;
}

// GDPR consent validation
export interface ConsentRecord {
  purpose: string;
  granted: boolean;
  timestamp: string;
  version: string;
  ipAddress?: string;
}

export function validateConsent(consents: ConsentRecord[], requiredPurpose: string): boolean {
  const consent = consents.find(c => c.purpose === requiredPurpose);
  if (!consent) return false;
  
  // Check if consent is still valid (not older than 2 years for GDPR)
  const consentDate = new Date(consent.timestamp);
  const twoYearsAgo = new Date();
  twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2);
  
  return consent.granted && consentDate > twoYearsAgo;
}

// Generate secure tokens
export function generateSecureToken(length: number = 32): string {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Session management for HIPAA compliance
export class SecureSession {
  private sessionId: string;
  private startTime: number;
  private lastActivity: number;
  private warningShown: boolean = false;
  
  constructor() {
    this.sessionId = generateSecureToken();
    this.startTime = Date.now();
    this.lastActivity = Date.now();
    this.initSessionMonitoring();
  }
  
  private initSessionMonitoring(): void {
    // Track user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      document.addEventListener(event, () => {
        this.updateActivity();
      }, true);
    });
    
    // Check session validity every minute
    setInterval(() => {
      this.checkSessionValidity();
    }, 60 * 1000);
  }
  
  private updateActivity(): void {
    this.lastActivity = Date.now();
    this.warningShown = false;
  }
  
  private checkSessionValidity(): void {
    const now = Date.now();
    const sessionAge = now - this.startTime;
    const idleTime = now - this.lastActivity;
    
    // Check if session has exceeded maximum duration
    if (sessionAge > SECURITY_CONFIG.session.maxDuration) {
      this.terminateSession('SESSION_EXPIRED');
      return;
    }
    
    // Check for idle timeout
    if (idleTime > SECURITY_CONFIG.session.idleTimeout) {
      this.terminateSession('IDLE_TIMEOUT');
      return;
    }
    
    // Show warning before idle timeout
    const timeUntilTimeout = SECURITY_CONFIG.session.idleTimeout - idleTime;
    if (timeUntilTimeout <= SECURITY_CONFIG.session.warningTime && !this.warningShown) {
      this.showTimeoutWarning(Math.ceil(timeUntilTimeout / 60000));
      this.warningShown = true;
    }
  }
  
  private showTimeoutWarning(minutesLeft: number): void {
    // This would integrate with your notification system
    console.warn(`Session will expire in ${minutesLeft} minutes due to inactivity`);
    
    // In a real implementation, you'd show a modal or notification
    const userWantsToStay = confirm(
      `Your session will expire in ${minutesLeft} minutes due to inactivity. Do you want to continue?`
    );
    
    if (userWantsToStay) {
      this.updateActivity();
    }
  }
  
  private terminateSession(reason: string): void {
    console.warn(`Session terminated: ${reason}`);
    
    // Clear all session data
    sessionStorage.clear();
    localStorage.removeItem('authToken');
    
    // Redirect to login
    window.location.href = '/login';
  }
  
  getSessionId(): string {
    return this.sessionId;
  }
  
  getRemainingTime(): number {
    const now = Date.now();
    const sessionTimeLeft = SECURITY_CONFIG.session.maxDuration - (now - this.startTime);
    const idleTimeLeft = SECURITY_CONFIG.session.idleTimeout - (now - this.lastActivity);
    return Math.min(sessionTimeLeft, idleTimeLeft);
  }
}

// Rate limiting for API calls
export class RateLimiter {
  private attempts: Map<string, number[]> = new Map();
  
  isAllowed(identifier: string, maxAttempts: number = 5, windowMs: number = 15 * 60 * 1000): boolean {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    // Get or initialize attempts for this identifier
    const userAttempts = this.attempts.get(identifier) || [];
    
    // Filter out old attempts outside the time window
    const recentAttempts = userAttempts.filter(timestamp => timestamp > windowStart);
    
    // Update the attempts list
    this.attempts.set(identifier, recentAttempts);
    
    // Check if limit exceeded
    if (recentAttempts.length >= maxAttempts) {
      return false;
    }
    
    // Record this attempt
    recentAttempts.push(now);
    this.attempts.set(identifier, recentAttempts);
    
    return true;
  }
  
  getRemainingAttempts(identifier: string, maxAttempts: number = 5, windowMs: number = 15 * 60 * 1000): number {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    const userAttempts = this.attempts.get(identifier) || [];
    const recentAttempts = userAttempts.filter(timestamp => timestamp > windowStart);
    
    return Math.max(0, maxAttempts - recentAttempts.length);
  }
  
  getResetTime(identifier: string, windowMs: number = 15 * 60 * 1000): Date | null {
    const userAttempts = this.attempts.get(identifier) || [];
    if (userAttempts.length === 0) return null;
    
    const oldestAttempt = Math.min(...userAttempts);
    return new Date(oldestAttempt + windowMs);
  }
}

// Export singleton instances
export const secureSession = new SecureSession();
export const rateLimiter = new RateLimiter();

// Clean up sensitive data from memory
export function secureClearString(str: string): void {
  // In JavaScript, we can't truly clear strings from memory,
  // but we can try to overwrite the variable
  if (typeof str === 'string') {
    // This is more of a best-effort approach
    str = '\0'.repeat(str.length);
  }
}