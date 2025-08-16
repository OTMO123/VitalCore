# Core Functionality Development Roadmap

## 🎯 Current Focus: Working System with Complete Features

**Objective**: Build fully functional healthcare system with all core features working end-to-end, with security foundation ready for future expansion.

## 📊 Current System Analysis

### **✅ What's Working Well**
- **Backend Foundation**: FastAPI + PostgreSQL + Redis architecture
- **Security Infrastructure**: JWT authentication, PHI encryption, audit logging
- **Frontend Structure**: React + TypeScript with component library
- **API Integration**: Axios client with token refresh and error handling

### **🔧 What Needs Completion**

#### **Backend Core Functionality Gaps**
1. **Patient Management**: Complete CRUD operations with PHI handling
2. **Document Management**: File upload, processing, and retrieval
3. **Healthcare Records**: Complete medical record management
4. **IRIS API Integration**: Full integration with external healthcare APIs
5. **Dashboard Data**: Real-time metrics and healthcare analytics
6. **User Management**: Complete user lifecycle management

#### **Frontend Integration Gaps**
1. **Data Flow**: Components not fully connected to backend APIs
2. **State Management**: Redux store not fully integrated
3. **Real-time Updates**: WebSocket or polling for live data
4. **File Handling**: Document upload and preview functionality
5. **Error Handling**: User-friendly error states and recovery
6. **Loading States**: Proper loading indicators and skeleton screens

## 🚀 Development Strategy

### **Phase 1: Complete Core Backend APIs (Week 1-2)**

#### **1.1 Patient Management API - Complete Implementation**

**Current State**: Basic structure exists
**Goal**: Full CRUD with PHI protection

```python
# app/modules/healthcare_records/service.py - Enhanced Implementation

class PatientService:
    def __init__(self, 
                 repository: PatientRepository,
                 encryption_service: EncryptionService,
                 audit_service: AuditService):
        self.repository = repository
        self.encryption = encryption_service
        self.audit = audit_service
    
    async def create_patient(self, patient_data: CreatePatientRequest, user_id: str) -> Patient:
        """Create new patient with PHI encryption and audit logging"""
        # Validate and encrypt PHI fields
        encrypted_data = await self._encrypt_phi_fields(patient_data.dict())
        
        # Create patient record
        patient = await self.repository.create(encrypted_data)
        
        # Log creation for audit
        await self.audit.log_patient_creation(patient.id, user_id)
        
        return patient
    
    async def get_patient(self, patient_id: str, user_id: str, 
                         purpose: str = "treatment") -> Patient:
        """Get patient with access control and audit logging"""
        # Validate access permissions
        await self._validate_patient_access(patient_id, user_id, purpose)
        
        # Get encrypted patient data
        patient = await self.repository.get_by_id(patient_id)
        
        # Decrypt PHI fields for authorized access
        decrypted_data = await self._decrypt_phi_fields(patient)
        
        # Log PHI access for audit
        await self.audit.log_phi_access(patient_id, user_id, purpose)
        
        return decrypted_data
    
    async def update_patient(self, patient_id: str, updates: UpdatePatientRequest, 
                           user_id: str) -> Patient:
        """Update patient with change tracking and audit"""
        # Get current patient for change tracking
        current_patient = await self.repository.get_by_id(patient_id)
        
        # Encrypt updated PHI fields
        encrypted_updates = await self._encrypt_phi_fields(updates.dict(exclude_unset=True))
        
        # Update patient record
        updated_patient = await self.repository.update(patient_id, encrypted_updates)
        
        # Log changes for audit
        await self.audit.log_patient_update(patient_id, user_id, 
                                          self._get_changed_fields(current_patient, encrypted_updates))
        
        return updated_patient
    
    async def list_patients(self, user_id: str, filters: PatientFilters = None, 
                          page: int = 1, size: int = 20) -> PaginatedPatients:
        """List patients with role-based filtering"""
        # Apply role-based access filters
        access_filters = await self._get_user_access_filters(user_id)
        
        # Combine with user filters
        combined_filters = self._combine_filters(filters, access_filters)
        
        # Get paginated results
        patients = await self.repository.list_with_filters(combined_filters, page, size)
        
        # Decrypt only necessary fields for list view
        for patient in patients.items:
            patient.phi_fields = await self._decrypt_list_fields(patient.phi_fields)
        
        return patients

# TDD Test Example
@pytest.mark.asyncio
async def test_create_patient_encrypts_phi_data():
    """Test that patient creation properly encrypts PHI data"""
    # Arrange
    patient_data = CreatePatientRequest(
        first_name="John",
        last_name="Doe", 
        ssn="123-45-6789",
        date_of_birth="1990-01-01"
    )
    
    # Act
    patient = await patient_service.create_patient(patient_data, "user123")
    
    # Assert - PHI fields should be encrypted in database
    db_patient = await patient_repository.get_raw_by_id(patient.id)
    assert is_encrypted(db_patient.ssn)
    assert is_encrypted(db_patient.first_name)
    assert is_encrypted(db_patient.last_name)
    
    # Assert - Audit log should contain creation event
    audit_logs = await audit_service.get_logs_for_patient(patient.id)
    assert any(log.event_type == "PATIENT_CREATED" for log in audit_logs)
```

