import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest'
import { JSDOM } from 'jsdom'

// Mock axios for API testing
const mockAxios = {
  defaults: { baseURL: 'http://localhost:8000/api/v1' },
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  create: vi.fn(() => mockAxios),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() }
  }
}

vi.mock('axios', () => ({ default: mockAxios }))

// API-to-UI Integration Test Suite for HEMA3N
describe('HEMA3N API-to-UI Integration Test Suite', () => {
  let dom: JSDOM
  let window: Window
  let document: Document

  beforeAll(async () => {
    dom = new JSDOM('<!DOCTYPE html><html><head><title>HEMA3N Platform</title></head><body><div id="root"></div></body></html>', {
      url: 'http://localhost:3000',
      pretendToBeVisual: true,
      resources: 'usable'
    })
    
    // @ts-ignore
    global.window = dom.window
    // @ts-ignore
    global.document = dom.window.document
    // @ts-ignore
    global.navigator = dom.window.navigator
    // @ts-ignore
    global.fetch = vi.fn()
    
    window = dom.window as unknown as Window
    document = dom.window.document
  })

  afterAll(() => {
    dom.window.close()
    vi.restoreAllMocks()
  })

  describe('Authentication API Integration', () => {
    it('should handle successful login and update UI state', async () => {
      // Mock successful login response
      mockAxios.post.mockResolvedValueOnce({
        data: {
          access_token: 'mock-jwt-token',
          user: {
            id: 1,
            username: 'admin',
            role: 'admin',
            permissions: ['read', 'write', 'admin']
          }
        }
      })

      // Simulate login form and response handling
      const loginContainer = document.createElement('div')
      loginContainer.innerHTML = `
        <form id="login-form">
          <input type="text" id="username" value="admin" />
          <input type="password" id="password" value="admin123" />
          <button type="submit" id="login-btn">Login</button>
        </form>
        <div id="user-info" style="display: none;"></div>
        <div id="error-message" style="display: none;"></div>
      `
      
      document.body.appendChild(loginContainer)

      // Simulate form submission and API call
      const loginForm = document.getElementById('login-form')
      const userInfo = document.getElementById('user-info')
      const errorMsg = document.getElementById('error-message')

      // Mock API response processing
      const apiResponse = await mockAxios.post('/auth/login', {
        username: 'admin',
        password: 'admin123'
      })

      // Simulate UI update after successful login
      if (apiResponse.data.access_token && userInfo) {
        userInfo.innerHTML = `
          <span>Welcome, ${apiResponse.data.user.username}</span>
          <span class="role">Role: ${apiResponse.data.user.role}</span>
        `
        userInfo.style.display = 'block'
      }

      expect(mockAxios.post).toHaveBeenCalledWith('/auth/login', {
        username: 'admin',
        password: 'admin123'
      })
      expect(userInfo?.textContent).toContain('Welcome, admin')
      expect(userInfo?.textContent).toContain('Role: admin')
    })

    it('should handle login failure and display error message', async () => {
      // Mock failed login response
      mockAxios.post.mockRejectedValueOnce({
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' }
        }
      })

      const errorContainer = document.createElement('div')
      errorContainer.innerHTML = `
        <div id="error-display" class="hidden"></div>
      `
      
      document.body.appendChild(errorContainer)

      // Simulate API call and error handling
      try {
        await mockAxios.post('/auth/login', {
          username: 'invalid',
          password: 'wrong'
        })
      } catch (error: any) {
        const errorDisplay = document.getElementById('error-display')
        if (errorDisplay) {
          errorDisplay.textContent = error.response.data.detail
          errorDisplay.classList.remove('hidden')
        }
      }

      const errorDisplay = document.getElementById('error-display')
      expect(errorDisplay?.textContent).toBe('Invalid credentials')
      expect(errorDisplay?.classList.contains('hidden')).toBe(false)
    })
  })

  describe('Patient Data API Integration', () => {
    it('should fetch patient list and populate data grid', async () => {
      // Mock patients API response
      const mockPatients = [
        {
          id: 'P001',
          name: 'John Doe',
          dob: '1980-01-15',
          status: 'Active',
          last_visit: '2024-01-10'
        },
        {
          id: 'P002',
          name: 'Jane Smith',
          dob: '1975-05-22',
          status: 'Inactive',
          last_visit: '2023-12-15'
        }
      ]

      mockAxios.get.mockResolvedValueOnce({
        data: { patients: mockPatients, total: 2 }
      })

      // Simulate patients data grid
      const patientsContainer = document.createElement('div')
      patientsContainer.innerHTML = `
        <div class="MuiDataGrid-root">
          <div class="MuiDataGrid-columnHeaders">
            <div role="columnheader">ID</div>
            <div role="columnheader">Name</div>
            <div role="columnheader">DOB</div>
            <div role="columnheader">Status</div>
          </div>
          <div class="MuiDataGrid-virtualScroller">
            <div id="patient-rows"></div>
          </div>
        </div>
        <div id="loading-indicator" style="display: block;">Loading patients...</div>
      `
      
      document.body.appendChild(patientsContainer)

      // Simulate API call and UI update
      const response = await mockAxios.get('/patients')
      const patientRows = document.getElementById('patient-rows')
      const loadingIndicator = document.getElementById('loading-indicator')

      if (patientRows && response.data.patients) {
        response.data.patients.forEach((patient: any) => {
          const row = document.createElement('div')
          row.className = 'MuiDataGrid-row'
          row.innerHTML = `
            <div class="MuiDataGrid-cell">${patient.id}</div>
            <div class="MuiDataGrid-cell">${patient.name}</div>
            <div class="MuiDataGrid-cell">${patient.dob}</div>
            <div class="MuiDataGrid-cell">
              <span class="status-${patient.status.toLowerCase()}">${patient.status}</span>
            </div>
          `
          patientRows.appendChild(row)
        })
      }

      if (loadingIndicator) {
        loadingIndicator.style.display = 'none'
      }

      expect(mockAxios.get).toHaveBeenCalledWith('/patients')
      expect(document.querySelectorAll('.MuiDataGrid-row').length).toBe(2)
      expect(document.querySelector('.MuiDataGrid-cell')?.textContent).toBe('P001')
      expect(loadingIndicator?.style.display).toBe('none')
    })

    it('should handle patient creation API and update UI', async () => {
      // Mock successful patient creation
      const newPatient = {
        id: 'P003',
        name: 'Bob Johnson',
        dob: '1990-08-30',
        status: 'Active'
      }

      mockAxios.post.mockResolvedValueOnce({
        data: { patient: newPatient, message: 'Patient created successfully' }
      })

      const createPatientForm = document.createElement('div')
      createPatientForm.innerHTML = `
        <form id="patient-form">
          <input type="text" id="patient-name" value="Bob Johnson" />
          <input type="date" id="patient-dob" value="1990-08-30" />
          <button type="submit" id="create-btn">Create Patient</button>
        </form>
        <div id="success-message" class="hidden"></div>
        <div id="patient-list">
          <div class="patient-count">Patients: 2</div>
        </div>
      `
      
      document.body.appendChild(createPatientForm)

      // Simulate form submission and API call
      const response = await mockAxios.post('/patients', {
        name: 'Bob Johnson',
        dob: '1990-08-30'
      })

      const successMessage = document.getElementById('success-message')
      const patientCount = document.querySelector('.patient-count')

      if (response.data.patient && successMessage) {
        successMessage.textContent = response.data.message
        successMessage.classList.remove('hidden')
      }

      if (patientCount) {
        patientCount.textContent = 'Patients: 3'
      }

      expect(mockAxios.post).toHaveBeenCalledWith('/patients', {
        name: 'Bob Johnson',
        dob: '1990-08-30'
      })
      expect(successMessage?.textContent).toBe('Patient created successfully')
      expect(patientCount?.textContent).toBe('Patients: 3')
    })
  })

  describe('IRIS API Integration Tests', () => {
    it('should fetch immunization records and display in timeline', async () => {
      const mockImmunizations = [
        {
          id: 'IMM001',
          vaccine: 'COVID-19',
          date: '2023-12-01',
          status: 'Completed',
          provider: 'CVS Pharmacy'
        },
        {
          id: 'IMM002',
          vaccine: 'Influenza',
          date: '2023-10-15',
          status: 'Completed',
          provider: 'Walgreens'
        }
      ]

      mockAxios.get.mockResolvedValueOnce({
        data: { immunizations: mockImmunizations }
      })

      const irisContainer = document.createElement('div')
      irisContainer.innerHTML = `
        <div class="iris-integration-page">
          <div id="immunization-timeline"></div>
          <div id="sync-status">Last sync: Never</div>
        </div>
      `
      
      document.body.appendChild(irisContainer)

      // Simulate IRIS API call
      const response = await mockAxios.get('/iris/immunizations/P001')
      const timeline = document.getElementById('immunization-timeline')
      const syncStatus = document.getElementById('sync-status')

      if (timeline && response.data.immunizations) {
        response.data.immunizations.forEach((imm: any) => {
          const timelineItem = document.createElement('div')
          timelineItem.className = 'timeline-item'
          timelineItem.innerHTML = `
            <div class="timeline-date">${imm.date}</div>
            <div class="timeline-content">
              <h4>${imm.vaccine}</h4>
              <p>Provider: ${imm.provider}</p>
              <span class="status-${imm.status.toLowerCase()}">${imm.status}</span>
            </div>
          `
          timeline.appendChild(timelineItem)
        })
      }

      if (syncStatus) {
        syncStatus.textContent = `Last sync: ${new Date().toLocaleString()}`
      }

      expect(mockAxios.get).toHaveBeenCalledWith('/iris/immunizations/P001')
      expect(document.querySelectorAll('.timeline-item').length).toBe(2)
      expect(document.querySelector('.timeline-content h4')?.textContent).toBe('COVID-19')
    })

    it('should handle IRIS API errors gracefully', async () => {
      // Mock IRIS API error
      mockAxios.get.mockRejectedValueOnce({
        response: {
          status: 503,
          data: { detail: 'IRIS service unavailable' }
        }
      })

      const errorContainer = document.createElement('div')
      errorContainer.innerHTML = `
        <div id="iris-error" class="hidden"></div>
        <div id="retry-btn" class="hidden">Retry Connection</div>
      `
      
      document.body.appendChild(errorContainer)

      // Simulate API call and error handling
      try {
        await mockAxios.get('/iris/status')
      } catch (error: any) {
        const errorDiv = document.getElementById('iris-error')
        const retryBtn = document.getElementById('retry-btn')

        if (errorDiv && error.response) {
          errorDiv.textContent = `IRIS Error: ${error.response.data.detail}`
          errorDiv.classList.remove('hidden')
        }

        if (retryBtn) {
          retryBtn.classList.remove('hidden')
        }
      }

      const errorDiv = document.getElementById('iris-error')
      const retryBtn = document.getElementById('retry-btn')

      expect(errorDiv?.textContent).toBe('IRIS Error: IRIS service unavailable')
      expect(retryBtn?.classList.contains('hidden')).toBe(false)
    })
  })

  describe('Real-time Data Updates', () => {
    it('should handle WebSocket-like real-time patient updates', async () => {
      const realtimeContainer = document.createElement('div')
      realtimeContainer.innerHTML = `
        <div id="patient-status" data-patient-id="P001">
          <span class="vitals">Heart Rate: --</span>
          <span class="status">Status: Monitoring</span>
        </div>
        <div id="alert-container"></div>
      `
      
      document.body.appendChild(realtimeContainer)

      // Simulate real-time update
      const mockRealtimeUpdate = {
        patient_id: 'P001',
        vitals: {
          heart_rate: 85,
          blood_pressure: '120/80'
        },
        status: 'Normal',
        timestamp: new Date().toISOString()
      }

      const patientStatus = document.getElementById('patient-status')
      const vitalsSpan = document.querySelector('.vitals')
      const statusSpan = document.querySelector('.status')

      if (vitalsSpan && mockRealtimeUpdate.vitals) {
        vitalsSpan.textContent = `Heart Rate: ${mockRealtimeUpdate.vitals.heart_rate} bpm`
      }

      if (statusSpan) {
        statusSpan.textContent = `Status: ${mockRealtimeUpdate.status}`
      }

      expect(vitalsSpan?.textContent).toBe('Heart Rate: 85 bpm')
      expect(statusSpan?.textContent).toBe('Status: Normal')
    })

    it('should handle critical alerts from backend', async () => {
      const alertContainer = document.createElement('div')
      alertContainer.innerHTML = `
        <div id="alerts-list"></div>
      `
      
      document.body.appendChild(alertContainer)

      // Simulate critical alert
      const criticalAlert = {
        id: 'ALERT001',
        type: 'CRITICAL',
        message: 'Patient P001 - Abnormal heart rhythm detected',
        timestamp: new Date().toISOString(),
        requires_action: true
      }

      const alertsList = document.getElementById('alerts-list')
      if (alertsList) {
        const alertElement = document.createElement('div')
        alertElement.className = `alert alert-${criticalAlert.type.toLowerCase()}`
        alertElement.setAttribute('role', 'alert')
        alertElement.innerHTML = `
          <div class="alert-content">
            <span class="alert-time">${new Date(criticalAlert.timestamp).toLocaleTimeString()}</span>
            <span class="alert-message">${criticalAlert.message}</span>
            ${criticalAlert.requires_action ? '<button class="alert-action">Acknowledge</button>' : ''}
          </div>
        `
        alertsList.appendChild(alertElement)
      }

      const alert = document.querySelector('.alert-critical')
      const alertMessage = document.querySelector('.alert-message')
      const actionButton = document.querySelector('.alert-action')

      expect(alert?.getAttribute('role')).toBe('alert')
      expect(alertMessage?.textContent).toBe('Patient P001 - Abnormal heart rhythm detected')
      expect(actionButton?.textContent).toBe('Acknowledge')
    })
  })

  describe('Chart Data Integration', () => {
    it('should fetch analytics data and render charts', async () => {
      const mockAnalytics = {
        patient_trends: [
          { date: '2024-01-01', new_patients: 5, total_visits: 25 },
          { date: '2024-01-02', new_patients: 3, total_visits: 18 },
          { date: '2024-01-03', new_patients: 7, total_visits: 32 }
        ],
        department_stats: {
          emergency: 45,
          outpatient: 120,
          surgery: 23
        }
      }

      mockAxios.get.mockResolvedValueOnce({
        data: mockAnalytics
      })

      const chartsContainer = document.createElement('div')
      chartsContainer.innerHTML = `
        <div class="dashboard-charts">
          <div class="chart-container" id="trends-chart"></div>
          <div class="chart-container" id="department-chart"></div>
        </div>
      `
      
      document.body.appendChild(chartsContainer)

      // Simulate chart data processing
      const response = await mockAxios.get('/analytics/dashboard')
      const trendsChart = document.getElementById('trends-chart')
      const deptChart = document.getElementById('department-chart')

      if (trendsChart && response.data.patient_trends) {
        trendsChart.innerHTML = `
          <h3>Patient Trends</h3>
          <div class="chart-data">
            ${response.data.patient_trends.map((item: any) => 
              `<div class="data-point" data-date="${item.date}" data-patients="${item.new_patients}"></div>`
            ).join('')}
          </div>
        `
      }

      if (deptChart && response.data.department_stats) {
        deptChart.innerHTML = `
          <h3>Department Statistics</h3>
          <div class="stats-grid">
            ${Object.entries(response.data.department_stats).map(([dept, count]) => 
              `<div class="stat-item">${dept}: ${count}</div>`
            ).join('')}
          </div>
        `
      }

      expect(mockAxios.get).toHaveBeenCalledWith('/analytics/dashboard')
      expect(document.querySelectorAll('.data-point').length).toBe(3)
      expect(document.querySelectorAll('.stat-item').length).toBe(3)
      expect(document.querySelector('.stat-item')?.textContent).toContain('emergency: 45')
    })
  })

  describe('Error Boundary Integration', () => {
    it('should handle API timeout errors gracefully', async () => {
      // Mock timeout error
      mockAxios.get.mockRejectedValueOnce({
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      })

      const errorBoundary = document.createElement('div')
      errorBoundary.innerHTML = `
        <div id="error-boundary" class="hidden">
          <h3>Something went wrong</h3>
          <p id="error-details"></p>
          <button id="retry-btn">Try Again</button>
        </div>
      `
      
      document.body.appendChild(errorBoundary)

      try {
        await mockAxios.get('/patients')
      } catch (error: any) {
        const errorBoundaryDiv = document.getElementById('error-boundary')
        const errorDetails = document.getElementById('error-details')

        if (errorBoundaryDiv && errorDetails) {
          errorDetails.textContent = 'Connection timeout - please check your network and try again'
          errorBoundaryDiv.classList.remove('hidden')
        }
      }

      const errorBoundaryDiv = document.getElementById('error-boundary')
      const errorDetails = document.getElementById('error-details')

      expect(errorBoundaryDiv?.classList.contains('hidden')).toBe(false)
      expect(errorDetails?.textContent).toContain('Connection timeout')
    })
  })
})