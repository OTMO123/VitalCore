/**
 * VitalCore API Client
 * Complete JavaScript wrapper for the healthcare backend
 * Supports VitalCore, MedVault, and MedBrain APIs
 */

class VitalCoreClient {
    constructor(baseURL = null, options = {}) {
        // Auto-detect API URL based on environment
        this.baseURL = baseURL || this.detectApiUrl();
        this.token = localStorage.getItem('vitalcore_token');
        this.options = {
            timeout: 30000,
            retries: 3,
            ...options
        };
        
        // Event listeners for real-time updates
        this.eventListeners = new Map();
        this.websocket = null;
        
        // Initialize WebSocket for real-time notifications
        this.initWebSocket();
    }

    // =============================================
    // ENVIRONMENT DETECTION
    // =============================================
    
    detectApiUrl() {
        // Check if running in Vite development environment
        if (typeof import.meta !== 'undefined' && import.meta.env) {
            return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        }
        
        // Check for environment variables in various contexts
        if (typeof process !== 'undefined' && process.env) {
            return process.env.VITE_API_BASE_URL || process.env.REACT_APP_API_URL || 'http://localhost:8000';
        }
        
        // Auto-detect based on current host
        const currentHost = window.location.hostname;
        const currentProtocol = window.location.protocol;
        
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
            // Development - assume backend is on 8000
            return `${currentProtocol}//localhost:8000`;
        } else {
            // Production - assume same host, different port or path
            return `${currentProtocol}//${currentHost}:8000`;
        }
    }
    
    detectWebSocketUrl() {
        const baseUrl = this.baseURL.replace(/^http/, 'ws');
        return `${baseUrl}/ws`;
    }

    // =============================================
    // AUTHENTICATION & SESSION MANAGEMENT
    // =============================================

    async login(credentials) {
        try {
            const response = await this.request('/api/v1/auth/login', {
                method: 'POST',
                body: JSON.stringify(credentials)
            });
            
            if (response.access_token) {
                this.token = response.access_token;
                localStorage.setItem('vitalcore_token', this.token);
                localStorage.setItem('vitalcore_user', JSON.stringify(response.user));
                
                // Reconnect WebSocket with auth
                this.initWebSocket();
            }
            
            return response;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    async logout() {
        try {
            await this.request('/api/v1/auth/logout', { method: 'POST' });
        } finally {
            this.token = null;
            localStorage.removeItem('vitalcore_token');
            localStorage.removeItem('vitalcore_user');
            
            if (this.websocket) {
                this.websocket.close();
            }
        }
    }

    async refreshToken() {
        try {
            const response = await this.request('/api/v1/auth/refresh', {
                method: 'POST'
            });
            
            if (response.access_token) {
                this.token = response.access_token;
                localStorage.setItem('vitalcore_token', this.token);
            }
            
            return response;
        } catch (error) {
            // If refresh fails, logout user
            await this.logout();
            throw error;
        }
    }

    getCurrentUser() {
        return JSON.parse(localStorage.getItem('vitalcore_user') || 'null');
    }

    // =============================================
    // VITALCORE DASHBOARD APIs
    // =============================================

    dashboard = {
        // Get comprehensive dashboard statistics
        getStats: async () => {
            return this.request('/api/v1/dashboard/stats');
        },

        // Get recent activity feed
        getActivities: async (limit = 50) => {
            return this.request(`/api/v1/dashboard/activities?limit=${limit}`);
        },

        // Get system alerts
        getAlerts: async () => {
            return this.request('/api/v1/dashboard/alerts');
        },

        // Get system health status
        getHealth: async () => {
            return this.request('/health/detailed');
        },

        // Get performance metrics (admin only)
        getPerformance: async () => {
            return this.request('/api/v1/dashboard/performance');
        },

        // Refresh dashboard data (bulk update)
        refresh: async () => {
            return this.request('/api/v1/dashboard/refresh', {
                method: 'POST'
            });
        },

        // Get SOC2 availability metrics
        getSOC2Status: async () => {
            return this.request('/api/v1/dashboard/soc2/availability');
        },

        // Get circuit breaker status
        getCircuitBreakers: async () => {
            return this.request('/api/v1/dashboard/soc2/circuit-breakers');
        }
    };

    // =============================================
    // MEDVAULT - SECURE DATA STORAGE APIs
    // =============================================

    medvault = {
        // Get audit logs with filtering
        getAuditLogs: async (filters = {}) => {
            const params = new URLSearchParams(filters);
            return this.request(`/api/v1/audit-logs/logs?${params}`);
        },

        // Get enhanced audit activities
        getAuditActivities: async (limit = 100) => {
            return this.request(`/api/v1/audit-logs/enhanced-activities?limit=${limit}`);
        },

        // Get compliance report
        getComplianceReport: async (type = 'soc2') => {
            return this.request(`/api/v1/audit-logs/compliance/report?type=${type}`);
        },

        // Verify log integrity
        verifyIntegrity: async () => {
            return this.request('/api/v1/audit-logs/integrity/verify');
        },

        // Log PHI access (automatically called)
        logPHIAccess: async (patientId, purpose) => {
            return this.request('/api/v1/audit-logs/phi/access', {
                method: 'POST',
                body: JSON.stringify({ patient_id: patientId, purpose })
            });
        },

        // Get user activity logs
        getUserActivity: async (userId, timeRange = '24h') => {
            return this.request(`/api/v1/audit-logs/user/${userId}/activity?range=${timeRange}`);
        },

        // Get security violations
        getSecurityViolations: async () => {
            return this.request('/api/v1/audit-logs/security/violations');
        },

        // Export audit logs
        exportLogs: async (format = 'csv', filters = {}) => {
            return this.request('/api/v1/audit-logs/export', {
                method: 'POST',
                body: JSON.stringify({ format, filters })
            });
        },

        // Security monitoring
        security: {
            getDashboard: async () => {
                return this.request('/api/v1/security/dashboard');
            },

            getViolations: async () => {
                return this.request('/api/v1/security/violations');
            },

            getAnomalies: async () => {
                return this.request('/api/v1/security/anomalies');
            },

            reportIncident: async (incident) => {
                return this.request('/api/v1/security/incidents', {
                    method: 'POST',
                    body: JSON.stringify(incident)
                });
            },

            getMetrics: async () => {
                return this.request('/api/v1/security/metrics');
            },

            getComplianceStatus: async () => {
                return this.request('/api/v1/security/compliance/status');
            }
        }
    };

    // =============================================
    // MEDBRAIN - AI ASSISTANT APIs
    // =============================================

    medbrain = {
        // Send message to AI for clinical analysis
        clinicalAnalysis: async (request) => {
            return this.request('/api/v1/ai/gemma/clinical-analysis', {
                method: 'POST',
                body: JSON.stringify(request)
            });
        },

        // Get AI diagnostic assistance
        diagnosisAssist: async (symptoms, patientHistory) => {
            return this.request('/api/v1/ai/gemma/diagnosis-assist', {
                method: 'POST',
                body: JSON.stringify({
                    symptoms,
                    patient_history: patientHistory
                })
            });
        },

        // Get AI model status
        getModelStatus: async () => {
            return this.request('/api/v1/ai/models/status');
        },

        // Get explainable AI reasoning
        getExplanation: async (predictionId) => {
            return this.request('/api/v1/ai/explainable/reasoning', {
                method: 'POST',
                body: JSON.stringify({ prediction_id: predictionId })
            });
        },

        // Multimodal analysis (text + images)
        multimodalAnalysis: async (data) => {
            return this.request('/api/v1/ai/multimodal/analyze', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        // ML model management
        models: {
            list: async () => {
                return this.request('/api/v1/ml/models');
            },

            getPerformance: async () => {
                return this.request('/api/v1/ml/performance/metrics');
            },

            startTraining: async (config) => {
                return this.request('/api/v1/ml/training/start', {
                    method: 'POST',
                    body: JSON.stringify(config)
                });
            },

            getTrainingStatus: async (jobId) => {
                return this.request(`/api/v1/ml/training/${jobId}/status`);
            },

            deploy: async (modelId) => {
                return this.request('/api/v1/ml/models/deploy', {
                    method: 'POST',
                    body: JSON.stringify({ model_id: modelId })
                });
            }
        },

        // Data anonymization
        anonymize: async (data) => {
            return this.request('/api/v1/ml/anonymize', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }
    };

    // =============================================
    // HEALTHCARE RECORDS APIs
    // =============================================

    healthcare = {
        // Patient management
        patients: {
            list: async (filters = {}) => {
                const params = new URLSearchParams(filters);
                return this.request(`/fhir/Patient?${params}`);
            },

            get: async (patientId) => {
                // Automatically log PHI access
                await this.medvault.logPHIAccess(patientId, 'PATIENT_RECORD_VIEW');
                return this.request(`/fhir/Patient/${patientId}`);
            },

            create: async (patient) => {
                return this.request('/fhir/Patient', {
                    method: 'POST',
                    body: JSON.stringify(patient)
                });
            },

            update: async (patientId, patient) => {
                await this.medvault.logPHIAccess(patientId, 'PATIENT_RECORD_UPDATE');
                return this.request(`/fhir/Patient/${patientId}`, {
                    method: 'PUT',
                    body: JSON.stringify(patient)
                });
            },

            delete: async (patientId) => {
                await this.medvault.logPHIAccess(patientId, 'PATIENT_RECORD_DELETE');
                return this.request(`/fhir/Patient/${patientId}`, {
                    method: 'DELETE'
                });
            },

            search: async (query) => {
                return this.request('/api/v1/search/patients/advanced', {
                    method: 'POST',
                    body: JSON.stringify(query)
                });
            }
        },

        // Immunization management
        immunizations: {
            list: async (filters = {}) => {
                const params = new URLSearchParams(filters);
                return this.request(`/api/v1/healthcare/immunizations?${params}`);
            },

            get: async (immunizationId) => {
                return this.request(`/api/v1/healthcare/immunizations/${immunizationId}`);
            },

            create: async (immunization) => {
                if (immunization.patient_id) {
                    await this.medvault.logPHIAccess(immunization.patient_id, 'IMMUNIZATION_CREATE');
                }
                return this.request('/api/v1/healthcare/immunizations', {
                    method: 'POST',
                    body: JSON.stringify(immunization)
                });
            },

            update: async (immunizationId, immunization) => {
                return this.request(`/api/v1/healthcare/immunizations/${immunizationId}`, {
                    method: 'PUT',
                    body: JSON.stringify(immunization)
                });
            },

            delete: async (immunizationId) => {
                return this.request(`/api/v1/healthcare/immunizations/${immunizationId}`, {
                    method: 'DELETE'
                });
            }
        },

        // Document management
        documents: {
            upload: async (file, metadata) => {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('metadata', JSON.stringify(metadata));

                return this.request('/api/v1/documents/upload', {
                    method: 'POST',
                    body: formData,
                    headers: {} // Let browser set Content-Type for FormData
                });
            },

            get: async (documentId) => {
                return this.request(`/api/v1/documents/${documentId}`);
            },

            download: async (documentId) => {
                const response = await fetch(`${this.baseURL}/api/v1/documents/${documentId}/download`, {
                    headers: this.getHeaders()
                });
                return response.blob();
            },

            search: async (query) => {
                return this.request('/api/v1/documents/search', {
                    method: 'POST',
                    body: JSON.stringify(query)
                });
            },

            list: async (filters = {}) => {
                const params = new URLSearchParams(filters);
                return this.request(`/api/v1/documents?${params}`);
            }
        }
    };

    // =============================================
    // ANALYTICS & REPORTING APIs
    // =============================================

    analytics = {
        // Population health analytics
        populationHealth: async (metrics) => {
            return this.request('/api/v1/analytics/population/metrics', {
                method: 'POST',
                body: JSON.stringify(metrics)
            });
        },

        // Risk analysis
        riskDistribution: async (parameters) => {
            return this.request('/api/v1/analytics/risk/distribution', {
                method: 'POST',
                body: JSON.stringify(parameters)
            });
        },

        // Quality measures
        qualityMeasures: async (measures) => {
            return this.request('/api/v1/analytics/quality/measures', {
                method: 'POST',
                body: JSON.stringify(measures)
            });
        },

        // Cost analysis
        costAnalysis: async (parameters) => {
            return this.request('/api/v1/analytics/cost/analysis', {
                method: 'POST',
                body: JSON.stringify(parameters)
            });
        },

        // Get intervention opportunities
        getInterventions: async () => {
            return this.request('/api/v1/analytics/interventions');
        },

        // Trend analysis
        getTrends: async (metricType, timeRange = '30d') => {
            return this.request(`/api/v1/analytics/trends/${metricType}?range=${timeRange}`);
        },

        // Cohort analysis
        cohortAnalysis: async (cohortConfig) => {
            return this.request('/api/v1/analytics/cohorts/analyze', {
                method: 'POST',
                body: JSON.stringify(cohortConfig)
            });
        },

        // Risk stratification
        riskStratification: {
            calculate: async (patientData) => {
                return this.request('/api/v1/patients/risk/calculate', {
                    method: 'POST',
                    body: JSON.stringify(patientData)
                });
            },

            getPopulationSummary: async () => {
                return this.request('/api/v1/patients/risk/population/summary');
            },

            getHighRiskPatients: async () => {
                return this.request('/api/v1/patients/risk/high-risk');
            },

            getInterventions: async (riskFactors) => {
                return this.request('/api/v1/patients/risk/interventions', {
                    method: 'POST',
                    body: JSON.stringify(riskFactors)
                });
            },

            getModelPerformance: async () => {
                return this.request('/api/v1/patients/risk/models/performance');
            }
        }
    };

    // =============================================
    // FHIR R4 COMPLIANCE APIs
    // =============================================

    fhir = {
        // Bundle processing
        processBundle: async (bundle) => {
            return this.request('/fhir/Bundle', {
                method: 'POST',
                body: JSON.stringify(bundle)
            });
        },

        // Get FHIR capability statement
        getCapabilityStatement: async () => {
            return this.request('/fhir/metadata');
        },

        // FHIR resource validation
        validateResource: async (resource, profile = null) => {
            return this.request('/api/v1/fhir/validate', {
                method: 'POST',
                body: JSON.stringify({ resource, profile })
            });
        },

        // Search across all FHIR resources
        search: async (resourceType, parameters = {}) => {
            const params = new URLSearchParams(parameters);
            return this.request(`/fhir/${resourceType}?${params}`);
        }
    };

    // =============================================
    // REAL-TIME NOTIFICATIONS
    // =============================================

    // Subscribe to real-time events
    subscribe(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, new Set());
        }
        this.eventListeners.get(eventType).add(callback);
    }

    // Unsubscribe from events
    unsubscribe(eventType, callback) {
        if (this.eventListeners.has(eventType)) {
            this.eventListeners.get(eventType).delete(callback);
        }
    }

    // Initialize WebSocket connection for real-time updates
    initWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsURL = `${protocol}//${window.location.host}/ws/notifications`;
        
        this.websocket = new WebSocket(wsURL);
        
        this.websocket.onopen = () => {
            console.log('VitalCore WebSocket connected');
            
            // Send authentication
            if (this.token) {
                this.websocket.send(JSON.stringify({
                    type: 'auth',
                    token: this.token
                }));
            }
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            console.log('VitalCore WebSocket disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.initWebSocket(), 5000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('VitalCore WebSocket error:', error);
        };
    }

    // Handle incoming WebSocket messages
    handleWebSocketMessage(data) {
        const { type, payload } = data;
        
        if (this.eventListeners.has(type)) {
            this.eventListeners.get(type).forEach(callback => {
                callback(payload);
            });
        }
        
        // Emit global event
        window.dispatchEvent(new CustomEvent('vitalcore-notification', {
            detail: data
        }));
    }

    // =============================================
    // CORE HTTP CLIENT
    // =============================================

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: this.getHeaders(options.headers),
            ...options
        };

        let attempt = 0;
        while (attempt < this.options.retries) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.options.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (response.status === 401 && this.token && attempt === 0) {
                    // Try to refresh token
                    try {
                        await this.refreshToken();
                        config.headers = this.getHeaders(options.headers);
                        attempt++;
                        continue;
                    } catch (refreshError) {
                        await this.logout();
                        throw new Error('Authentication required');
                    }
                }
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
                    throw new Error(`HTTP ${response.status}: ${errorData.message || response.statusText}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }
                
                return response;
                
            } catch (error) {
                attempt++;
                
                if (error.name === 'AbortError') {
                    throw new Error('Request timeout');
                }
                
                if (attempt >= this.options.retries) {
                    throw error;
                }
                
                // Exponential backoff
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
            }
        }
    }

    getHeaders(customHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...customHeaders
        };
        
        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    // =============================================
    // WEBSOCKET REAL-TIME COMMUNICATION
    // =============================================
    
    initWebSocket() {
        try {
            const wsUrl = this.detectWebSocketUrl();
            console.log('🔌 Initializing WebSocket connection:', wsUrl);
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('✅ WebSocket connected');
                this.emit('websocket:connected');
                
                // Send authentication if available
                if (this.token) {
                    this.websocket.send(JSON.stringify({
                        type: 'auth',
                        token: this.token
                    }));
                }
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📨 WebSocket message received:', data.type);
                    
                    // Emit event to listeners
                    this.emit(`websocket:${data.type}`, data);
                    this.emit('websocket:message', data);
                } catch (error) {
                    console.error('🔥 Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = (event) => {
                console.log('🔌 WebSocket disconnected:', event.code, event.reason);
                this.emit('websocket:disconnected', { code: event.code, reason: event.reason });
                
                // Auto-reconnect after delay if not a normal closure
                if (event.code !== 1000 && event.code !== 1001) {
                    setTimeout(() => {
                        console.log('🔄 Attempting WebSocket reconnection...');
                        this.initWebSocket();
                    }, 5000);
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('🔥 WebSocket error:', error);
                this.emit('websocket:error', error);
            };
            
        } catch (error) {
            console.error('🔥 Failed to initialize WebSocket:', error);
        }
    }
    
    // Event emitter for WebSocket events
    emit(event, data) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`🔥 Error in event listener for ${event}:`, error);
                }
            });
        }
    }
    
    // Subscribe to WebSocket events
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }
    
    // Unsubscribe from WebSocket events
    off(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    // Send message via WebSocket
    send(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            console.warn('⚠️ WebSocket not connected, cannot send message');
        }
    }

    // =============================================
    // UTILITY METHODS
    // =============================================

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.token;
    }

    // Get current connection status
    getConnectionStatus() {
        return {
            authenticated: this.isAuthenticated(),
            websocket: this.websocket?.readyState === WebSocket.OPEN,
            user: this.getCurrentUser()
        };
    }

    // Format error for display
    formatError(error) {
        if (error.message.includes('HTTP 422')) {
            return 'Validation error: Please check your input data';
        }
        if (error.message.includes('HTTP 403')) {
            return 'Access denied: You don\'t have permission for this action';
        }
        if (error.message.includes('HTTP 404')) {
            return 'Resource not found';
        }
        if (error.message.includes('HTTP 500')) {
            return 'Server error: Please try again later';
        }
        return error.message || 'An unexpected error occurred';
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VitalCoreClient;
}

// Global instance for browser usage
if (typeof window !== 'undefined') {
    window.VitalCoreClient = VitalCoreClient;
    
    // Create default instance
    window.vitalcore = new VitalCoreClient();
    
    // Auto-refresh token every 30 minutes if authenticated
    setInterval(() => {
        if (window.vitalcore.isAuthenticated()) {
            window.vitalcore.refreshToken().catch(console.error);
        }
    }, 30 * 60 * 1000);
}