#### **1.2 Document Management API - File Handling**

```python
# app/modules/document_management/service.py - Core Implementation

class DocumentService:
    def __init__(self, 
                 storage_backend: StorageBackend,
                 classification_service: DocumentClassificationService):
        self.storage = storage_backend
        self.classifier = classification_service
    
    async def upload_document(self, file: UploadFile, patient_id: str, 
                            user_id: str) -> DocumentRecord:
        """Upload and process document with automatic classification"""
        # Validate file type and size
        await self._validate_file(file)
        
        # Auto-classify document type
        classification = await self.classifier.classify_document(file)
        
        # Generate secure filename and store file
        secure_filename = await self._generate_secure_filename(file.filename)
        file_path = await self.storage.store_file(file, secure_filename)
        
        # Create document record
        document = await self._create_document_record(
            file_path, classification, patient_id, user_id
        )
        
        # Extract text for search (if applicable)
        if classification.is_text_document:
            extracted_text = await self._extract_text(file_path)
            document.searchable_content = await self._encrypt_content(extracted_text)
        
        return document
    
    async def get_document(self, document_id: str, user_id: str) -> DocumentResponse:
        """Get document with access control"""
        # Validate access permissions
        document = await self.repository.get_by_id(document_id)
        await self._validate_document_access(document, user_id)
        
        # Get file content
        file_content = await self.storage.get_file(document.file_path)
        
        # Log document access
        await self.audit.log_document_access(document_id, user_id)
        
        return DocumentResponse(
            document=document,
            content=file_content,
            download_url=await self._generate_download_url(document_id)
        )

# TDD Test Example
@pytest.mark.asyncio
async def test_upload_document_auto_classifies():
    """Test document upload with automatic classification"""
    # Arrange
    test_file = create_test_pdf_file()
    
    # Act
    document = await document_service.upload_document(
        test_file, "patient123", "user456"
    )
    
    # Assert
    assert document.classification.document_type is not None
    assert document.file_path.endswith('.pdf')
    assert document.patient_id == "patient123"
```

#### **1.3 Dashboard Data API - Real-time Metrics**

