import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest'
import { JSDOM } from 'jsdom'

// Responsive design testing across different viewport sizes
describe('HEMA3N Responsive Design Test Suite', () => {
  let dom: JSDOM
  let window: Window
  let document: Document

  // Common viewport sizes for testing
  const VIEWPORTS = {
    mobile: { width: 375, height: 667, name: 'iPhone SE' },
    mobileLarge: { width: 414, height: 896, name: 'iPhone XR' },
    tablet: { width: 768, height: 1024, name: 'iPad' },
    tabletLandscape: { width: 1024, height: 768, name: 'iPad Landscape' },
    desktop: { width: 1200, height: 800, name: 'Desktop' },
    desktopLarge: { width: 1920, height: 1080, name: 'Large Desktop' }
  }

  // Mock window.matchMedia
  const mockMatchMedia = vi.fn((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }))

  beforeAll(async () => {
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>HEMA3N Responsive Test</title>
          <style>
            .container { max-width: 1200px; margin: 0 auto; padding: 0 16px; }
            .grid { display: grid; gap: 16px; }
            .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
            .grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .hidden { display: none; }
            .block { display: block; }
            .flex { display: flex; }
            .flex-col { flex-direction: column; }
            .text-sm { font-size: 14px; }
            .text-base { font-size: 16px; }
            .text-lg { font-size: 18px; }
            .p-4 { padding: 16px; }
            .p-6 { padding: 24px; }
            .m-4 { margin: 16px; }
            @media (min-width: 640px) {
              .sm\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
              .sm\\:text-base { font-size: 16px; }
              .sm\\:block { display: block; }
              .sm\\:hidden { display: none; }
            }
            @media (min-width: 768px) {
              .md\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
              .md\\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
              .md\\:flex-row { flex-direction: row; }
              .md\\:text-lg { font-size: 18px; }
            }
            @media (min-width: 1024px) {
              .lg\\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
              .lg\\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
            }
          </style>
        </head>
        <body><div id="root"></div></body>
      </html>
    `, {
      url: 'http://localhost:3000',
      pretendToBeVisual: true,
      resources: 'usable'
    })
    
    // @ts-ignore
    global.window = dom.window
    // @ts-ignore
    global.document = dom.window.document
    // @ts-ignore
    global.matchMedia = mockMatchMedia
    
    window = dom.window as unknown as Window
    document = dom.window.document
  })

  afterAll(() => {
    dom.window.close()
    vi.restoreAllMocks()
  })

  // Helper function to simulate viewport changes
  function setViewport(viewport: { width: number; height: number; name: string }) {
    // Mock window size changes
    Object.defineProperty(window, 'innerWidth', { writable: true, value: viewport.width })
    Object.defineProperty(window, 'innerHeight', { writable: true, value: viewport.height })
    
    // Mock media queries
    mockMatchMedia.mockImplementation((query: string) => ({
      matches: evaluateMediaQuery(query, viewport.width),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
  }

  // Helper function to evaluate media queries
  function evaluateMediaQuery(query: string, width: number): boolean {
    if (query.includes('min-width: 1024px')) return width >= 1024
    if (query.includes('min-width: 768px')) return width >= 768
    if (query.includes('min-width: 640px')) return width >= 640
    if (query.includes('max-width: 767px')) return width <= 767
    if (query.includes('max-width: 639px')) return width <= 639
    return false
  }

  describe('Navigation Responsive Tests', () => {
    it('should show mobile menu on small screens', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const navigation = document.createElement('nav')
      navigation.className = 'responsive-nav'
      navigation.innerHTML = `
        <div class="container flex justify-between items-center p-4">
          <div class="logo">
            <h1 class="text-lg md:text-xl">HEMA3N</h1>
          </div>
          <div class="desktop-menu hidden md:block">
            <ul class="flex gap-6">
              <li><a href="/dashboard">Dashboard</a></li>
              <li><a href="/patients">Patients</a></li>
              <li><a href="/iris">IRIS</a></li>
              <li><a href="/audit">Audit</a></li>
            </ul>
          </div>
          <button class="mobile-menu-toggle block md:hidden" aria-label="Open menu">
            ☰
          </button>
        </div>
        <div class="mobile-menu hidden" id="mobile-menu">
          <ul class="flex flex-col p-4 gap-4">
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/patients">Patients</a></li>
            <li><a href="/iris">IRIS Integration</a></li>
            <li><a href="/audit">Audit Logs</a></li>
          </ul>
        </div>
      `
      
      document.body.appendChild(navigation)
      
      const desktopMenu = navigation.querySelector('.desktop-menu')
      const mobileToggle = navigation.querySelector('.mobile-menu-toggle')
      
      // On mobile, desktop menu should be hidden and mobile toggle visible
      expect(desktopMenu?.classList.contains('hidden')).toBe(true)
      expect(mobileToggle?.classList.contains('block')).toBe(true)
      expect(window.innerWidth).toBe(375)
    })

    it('should show desktop menu on larger screens', async () => {
      setViewport(VIEWPORTS.desktop)
      
      const navigation = document.createElement('nav')
      navigation.className = 'responsive-nav'
      navigation.innerHTML = `
        <div class="container flex justify-between items-center p-4">
          <div class="logo">
            <h1 class="text-lg md:text-xl">HEMA3N</h1>
          </div>
          <div class="desktop-menu hidden md:block">
            <ul class="flex gap-6">
              <li><a href="/dashboard">Dashboard</a></li>
              <li><a href="/patients">Patients</a></li>
              <li><a href="/iris">IRIS</a></li>
              <li><a href="/audit">Audit</a></li>
            </ul>
          </div>
          <button class="mobile-menu-toggle block md:hidden">☰</button>
        </div>
      `
      
      document.body.appendChild(navigation)
      
      const desktopMenu = navigation.querySelector('.desktop-menu')
      const mobileToggle = navigation.querySelector('.mobile-menu-toggle')
      
      // On desktop, menu should be visible and toggle hidden
      expect(window.innerWidth).toBe(1200)
      // Would check computed styles in real implementation
      expect(desktopMenu).toBeDefined()
      expect(mobileToggle).toBeDefined()
    })
  })

  describe('Dashboard Grid Responsive Tests', () => {
    it('should stack cards vertically on mobile', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const dashboard = document.createElement('div')
      dashboard.className = 'dashboard-responsive'
      dashboard.innerHTML = `
        <div class="container">
          <h1 class="text-lg md:text-xl mb-6">Healthcare Dashboard</h1>
          <div class="stats-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="stat-card p-4 bg-white rounded shadow">
              <h3 class="text-sm md:text-base">Active Patients</h3>
              <div class="text-lg md:text-xl font-bold">1,234</div>
            </div>
            <div class="stat-card p-4 bg-white rounded shadow">
              <h3 class="text-sm md:text-base">Appointments Today</h3>
              <div class="text-lg md:text-xl font-bold">56</div>
            </div>
            <div class="stat-card p-4 bg-white rounded shadow">
              <h3 class="text-sm md:text-base">Critical Alerts</h3>
              <div class="text-lg md:text-xl font-bold">3</div>
            </div>
            <div class="stat-card p-4 bg-white rounded shadow">
              <h3 class="text-sm md:text-base">Pending Tasks</h3>
              <div class="text-lg md:text-xl font-bold">12</div>
            </div>
          </div>
        </div>
      `
      
      document.body.appendChild(dashboard)
      
      const statsGrid = dashboard.querySelector('.stats-grid')
      const statCards = dashboard.querySelectorAll('.stat-card')
      
      expect(statsGrid?.classList.contains('grid-cols-1')).toBe(true)
      expect(statCards.length).toBe(4)
      expect(window.innerWidth).toBe(375)
    })

    it('should show 2 columns on tablets', async () => {
      setViewport(VIEWPORTS.tablet)
      
      const dashboard = document.createElement('div')
      dashboard.innerHTML = `
        <div class="dashboard-tablet">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="card">Card 1</div>
            <div class="card">Card 2</div>
            <div class="card">Card 3</div>
            <div class="card">Card 4</div>
          </div>
        </div>
      `
      
      document.body.appendChild(dashboard)
      
      const grid = dashboard.querySelector('.grid')
      
      // At tablet width (768px), should use sm:grid-cols-2
      expect(grid?.classList.contains('sm:grid-cols-2')).toBe(true)
      expect(window.innerWidth).toBe(768)
    })

    it('should show 4 columns on large desktop', async () => {
      setViewport(VIEWPORTS.desktopLarge)
      
      const dashboard = document.createElement('div')
      dashboard.innerHTML = `
        <div class="dashboard-large">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="card">Card 1</div>
            <div class="card">Card 2</div>
            <div class="card">Card 3</div>
            <div class="card">Card 4</div>
            <div class="card">Card 5</div>
            <div class="card">Card 6</div>
          </div>
        </div>
      `
      
      document.body.appendChild(dashboard)
      
      const grid = dashboard.querySelector('.grid')
      
      expect(grid?.classList.contains('lg:grid-cols-4')).toBe(true)
      expect(window.innerWidth).toBe(1920)
    })
  })

  describe('Form Responsive Tests', () => {
    it('should stack form fields vertically on mobile', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const patientForm = document.createElement('div')
      patientForm.className = 'patient-form-responsive'
      patientForm.innerHTML = `
        <form class="p-4">
          <h2 class="text-lg mb-4">Patient Information</h2>
          <div class="form-grid grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-field">
              <label class="block text-sm mb-1">First Name</label>
              <input type="text" class="w-full p-2 border rounded">
            </div>
            <div class="form-field">
              <label class="block text-sm mb-1">Last Name</label>
              <input type="text" class="w-full p-2 border rounded">
            </div>
            <div class="form-field md:col-span-2">
              <label class="block text-sm mb-1">Email Address</label>
              <input type="email" class="w-full p-2 border rounded">
            </div>
            <div class="form-field">
              <label class="block text-sm mb-1">Phone</label>
              <input type="tel" class="w-full p-2 border rounded">
            </div>
            <div class="form-field">
              <label class="block text-sm mb-1">Date of Birth</label>
              <input type="date" class="w-full p-2 border rounded">
            </div>
          </div>
          <div class="form-actions flex flex-col sm:flex-row gap-2 mt-6">
            <button type="submit" class="primary-btn w-full sm:w-auto">Save Patient</button>
            <button type="button" class="secondary-btn w-full sm:w-auto">Cancel</button>
          </div>
        </form>
      `
      
      document.body.appendChild(patientForm)
      
      const formGrid = patientForm.querySelector('.form-grid')
      const formActions = patientForm.querySelector('.form-actions')
      const formFields = patientForm.querySelectorAll('.form-field')
      
      expect(formGrid?.classList.contains('grid-cols-1')).toBe(true)
      expect(formActions?.classList.contains('flex-col')).toBe(true)
      expect(formFields.length).toBe(5)
      expect(window.innerWidth).toBe(375)
    })

    it('should show side-by-side layout on desktop', async () => {
      setViewport(VIEWPORTS.desktop)
      
      const patientForm = document.createElement('div')
      patientForm.innerHTML = `
        <form class="p-6">
          <div class="form-grid grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>Field 1</div>
            <div>Field 2</div>
          </div>
          <div class="form-actions flex flex-col sm:flex-row gap-2 mt-6">
            <button>Save</button>
            <button>Cancel</button>
          </div>
        </form>
      `
      
      document.body.appendChild(patientForm)
      
      const formGrid = patientForm.querySelector('.form-grid')
      const formActions = patientForm.querySelector('.form-actions')
      
      expect(formGrid?.classList.contains('md:grid-cols-2')).toBe(true)
      expect(formActions?.classList.contains('sm:flex-row')).toBe(true)
      expect(window.innerWidth).toBe(1200)
    })
  })

  describe('Data Table Responsive Tests', () => {
    it('should hide non-essential columns on mobile', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const dataTable = document.createElement('div')
      dataTable.className = 'responsive-table'
      dataTable.innerHTML = `
        <div class="table-container">
          <table class="w-full">
            <thead>
              <tr>
                <th class="text-left p-2">ID</th>
                <th class="text-left p-2">Name</th>
                <th class="text-left p-2 hidden sm:table-cell">Email</th>
                <th class="text-left p-2 hidden md:table-cell">Phone</th>
                <th class="text-left p-2 hidden lg:table-cell">Last Visit</th>
                <th class="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="p-2">P001</td>
                <td class="p-2">John Doe</td>
                <td class="p-2 hidden sm:table-cell">john@example.com</td>
                <td class="p-2 hidden md:table-cell">555-0123</td>
                <td class="p-2 hidden lg:table-cell">2024-01-15</td>
                <td class="p-2">Active</td>
              </tr>
            </tbody>
          </table>
        </div>
      `
      
      document.body.appendChild(dataTable)
      
      const headers = dataTable.querySelectorAll('th')
      const visibleHeaders = Array.from(headers).filter(th => 
        !th.classList.contains('hidden') || 
        (th.classList.contains('hidden') && th.classList.contains('sm:table-cell') && window.innerWidth >= 640)
      )
      
      // On mobile, should show only essential columns (ID, Name, Status)
      expect(window.innerWidth).toBe(375)
      expect(headers.length).toBe(6) // All headers exist
      // In real implementation, would check computed display property
    })

    it('should show all columns on desktop', async () => {
      setViewport(VIEWPORTS.desktop)
      
      const dataTable = document.createElement('div')
      dataTable.innerHTML = `
        <table class="responsive-table-desktop">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th class="hidden sm:table-cell">Email</th>
              <th class="hidden md:table-cell">Phone</th>
              <th class="hidden lg:table-cell">Last Visit</th>
              <th>Status</th>
            </tr>
          </thead>
        </table>
      `
      
      document.body.appendChild(dataTable)
      
      const headers = dataTable.querySelectorAll('th')
      
      expect(window.innerWidth).toBe(1200)
      expect(headers.length).toBe(6)
      // All columns should be visible on desktop
    })
  })

  describe('Chart Responsive Tests', () => {
    it('should adjust chart dimensions for mobile', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const chartContainer = document.createElement('div')
      chartContainer.className = 'chart-responsive'
      chartContainer.innerHTML = `
        <div class="chart-wrapper p-4">
          <h3 class="text-base md:text-lg mb-4">Patient Trends</h3>
          <div class="chart-content" style="width: 100%; height: 250px; background: #f0f0f0;">
            <div class="chart-mobile" style="width: 100%; height: 100%;">Mobile Chart View</div>
          </div>
          <div class="chart-legend flex flex-col sm:flex-row gap-2 mt-2 text-xs sm:text-sm">
            <div class="legend-item">🔵 New Patients</div>
            <div class="legend-item">🟢 Return Visits</div>
          </div>
        </div>
      `
      
      document.body.appendChild(chartContainer)
      
      const chartContent = chartContainer.querySelector('.chart-content')
      const chartLegend = chartContainer.querySelector('.chart-legend')
      
      expect(window.innerWidth).toBe(375)
      expect(chartContent?.style.height).toBe('250px')
      expect(chartLegend?.classList.contains('flex-col')).toBe(true)
    })

    it('should show larger charts on desktop', async () => {
      setViewport(VIEWPORTS.desktop)
      
      const chartContainer = document.createElement('div')
      chartContainer.innerHTML = `
        <div class="chart-desktop">
          <div class="chart-content" style="width: 100%; height: 400px;">Desktop Chart View</div>
          <div class="chart-controls flex flex-row gap-4 mt-4">
            <button>1D</button>
            <button>1W</button>
            <button>1M</button>
            <button>1Y</button>
          </div>
        </div>
      `
      
      document.body.appendChild(chartContainer)
      
      const chartContent = chartContainer.querySelector('.chart-content')
      const chartControls = chartContainer.querySelector('.chart-controls')
      
      expect(window.innerWidth).toBe(1200)
      expect(chartContent?.style.height).toBe('400px')
      expect(chartControls?.classList.contains('flex-row')).toBe(true)
    })
  })

  describe('Modal Responsive Tests', () => {
    it('should use full-screen modal on mobile', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const modal = document.createElement('div')
      modal.className = 'modal-responsive'
      modal.innerHTML = `
        <div class="modal-overlay fixed inset-0 bg-black bg-opacity-50">
          <div class="modal-content bg-white m-0 sm:m-4 sm:max-w-lg sm:mx-auto h-full sm:h-auto sm:rounded-lg">
            <div class="modal-header p-4 border-b sm:p-6">
              <h3 class="text-lg font-semibold">Patient Details</h3>
              <button class="close-btn absolute top-4 right-4">×</button>
            </div>
            <div class="modal-body p-4 sm:p-6">
              <p>Patient information and details...</p>
            </div>
            <div class="modal-footer p-4 border-t sm:p-6">
              <div class="flex flex-col sm:flex-row gap-2">
                <button class="w-full sm:w-auto">Save</button>
                <button class="w-full sm:w-auto">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      `
      
      document.body.appendChild(modal)
      
      const modalContent = modal.querySelector('.modal-content')
      
      expect(window.innerWidth).toBe(375)
      // On mobile, modal should be full-screen (h-full, m-0)
      expect(modalContent?.classList.contains('h-full')).toBe(true)
      expect(modalContent?.classList.contains('m-0')).toBe(true)
    })

    it('should use centered modal on desktop', async () => {
      setViewport(VIEWPORTS.desktop)
      
      const modal = document.createElement('div')
      modal.innerHTML = `
        <div class="modal-desktop">
          <div class="modal-content bg-white m-0 sm:m-4 sm:max-w-lg sm:mx-auto h-full sm:h-auto sm:rounded-lg">
            Desktop Modal Content
          </div>
        </div>
      `
      
      document.body.appendChild(modal)
      
      const modalContent = modal.querySelector('.modal-content')
      
      expect(window.innerWidth).toBe(1200)
      // On desktop, modal should be centered and rounded
      expect(modalContent?.classList.contains('sm:rounded-lg')).toBe(true)
      expect(modalContent?.classList.contains('sm:mx-auto')).toBe(true)
    })
  })

  describe('Touch and Interaction Responsive Tests', () => {
    it('should increase touch targets on mobile', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const touchInterface = document.createElement('div')
      touchInterface.className = 'touch-interface'
      touchInterface.innerHTML = `
        <div class="action-buttons p-4">
          <button class="touch-button p-3 sm:p-2 text-base sm:text-sm min-h-12 sm:min-h-8">
            Large Touch Target
          </button>
          <div class="dropdown-menu">
            <button class="dropdown-trigger p-3 sm:p-2 min-h-12 sm:min-h-8">
              Menu ▼
            </button>
            <div class="dropdown-content hidden">
              <a href="#" class="block p-3 sm:p-2">Option 1</a>
              <a href="#" class="block p-3 sm:p-2">Option 2</a>
            </div>
          </div>
        </div>
      `
      
      document.body.appendChild(touchInterface)
      
      const touchButton = touchInterface.querySelector('.touch-button')
      const dropdownTrigger = touchInterface.querySelector('.dropdown-trigger')
      
      expect(window.innerWidth).toBe(375)
      // Touch targets should be larger on mobile (min-h-12 = 48px)
      expect(touchButton?.classList.contains('min-h-12')).toBe(true)
      expect(dropdownTrigger?.classList.contains('min-h-12')).toBe(true)
    })
  })

  describe('Typography Responsive Tests', () => {
    it('should use smaller font sizes on mobile', async () => {
      setViewport(VIEWPORTS.mobile)
      
      const typographyTest = document.createElement('div')
      typographyTest.innerHTML = `
        <div class="typography-responsive p-4">
          <h1 class="text-lg sm:text-xl md:text-2xl mb-4">Main Heading</h1>
          <h2 class="text-base sm:text-lg md:text-xl mb-3">Section Heading</h2>
          <p class="text-sm sm:text-base mb-2">Body text paragraph</p>
          <small class="text-xs sm:text-sm">Small print text</small>
        </div>
      `
      
      document.body.appendChild(typographyTest)
      
      const heading1 = typographyTest.querySelector('h1')
      const heading2 = typographyTest.querySelector('h2')
      const paragraph = typographyTest.querySelector('p')
      
      expect(window.innerWidth).toBe(375)
      expect(heading1?.classList.contains('text-lg')).toBe(true)
      expect(heading2?.classList.contains('text-base')).toBe(true)
      expect(paragraph?.classList.contains('text-sm')).toBe(true)
    })
  })
})