```python
# app/modules/dashboard/service.py - Complete Implementation

class DashboardService:
    async def get_dashboard_data(self, user_id: str, 
                               role: str) -> DashboardData:
        """Get role-based dashboard data"""
        dashboard_data = DashboardData()
        
        if role in ["admin", "super_admin"]:
            dashboard_data = await self._get_admin_dashboard(user_id)
        elif role == "physician":
            dashboard_data = await self._get_physician_dashboard(user_id)
        elif role == "nurse":
            dashboard_data = await self._get_nurse_dashboard(user_id)
        else:
            dashboard_data = await self._get_basic_dashboard(user_id)
        
        return dashboard_data
    
    async def _get_admin_dashboard(self, user_id: str) -> AdminDashboardData:
        """Admin dashboard with system-wide metrics"""
        return AdminDashboardData(
            total_patients=await self.patient_repository.count_all(),
            active_users=await self.user_repository.count_active(),
            documents_uploaded_today=await self.document_repository.count_today(),
            security_alerts=await self.security_service.get_recent_alerts(),
            system_health=await self.monitoring_service.get_health_metrics(),
            compliance_status=await self.compliance_service.get_status(),
            recent_activities=await self.audit_service.get_recent_activities(limit=10)
        )
    
    async def _get_physician_dashboard(self, user_id: str) -> PhysicianDashboardData:
        """Physician dashboard with patient-focused data"""
        # Get physician's assigned patients
        assigned_patients = await self.patient_repository.get_assigned_to_physician(user_id)
        
        return PhysicianDashboardData(
            my_patients_count=len(assigned_patients),
            upcoming_appointments=await self._get_upcoming_appointments(user_id),
            pending_documents=await self._get_pending_document_reviews(user_id),
            recent_patient_updates=await self._get_recent_patient_updates(assigned_patients),
            clinical_alerts=await self._get_clinical_alerts(assigned_patients)
        )

# Real-time updates endpoint
@router.get("/dashboard/live-updates")
async def get_live_dashboard_updates(
    current_user: User = Depends(get_current_user)
):
    """Server-sent events for real-time dashboard updates"""
    async def event_generator():
        while True:
            # Get latest dashboard data
            latest_data = await dashboard_service.get_dashboard_data(
                current_user.id, current_user.role
            )
            
            # Yield server-sent event
            yield f"data: {latest_data.json()}\n\n"
            
            # Wait 30 seconds before next update
            await asyncio.sleep(30)
    
    return StreamingResponse(event_generator(), media_type="text/plain")
```

### **Phase 2: Frontend Integration & Data Flow (Week 2-3)**

#### **2.1 Complete Redux Integration**

```typescript
// frontend/src/store/slices/patientSlice.ts - Enhanced Implementation

interface PatientState {
  patients: Patient[];
  currentPatient: Patient | null;
  loading: boolean;
  error: string | null;
  filters: PatientFilters;
  pagination: PaginationInfo;
}

const patientSlice = createSlice({
  name: 'patient',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.loading = false;
    },
    setPatientsSuccess: (state, action) => {
      state.patients = action.payload.patients;
      state.pagination = action.payload.pagination;
      state.loading = false;
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPatients.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPatients.fulfilled, (state, action) => {
        state.patients = action.payload.patients;
        state.pagination = action.payload.pagination;
        state.loading = false;
      })
      .addCase(fetchPatients.rejected, (state, action) => {
        state.error = action.error.message || 'Failed to fetch patients';
        state.loading = false;
      });
  }
});

// Async thunks for API calls
export const fetchPatients = createAsyncThunk(
  'patient/fetchPatients',
  async (params: { page?: number; filters?: PatientFilters }) => {
    const response = await patientService.getPatients(params);
    return response.data;
  }
);

export const createPatient = createAsyncThunk(
  'patient/createPatient',
  async (patientData: CreatePatientRequest) => {
    const response = await patientService.createPatient(patientData);
    return response.data;
  }
);
```

#### **2.2 Component Integration with Backend**

```typescript
// frontend/src/components/patient/PatientListPage.tsx - Complete Implementation

const PatientListPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { 
    patients, 
    loading, 
    error, 
    pagination, 
    filters 
  } = useAppSelector(state => state.patient);

  // Fetch patients on component mount and filter changes
  useEffect(() => {
    dispatch(fetchPatients({ 
      page: pagination.currentPage, 
      filters 
    }));
  }, [dispatch, pagination.currentPage, filters]);

  const handlePatientCreate = async (patientData: CreatePatientRequest) => {
    try {
      await dispatch(createPatient(patientData)).unwrap();
      // Show success message
      toast.success('Patient created successfully');
      // Refresh patient list
      dispatch(fetchPatients({ page: 1, filters }));
    } catch (error) {
      toast.error('Failed to create patient');
    }
  };

  const handleFilterChange = (newFilters: PatientFilters) => {
    dispatch(setFilters(newFilters));
    // Reset to first page when filters change
    dispatch(fetchPatients({ page: 1, filters: newFilters }));
  };

  if (loading && patients.length === 0) {
    return <PatientListSkeleton />;
  }

  if (error) {
    return (
      <ErrorState 
        message={error}
        onRetry={() => dispatch(fetchPatients({ page: pagination.currentPage, filters }))}
      />
    );
  }

  return (
    <div className="patient-list-page">
      <PageHeader 
        title="Patients"
        action={
          <CreatePatientButton onSubmit={handlePatientCreate} />
        }
      />
      
      <PatientFilters 
        filters={filters}
        onFiltersChange={handleFilterChange}
      />
      
      <PatientTable 
        patients={patients}
        loading={loading}
        onPatientClick={(patient) => navigate(`/patients/${patient.id}`)}
      />
      
      <Pagination 
        {...pagination}
        onPageChange={(page) => dispatch(fetchPatients({ page, filters }))}
      />
    </div>
  );
};
```

#### **2.3 Real-time Dashboard Implementation**

```typescript
// frontend/src/components/dashboard/LiveDashboard.tsx

const LiveDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [connected, setConnected] = useState(false);
  const { user } = useAppSelector(state => state.auth);

  useEffect(() => {
    // Initial data load
    loadDashboardData();

    // Setup real-time updates via Server-Sent Events
    const eventSource = new EventSource('/api/v1/dashboard/live-updates', {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`
      }
    });

    eventSource.onopen = () => {
      setConnected(true);
    };

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setDashboardData(data);
    };

    eventSource.onerror = () => {
      setConnected(false);
      // Fallback to polling
      setupPolling();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await dashboardService.getDashboardData();
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  if (!dashboardData) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="live-dashboard">
      <DashboardHeader 
        connected={connected}
        lastUpdate={dashboardData.lastUpdated}
      />
      
      <DashboardGrid>
        {user?.role === 'admin' && (
          <AdminDashboardCards data={dashboardData as AdminDashboardData} />
        )}
        
        {user?.role === 'physician' && (
          <PhysicianDashboardCards data={dashboardData as PhysicianDashboardData} />
        )}
        
        <RecentActivitiesCard activities={dashboardData.recentActivities} />
        <SystemHealthCard health={dashboardData.systemHealth} />
      </DashboardGrid>
    </div>
  );
};
```

### **Phase 3: File Handling & Document Management (Week 3-4)**

#### **3.1 File Upload Component**

```typescript
// frontend/src/components/documents/DocumentUpload.tsx

const DocumentUpload: React.FC<{ patientId: string }> = ({ patientId }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileUpload = async (files: FileList) => {
    setUploading(true);
    setUploadProgress(0);

    try {
      for (const file of Array.from(files)) {
        await uploadFileWithProgress(file, patientId, (progress) => {
          setUploadProgress(progress);
        });
      }
      
      toast.success('Documents uploaded successfully');
      // Refresh document list
      await refetchDocuments();
    } catch (error) {
      toast.error('Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <DropZone 
      onDrop={handleFileUpload}
      disabled={uploading}
      accept={{
        'application/pdf': ['.pdf'],
        'image/*': ['.jpg', '.jpeg', '.png'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
      }}
    >
      {uploading ? (
        <UploadProgress progress={uploadProgress} />
      ) : (
        <UploadPrompt />
      )}
    </DropZone>
  );
};

// File upload service with progress
const uploadFileWithProgress = (
  file: File, 
  patientId: string, 
  onProgress: (progress: number) => void
): Promise<DocumentRecord> => {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const progress = (event.loaded / event.total) * 100;
        onProgress(progress);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);
        resolve(response);
      } else {
        reject(new Error('Upload failed'));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Upload error'));
    });

    xhr.open('POST', '/api/v1/documents/upload');
    xhr.setRequestHeader('Authorization', `Bearer ${getAccessToken()}`);
    xhr.send(formData);
  });
};
```

## 🎯 Implementation Priorities

### **Week 1: Backend API Completion**
1. **Day 1-2**: Complete Patient API with all CRUD operations
2. **Day 3-4**: Document Management API with file upload/download
3. **Day 5**: Dashboard data API with role-based responses
4. **Day 6-7**: Integration testing and bug fixes

### **Week 2: Frontend Data Integration**
1. **Day 1-2**: Redux store integration for all modules
2. **Day 3-4**: Component-API integration with error handling
3. **Day 5**: Real-time dashboard implementation
4. **Day 6-7**: UI polish and user experience improvements

### **Week 3: File Handling & Polish**
1. **Day 1-2**: File upload/download functionality
2. **Day 3-4**: Document preview and management
3. **Day 5**: Performance optimization
4. **Day 6-7**: End-to-end testing and bug fixes

### **Week 4: Production Readiness**
1. **Day 1-2**: Error handling and edge cases
2. **Day 3-4**: Performance testing and optimization
3. **Day 5**: Security testing and validation
4. **Day 6-7**: Documentation and deployment preparation

## 🧪 Testing Strategy

### **TDD for New Features**
```python
# Example TDD cycle for patient search
@pytest.mark.asyncio
async def test_patient_search_by_name():
    """Test patient search functionality"""
    # Arrange
    await create_test_patients()
    search_query = "John"
    
    # Act
    results = await patient_service.search_patients(
        query=search_query,
        user_id="physician123"
    )
    
    # Assert
    assert len(results) > 0
    assert all("john" in patient.full_name.lower() for patient in results)

@pytest.mark.asyncio
async def test_patient_search_respects_access_control():
    """Test that search respects user access permissions"""
    # Arrange
    nurse_user = create_test_nurse()
    restricted_patient = create_test_patient(restricted=True)
    
    # Act
    results = await patient_service.search_patients(
        query=restricted_patient.name,
        user_id=nurse_user.id
    )
    
    # Assert - nurse shouldn't see restricted patients
    assert restricted_patient.id not in [p.id for p in results]
```

### **Frontend Component Testing**
```typescript
// PatientList.test.tsx
describe('PatientList Component', () => {
  it('should load and display patients', async () => {
    const mockPatients = createMockPatients();
    
    render(
      <Provider store={mockStore}>
        <PatientList />
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('should handle loading states', () => {
    const loadingStore = createMockStore({ loading: true });
    
    render(
      <Provider store={loadingStore}>
        <PatientList />
      </Provider>
    );

    expect(screen.getByTestId('patient-list-skeleton')).toBeInTheDocument();
  });
});
```

## 🔧 Development Tools & Commands

### **Backend Development**
```bash
# Run development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests with coverage
pytest app/tests/ -v --cov=app --cov-report=html

# Run specific test module
pytest app/tests/modules/healthcare_records/ -v

# Database migrations
alembic revision --autogenerate -m "Add new fields"
alembic upgrade head
```

### **Frontend Development**
```bash
# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Type checking
npm run type-check
```

## 📋 Definition of Done

### **Backend Feature Complete When:**
- [ ] All CRUD operations implemented and tested
- [ ] API endpoints documented with OpenAPI
- [ ] Error handling implemented
- [ ] Audit logging integrated
- [ ] Security controls validated
- [ ] Unit tests >90% coverage
- [ ] Integration tests pass

### **Frontend Feature Complete When:**
- [ ] Component renders without errors
- [ ] Redux integration working
- [ ] Error states handled gracefully
- [ ] Loading states implemented
- [ ] Responsive design works
- [ ] Component tests pass
- [ ] TypeScript types complete

### **Integration Complete When:**
- [ ] Frontend-backend communication works
- [ ] Real-time updates functioning
- [ ] File upload/download works
- [ ] Authentication flow complete
- [ ] Error handling end-to-end
- [ ] Performance meets targets
- [ ] Security validation passes

---

**Focus**: Build working features first, ensure security foundation is solid, prepare for future security enhancements without over-engineering current implementation.