# VitalCore Flutter App - Architecture & Design Document

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Flutter App Architecture](#flutter-app-architecture)
4. [Screen-by-Screen Design](#screen-by-screen-design)
5. [Data Flow & State Management](#data-flow--state-management)
6. [API Integration Strategy](#api-integration-strategy)
7. [Security & Compliance](#security--compliance)
8. [UI/UX Design Guidelines](#uiux-design-guidelines)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

### Current Technology Stack
- **Frontend:** React 18.2 + TypeScript + Vite
- **Backend:** FastAPI (Python) with REST API
- **API Base:** `http://localhost:8000/api/v1`
- **Authentication:** JWT (access + refresh tokens)
- **Compliance:** HIPAA, SOC2 Type II, FHIR R4, GDPR

### Migration Strategy
**Recommended Approach:** Hybrid Architecture
- **Keep React Web App:** For desktop/browser access
- **Build Flutter Mobile App:** For iOS/Android with same FastAPI backend
- **Shared Backend:** Both frontends consume the same REST API

### Benefits
✅ Cross-platform mobile support (iOS + Android)
✅ Native mobile performance
✅ Single codebase for mobile platforms
✅ Reuse existing FastAPI backend
✅ No disruption to web users
✅ HIPAA compliance with secure storage

---

## Current State Analysis

### React Frontend Pages (Total: 20+ screens)

#### Authentication
1. **LoginPage** - User authentication with OAuth2
2. **RegisterPage** - New user registration

#### Dashboard
3. **DashboardPage** - Role-based dashboard (Admin/Doctor/Patient views)

#### Patient Management
4. **PatientListPage** - Advanced patient search and list
5. **PatientDetailPage** - Individual patient record view
6. **PatientFormPage** - Create/edit patient with FHIR R4 validation
7. **SymptomInputPage** - AI-powered symptom analysis with voice input

#### Healthcare Records
8. **HealthcareRecordsPage** - Clinical documents, FHIR validation, anonymization

#### Document Management
9. **DocumentManagementPage** - Upload, search, AI classification

#### IRIS Integration
10. **IRISIntegrationPage** - External API sync, health monitoring

#### Doctor Interface
11. **DoctorHistoryPage** - Medical history visualization
12. **DoctorTimelinePage** - GitBranch timeline visualization

#### Audit & Compliance
13. **AuditLogsPage** - Comprehensive audit trail
14. **CompliancePage** - HIPAA/SOC2/ISO 27001 compliance dashboard

#### AI & Analytics
15. **AIAgentsPage** - AI deployment and monitoring (Admin only)

#### Settings
16. **SettingsPage** - User and system configuration

### API Endpoints (100+ endpoints across 11 modules)
- **auth:** `/api/v1/auth/*` - 15+ endpoints
- **dashboard:** `/api/v1/dashboard/*` - 10+ endpoints
- **healthcare_records:** `/api/v1/healthcare/*` - 25+ endpoints
- **analytics:** `/api/v1/analytics/*` - 8+ endpoints
- **document_management:** `/api/v1/documents/*` - 3+ endpoints
- **iris_api:** `/api/v1/iris/*` - 12+ endpoints
- **audit_logger:** `/api/v1/audit-logs/*` - 12+ endpoints
- **clinical_workflows:** `/api/v1/clinical-workflows/*` - 10+ endpoints
- **ml_prediction:** `/api/v1/ml-prediction/*` - 6+ endpoints
- **risk_stratification:** `/api/v1/patients/risk/*` - 6+ endpoints
- **data_anonymization:** `/api/v1/ml-anonymization/*` - 9+ endpoints

---

## Flutter App Architecture

### Clean Architecture Pattern

```
lib/
├── main.dart                          # App entry point
├── core/
│   ├── constants/
│   │   ├── api_constants.dart         # API endpoints
│   │   ├── app_constants.dart         # App-wide constants
│   │   └── route_constants.dart       # Route names
│   ├── theme/
│   │   ├── app_theme.dart             # Material Design theme
│   │   ├── app_colors.dart            # Color palette
│   │   └── text_styles.dart           # Typography
│   ├── utils/
│   │   ├── validators.dart            # Form validators
│   │   ├── formatters.dart            # Data formatters
│   │   ├── date_utils.dart            # Date utilities
│   │   └── encryption_utils.dart      # PHI encryption helpers
│   ├── errors/
│   │   ├── exceptions.dart            # Custom exceptions
│   │   └── failures.dart              # Error handling
│   └── network/
│       ├── dio_client.dart            # HTTP client setup
│       ├── api_interceptor.dart       # Request/response interceptors
│       └── network_info.dart          # Connectivity check
├── data/
│   ├── models/
│   │   ├── user_model.dart
│   │   ├── patient_model.dart
│   │   ├── dashboard_model.dart
│   │   ├── clinical_document_model.dart
│   │   └── ... (30+ models)
│   ├── repositories/
│   │   ├── auth_repository.dart
│   │   ├── patient_repository.dart
│   │   ├── dashboard_repository.dart
│   │   └── ... (10+ repositories)
│   └── data_sources/
│       ├── remote/
│       │   ├── auth_api.dart
│       │   ├── patient_api.dart
│       │   └── ... (10+ API clients)
│       └── local/
│           ├── secure_storage.dart    # Token storage
│           └── cache_manager.dart     # Offline caching
├── domain/
│   ├── entities/
│   │   ├── user.dart
│   │   ├── patient.dart
│   │   ├── dashboard_stats.dart
│   │   └── ... (30+ entities)
│   ├── repositories/
│   │   └── ... (repository interfaces)
│   └── usecases/
│       ├── auth/
│       │   ├── login_usecase.dart
│       │   ├── logout_usecase.dart
│       │   └── refresh_token_usecase.dart
│       ├── patient/
│       │   ├── get_patients_usecase.dart
│       │   ├── create_patient_usecase.dart
│       │   └── ... (10+ usecases)
│       └── ... (organized by feature)
├── presentation/
│   ├── bloc/                          # State management
│   │   ├── auth/
│   │   │   ├── auth_bloc.dart
│   │   │   ├── auth_event.dart
│   │   │   └── auth_state.dart
│   │   ├── patient/
│   │   │   ├── patient_bloc.dart
│   │   │   ├── patient_event.dart
│   │   │   └── patient_state.dart
│   │   └── ... (15+ blocs)
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── login_screen.dart
│   │   │   └── register_screen.dart
│   │   ├── dashboard/
│   │   │   ├── dashboard_screen.dart
│   │   │   ├── admin_dashboard_tab.dart
│   │   │   ├── doctor_dashboard_tab.dart
│   │   │   └── patient_dashboard_tab.dart
│   │   ├── patients/
│   │   │   ├── patient_list_screen.dart
│   │   │   ├── patient_detail_screen.dart
│   │   │   ├── patient_form_screen.dart
│   │   │   └── symptom_input_screen.dart
│   │   ├── healthcare/
│   │   │   ├── healthcare_records_screen.dart
│   │   │   └── immunization_list_screen.dart
│   │   ├── documents/
│   │   │   └── document_management_screen.dart
│   │   ├── iris/
│   │   │   └── iris_integration_screen.dart
│   │   ├── audit/
│   │   │   ├── audit_logs_screen.dart
│   │   │   └── compliance_screen.dart
│   │   └── settings/
│   │       └── settings_screen.dart
│   └── widgets/
│       ├── common/
│       │   ├── custom_app_bar.dart
│       │   ├── loading_indicator.dart
│       │   ├── error_widget.dart
│       │   ├── empty_state.dart
│       │   └── custom_drawer.dart
│       ├── cards/
│       │   ├── metric_card.dart
│       │   ├── patient_card.dart
│       │   └── activity_card.dart
│       └── forms/
│           ├── custom_text_field.dart
│           ├── date_picker_field.dart
│           └── dropdown_field.dart
└── routes/
    └── app_router.dart                # Navigation setup
```

### State Management: Flutter Bloc

**Why Bloc?**
- ✅ Predictable state management
- ✅ Separation of business logic from UI
- ✅ Easy testing
- ✅ Excellent for complex apps
- ✅ Built-in error handling
- ✅ Stream-based (works well with real-time updates)

**Alternative Options:**
- **Riverpod:** Modern, more flexible (good alternative)
- **GetX:** Lightweight, less boilerplate (less structured)
- **Provider:** Simple, but less scalable for complex apps

### Key Dependencies

```yaml
dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5

  # Networking
  dio: ^5.3.3
  retrofit: ^4.0.3
  pretty_dio_logger: ^1.3.1

  # Local Storage
  flutter_secure_storage: ^9.0.0
  hive: ^2.2.3
  hive_flutter: ^1.1.0

  # JSON Serialization
  json_annotation: ^4.8.1
  freezed_annotation: ^2.4.1

  # UI Components
  google_fonts: ^6.1.0
  flutter_svg: ^2.0.9
  cached_network_image: ^3.3.0
  shimmer: ^3.0.0

  # Forms & Validation
  flutter_form_builder: ^9.1.1
  form_builder_validators: ^9.1.0

  # Charts & Visualization
  fl_chart: ^0.65.0
  syncfusion_flutter_charts: ^23.1.44

  # Date & Time
  intl: ^0.18.1
  timeago: ^3.6.0

  # Utilities
  get_it: ^7.6.4              # Dependency injection
  injectable: ^2.3.2
  logger: ^2.0.2
  connectivity_plus: ^5.0.2
  url_launcher: ^6.2.1

  # FHIR Support
  fhir: ^0.12.0              # FHIR R4 models

  # Security
  encrypt: ^5.0.3
  pointycastle: ^3.7.3

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

  # Code Generation
  build_runner: ^2.4.6
  json_serializable: ^6.7.1
  freezed: ^2.4.5
  retrofit_generator: ^8.0.4
  injectable_generator: ^2.4.1

  # Testing
  mockito: ^5.4.3
  bloc_test: ^9.1.5
```

---

## Screen-by-Screen Design

### 1. Authentication Screens

#### 1.1 Login Screen (`login_screen.dart`)

**API Endpoint:** `POST /api/v1/auth/login`

**UI Components:**
```
┌─────────────────────────────────┐
│     VitalCore Healthcare        │
│          [Logo]                 │
├─────────────────────────────────┤
│  Username                       │
│  [________________]             │
│                                 │
│  Password                       │
│  [________________] [👁]        │
│                                 │
│  [ ] Remember me                │
│                                 │
│  [    Login Button    ]         │
│                                 │
│  Forgot Password?               │
│  Create Account                 │
├─────────────────────────────────┤
│  🔒 HIPAA Compliant             │
│  🛡️ SOC2 Type II Certified      │
└─────────────────────────────────┘
```

**Data Flow:**
1. User enters credentials
2. Tap Login → `LoginEvent` to `AuthBloc`
3. AuthBloc calls `LoginUseCase`
4. LoginUseCase calls `AuthRepository.login()`
5. AuthRepository calls `AuthApi.login()`
6. Response: `TokenResponse` with access_token, refresh_token
7. Store tokens in `SecureStorage`
8. Navigate to Dashboard
9. Log audit event

**State Transitions:**
- `AuthInitial` → `AuthLoading` → `AuthAuthenticated` (success)
- `AuthInitial` → `AuthLoading` → `AuthError` (failure)

**Security Features:**
- Input sanitization
- Rate limiting (5 attempts)
- Secure token storage
- Audit logging

#### 1.2 Register Screen (`register_screen.dart`)

**API Endpoint:** `POST /api/v1/auth/register`

**Form Fields:**
- Username
- Email (validated)
- Password (strength indicator)
- Confirm Password
- Role (if allowed)
- Terms & Conditions checkbox

---

### 2. Dashboard Screen (`dashboard_screen.dart`)

**API Endpoint:** `POST /api/v1/dashboard/refresh`

**Layout:**
```
┌─────────────────────────────────────────┐
│ ☰  VitalCore    [🔔] [👤] [⚙️]         │
├─────────────────────────────────────────┤
│ Welcome, Dr. Smith                      │
│ Last login: 2 hours ago                 │
├─────────────────────────────────────────┤
│ [Admin] [Doctor] [Patient] ← Role Tabs  │
├─────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Patients │ │ Uptime   │ │Security │ │
│  │   1,247  │ │  99.9%   │ │   12    │ │
│  │  +12     │ │  30 days │ │ events  │ │
│  └──────────┘ └──────────┘ └─────────┘ │
├─────────────────────────────────────────┤
│  Recent Activities                      │
│  ┌─────────────────────────────────┐   │
│  │ 🟢 Patient created - 2m ago     │   │
│  │ 🟡 IRIS sync warning - 5m ago   │   │
│  │ 🔵 Login success - 10m ago      │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│  System Health                          │
│  Database:    ●●●●● 100%                │
│  IRIS API:    ●●●●○  80%                │
│  Encryption:  ●●●●● 100%                │
└─────────────────────────────────────────┘
```

**UI Components:**
- **AppBar:** Custom with notifications, profile, settings
- **TabBar:** Role switcher (Admin/Doctor/Patient)
- **MetricCards:** Material cards with icons, values, trends
- **ActivityFeed:** ListView with categorized activities
- **HealthIndicators:** Progress bars with status dots
- **RefreshIndicator:** Pull-to-refresh

**Data Models:**
```dart
class DashboardStats {
  final int totalPatients;
  final String totalPatientsChange;
  final double systemUptimePercentage;
  final double complianceScore;
  final Map<String, double> complianceDetails;
  final SecuritySummary securitySummary;
  final SystemHealthSummary systemHealth;
  final IRISIntegrationSummary irisIntegration;
  final DateTime lastUpdated;
}

class MetricData {
  final String title;
  final String value;
  final String change;
  final ChangeType changeType; // increase, decrease, neutral
  final IconData icon;
  final Color color;
}
```

**Real-time Updates:**
- Auto-refresh every 30 seconds
- WebSocket for critical alerts (future enhancement)
- Pull-to-refresh manual update

---

### 3. Patient Management Screens

#### 3.1 Patient List Screen (`patient_list_screen.dart`)

**API Endpoint:** `GET /api/v1/healthcare/patients`

**Layout:**
```
┌─────────────────────────────────────────┐
│ ← Patients              [+] [⚙️]        │
├─────────────────────────────────────────┤
│ 🔍 Search patients...                   │
├─────────────────────────────────────────┤
│ [All] [High Risk] [Recent] ← Filters    │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 👤 John Doe (M, 45)                 │ │
│ │    MRN: 123456 | Risk: 🔴 High     │ │
│ │    Last visit: 2 days ago           │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 👤 Jane Smith (F, 32)               │ │
│ │    MRN: 789012 | Risk: 🟢 Low      │ │
│ │    Last visit: 1 week ago           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More]                             │
└─────────────────────────────────────────┘
```

**UI Components:**
- **SearchBar:** Debounced search (500ms delay)
- **FilterChips:** Quick filters (All, High Risk, Recent)
- **PatientCard:** Custom card with avatar, info, risk badge
- **ListView.builder:** Efficient scrolling with pagination
- **FloatingActionButton:** Add new patient

**Features:**
- Infinite scroll pagination
- Real-time search
- Risk stratification color coding
- Sort by: Name, MRN, Risk, Last Visit
- Export to CSV (future)

**Query Parameters:**
- `skip`: offset for pagination
- `limit`: items per page (default 20)
- `search`: search term
- `gender`: filter by gender
- `min_age`, `max_age`: age range
- `risk_level`: filter by risk

#### 3.2 Patient Detail Screen (`patient_detail_screen.dart`)

**API Endpoint:** `GET /api/v1/healthcare/patients/{patient_id}`

**Layout:**
```
┌─────────────────────────────────────────┐
│ ←  Patient Details          [✏️] [🗑️]  │
├─────────────────────────────────────────┤
│      [Profile Photo]                    │
│      John Doe, 45 y/o Male              │
│      MRN: 123456789                     │
│      🔴 High Risk Score: 78/100         │
├─────────────────────────────────────────┤
│ [Overview][Records][Timeline][AI]       │
├─────────────────────────────────────────┤
│ Personal Information                    │
│ ┌─────────────────────────────────────┐ │
│ │ 📧 john.doe@email.com               │ │
│ │ 📱 +1 (555) 123-4567                │ │
│ │ 🏠 123 Main St, City, ST 12345      │ │
│ │ 🎂 DOB: Jan 15, 1979                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Medical Summary                         │
│ ┌─────────────────────────────────────┐ │
│ │ 💊 Medications: 3 active            │ │
│ │ ⚕️ Conditions: Hypertension, Dia... │ │
│ │ 💉 Immunizations: Up to date        │ │
│ │ 📊 Last Visit: 2 days ago           │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Tabs:**
1. **Overview:** Demographics, contact, insurance
2. **Records:** Clinical documents, lab results
3. **Timeline:** Medical history visualization
4. **AI Insights:** Risk factors, predictions

**Security:**
- PHI fields decrypted only with proper authorization
- Screen capture prevention
- Auto-lock on app background
- Audit logging for all PHI access

#### 3.3 Patient Form Screen (`patient_form_screen.dart`)

**API Endpoints:**
- Create: `POST /api/v1/healthcare/patients`
- Update: `PUT /api/v1/healthcare/patients/{id}`

**Form Sections:**
```
┌─────────────────────────────────────────┐
│ ← Create Patient           [Save]       │
├─────────────────────────────────────────┤
│ Basic Information                       │
│ ┌─────────────────────────────────────┐ │
│ │ Medical Record Number *             │ │
│ │ [________________]                  │ │
│ │                                     │ │
│ │ First Name *                        │ │
│ │ [________________]                  │ │
│ │                                     │ │
│ │ Last Name *                         │ │
│ │ [________________]                  │ │
│ │                                     │ │
│ │ Date of Birth *                     │ │
│ │ [📅 MM/DD/YYYY]                     │ │
│ │                                     │ │
│ │ Gender *                            │ │
│ │ [⌄ Select Gender]                   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Contact Information                     │
│ ┌─────────────────────────────────────┐ │
│ │ Phone Number                        │ │
│ │ [________________] 🔒               │ │
│ │                                     │ │
│ │ Email Address                       │ │
│ │ [________________] 🔒               │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Address                                 │
│ ┌─────────────────────────────────────┐ │
│ │ Street Address                      │ │
│ │ [________________] 🔒               │ │
│ │                                     │ │
│ │ City          State      ZIP        │ │
│ │ [_______]  [_______]  [_______] 🔒  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Consent                                 │
│ ┌─────────────────────────────────────┐ │
│ │ [✓] Treatment consent               │ │
│ │ [✓] Data sharing consent            │ │
│ │ [ ] Research consent                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [   Cancel   ]  [  Save Patient  ]     │
└─────────────────────────────────────────┘
```

**Validation:**
- Real-time FHIR R4 validation
- Required field indicators (*)
- Email format validation
- Phone number formatting
- Date picker constraints
- MRN uniqueness check

**Features:**
- Auto-save draft (local storage)
- PHI field encryption indicator (🔒)
- Form state persistence
- Validation error highlighting
- Success/error snackbar feedback

#### 3.4 Symptom Input Screen (`symptom_input_screen.dart`)

**API Endpoint:** `POST /api/v1/ml-prediction/symptom-analysis`

**Layout:**
```
┌─────────────────────────────────────────┐
│ ← Symptom Checker                       │
├─────────────────────────────────────────┤
│ Describe your symptoms                  │
│ ┌─────────────────────────────────────┐ │
│ │                                     │ │
│ │  I have been experiencing...        │ │
│ │                                     │ │
│ │                                     │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│ [🎤 Voice Input] [📷 Photo] [⌨️ Type]  │
├─────────────────────────────────────────┤
│ AI Analysis Results                     │
│ ┌─────────────────────────────────────┐ │
│ │ Possible Conditions:                │ │
│ │                                     │ │
│ │ 1. Common Cold (82% confidence)     │ │
│ │    • Rest and hydration             │ │
│ │    • Over-the-counter medication    │ │
│ │                                     │ │
│ │ 2. Allergies (15% confidence)       │ │
│ │    • Antihistamines                 │ │
│ │                                     │ │
│ │ 3. Flu (3% confidence)              │ │
│ │    • Consult doctor if worsens      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ⚠️ Low Confidence - Consult Doctor      │
│ [  Schedule Appointment  ]              │
└─────────────────────────────────────────┘
```

**Features:**
- **Voice Input:** Speech-to-text with permissions
- **Photo Upload:** Image recognition (future)
- **Text Input:** Natural language processing
- **AI Confidence:** Visual confidence meter
- **Recommendations:** Treatment suggestions
- **Escalation:** "Consult Doctor" for low confidence

---

### 4. Healthcare Records Screen

#### 4.1 Healthcare Records Screen (`healthcare_records_screen.dart`)

**API Endpoints:**
- Clinical Docs: `GET /api/v1/healthcare/documents`
- Immunizations: `GET /api/v1/healthcare/immunizations`
- FHIR Validate: `POST /api/v1/fhir/validate`

**Tabs:**
1. **Clinical Documents**
2. **Immunizations**
3. **FHIR Validation**
4. **Anonymization**

**Clinical Documents Tab:**
```
┌─────────────────────────────────────────┐
│ Clinical Documents                      │
├─────────────────────────────────────────┤
│ 🔍 Search documents...                  │
│ [Type ⌄] [Status ⌄] [Date ⌄]           │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 📄 Lab Result - CBC                 │ │
│ │    Patient: John Doe                │ │
│ │    Date: Nov 10, 2025               │ │
│ │    Status: Final  🔒 Encrypted      │ │
│ │    [View] [Download]                │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Clinical Note - Follow-up        │ │
│ │    Patient: Jane Smith              │ │
│ │    Date: Nov 9, 2025                │ │
│ │    Status: Draft                    │ │
│ │    [View] [Download]                │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Immunizations Tab:**
```
┌─────────────────────────────────────────┐
│ Immunizations                           │
├─────────────────────────────────────────┤
│ Patient: [Select Patient ⌄]            │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 💉 COVID-19 Vaccine (Pfizer)        │ │
│ │    Dose 2 of 2                      │ │
│ │    Date: Oct 15, 2025               │ │
│ │    Lot: EK1234                      │ │
│ │    Status: Completed ✓              │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 💉 Influenza Vaccine                │ │
│ │    Annual dose                      │ │
│ │    Date: Sep 1, 2025                │ │
│ │    Status: Completed ✓              │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [+ Add Immunization]                    │
└─────────────────────────────────────────┘
```

---

### 5. Document Management Screen

**API Endpoints:**
- Upload: `POST /api/v1/documents/upload`
- Download: `GET /api/v1/documents/download/{key}`

**Layout:**
```
┌─────────────────────────────────────────┐
│ ← Document Management                   │
├─────────────────────────────────────────┤
│ [Upload] [Search] [Analytics]           │
├─────────────────────────────────────────┤
│ Upload Documents                        │
│ ┌─────────────────────────────────────┐ │
│ │                                     │ │
│ │        📁 Drag & Drop Files         │ │
│ │           or tap to browse          │ │
│ │                                     │ │
│ │    Max 100MB | PDF, JPG, PNG        │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Patient: [Select Patient ⌄]            │
│ Type: [Document Type ⌄]                │
│                                         │
│ Uploading: file.pdf                     │
│ ████████████░░░░ 75%                    │
│                                         │
│ [  Upload All  ]                        │
└─────────────────────────────────────────┘
```

**Features:**
- Multi-file upload with progress
- AI classification (automatic)
- OCR text extraction
- HIPAA encryption
- Patient association
- Document preview

---

### 6. IRIS Integration Screen

**API Endpoints:**
- Health: `GET /api/v1/iris/health`
- Sync: `POST /api/v1/iris/sync`
- Status: `GET /api/v1/iris/status`

**Tabs:**
1. **Sync Operations**
2. **Endpoint Health**
3. **Configuration**
4. **Security**

**Sync Tab:**
```
┌─────────────────────────────────────────┐
│ IRIS Integration                        │
├─────────────────────────────────────────┤
│ Last Sync: 15 minutes ago               │
│ Status: ● Healthy                       │
│ Records: 1,247 synced                   │
├─────────────────────────────────────────┤
│ [  Sync Now  ]                          │
├─────────────────────────────────────────┤
│ Sync History                            │
│ ┌─────────────────────────────────────┐ │
│ │ ✓ Nov 11, 10:30 AM                  │ │
│ │   1,247 records • 2m 15s            │ │
│ │   0 errors                          │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ ⚠️ Nov 11, 10:15 AM                 │ │
│ │   1,245 records • 3m 42s            │ │
│ │   2 warnings                        │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Endpoint Health Tab:**
```
┌─────────────────────────────────────────┐
│ API Endpoints                           │
├─────────────────────────────────────────┤
│ Primary IRIS API                        │
│ ● Healthy | 120ms avg response          │
│ https://iris.example.com/api            │
│                                         │
│ Backup IRIS API                         │
│ ● Healthy | 95ms avg response           │
│ https://backup-iris.example.com/api     │
│                                         │
│ Auth Service                            │
│ ● Healthy | 45ms avg response           │
│                                         │
│ Uptime (30 days): 99.9%                 │
└─────────────────────────────────────────┘
```

---

### 7. Audit & Compliance Screens

#### 7.1 Audit Logs Screen (`audit_logs_screen.dart`)

**API Endpoint:** `GET /api/v1/audit-logs/logs`

**Tabs:**
1. **Audit Logs**
2. **Security Events**
3. **PHI Access**
4. **Compliance Reports**

**Audit Logs Tab:**
```
┌─────────────────────────────────────────┐
│ ← Audit Logs                            │
├─────────────────────────────────────────┤
│ 🔍 Search logs...                       │
│ [Severity ⌄] [Category ⌄] [Date ⌄]     │
├─────────────────────────────────────────┤
│ Last 7 days: 1,234 events               │
│ Warnings: 12 | Errors: 2                │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 🟢 INFO - User Login                │ │
│ │    User: john.doe                   │ │
│ │    IP: 192.168.1.100                │ │
│ │    Time: 2m ago                     │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 🟡 WARNING - Rate Limit Approached  │ │
│ │    User: jane.smith                 │ │
│ │    Requests: 95/100                 │ │
│ │    Time: 5m ago                     │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 🔵 INFO - Patient Created           │ │
│ │    User: dr.jones                   │ │
│ │    Patient: MRN 123456              │ │
│ │    Time: 10m ago                    │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**PHI Access Tab:**
```
┌─────────────────────────────────────────┐
│ PHI Access Logs                         │
├─────────────────────────────────────────┤
│ All PHI access is tracked and audited   │
│ for HIPAA compliance                    │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 🔒 PHI Access                       │ │
│ │    User: dr.smith                   │ │
│ │    Patient: John Doe (MRN 123456)   │ │
│ │    Fields: SSN, DOB, Phone          │ │
│ │    Purpose: Treatment               │ │
│ │    Time: 1h ago                     │ │
│ │    Signature: ✓ Verified            │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 7.2 Compliance Screen (`compliance_screen.dart`)

**API Endpoint:** `GET /api/v1/compliance/summary`

**Layout:**
```
┌─────────────────────────────────────────┐
│ ← Compliance Dashboard                  │
├─────────────────────────────────────────┤
│ Overall Compliance: 94%                 │
│ ████████████████░░ 94/100               │
├─────────────────────────────────────────┤
│ HIPAA Compliance                        │
│ ┌─────────────────────────────────────┐ │
│ │ Status: 98% Compliant ✓             │ │
│ │ ████████████████████ 98%            │ │
│ │                                     │ │
│ │ ✓ Technical Safeguards              │ │
│ │ ✓ Uses & Disclosures of PHI         │ │
│ │ ⚠️ 2 minor issues                   │ │
│ │                                     │ │
│ │ Last Audit: Jan 1, 2024             │ │
│ │ Next Audit: Jul 1, 2024             │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ SOC2 Type II Compliance                 │
│ ┌─────────────────────────────────────┐ │
│ │ Status: 96% Compliant ✓             │ │
│ │ ███████████████████░ 96%            │ │
│ │                                     │ │
│ │ ✓ Logical Access Controls           │ │
│ │ ✓ Data Transmission Security        │ │
│ │ ⚠️ 1 minor issue                    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ISO 27001 Compliance                    │
│ ┌─────────────────────────────────────┐ │
│ │ Status: 87% Partial ⚠️              │ │
│ │ █████████████████░░░ 87%            │ │
│ │                                     │ │
│ │ ✓ Access Control Policy             │ │
│ │ ✗ Information Backup                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [  Generate Report  ]                   │
└─────────────────────────────────────────┘
```

---

### 8. Settings Screen

**Layout:**
```
┌─────────────────────────────────────────┐
│ ← Settings                              │
├─────────────────────────────────────────┤
│ [User Settings] [System Admin]          │
├─────────────────────────────────────────┤
│ Account                                 │
│ ┌─────────────────────────────────────┐ │
│ │ Profile                          >  │ │
│ │ Change Password                  >  │ │
│ │ Notification Preferences         >  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Security                                │
│ ┌─────────────────────────────────────┐ │
│ │ [✓] Enable biometric login          │ │
│ │ [✓] Auto-lock after 5 minutes       │ │
│ │ [ ] Allow screenshots (PHI risk)    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Appearance                              │
│ ┌─────────────────────────────────────┐ │
│ │ Theme: [Light ⌄]                    │ │
│ │ Language: [English ⌄]               │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ About                                   │
│ ┌─────────────────────────────────────┐ │
│ │ Version 1.0.0                       │ │
│ │ Privacy Policy                   >  │ │
│ │ Terms of Service                 >  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [  Logout  ]                            │
└─────────────────────────────────────────┘
```

---

## Data Flow & State Management

### Authentication Flow (Bloc Pattern)

```dart
// Events
abstract class AuthEvent {}
class LoginRequested extends AuthEvent {
  final String username;
  final String password;
}
class LogoutRequested extends AuthEvent {}
class RefreshTokenRequested extends AuthEvent {}

// States
abstract class AuthState {}
class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}
class AuthAuthenticated extends AuthState {
  final User user;
  final String accessToken;
}
class AuthError extends AuthState {
  final String message;
}

// Bloc
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final LoginUseCase loginUseCase;
  final LogoutUseCase logoutUseCase;

  AuthBloc({required this.loginUseCase}) : super(AuthInitial()) {
    on<LoginRequested>((event, emit) async {
      emit(AuthLoading());

      final result = await loginUseCase(
        LoginParams(
          username: event.username,
          password: event.password,
        ),
      );

      result.fold(
        (failure) => emit(AuthError(failure.message)),
        (tokens) => emit(AuthAuthenticated(
          user: tokens.user,
          accessToken: tokens.accessToken,
        )),
      );
    });
  }
}
```

### API Call Flow

```
UI (Screen)
  ↓ dispatches event
Bloc
  ↓ calls
UseCase
  ↓ calls
Repository
  ↓ calls
API Client (Dio)
  ↓ HTTP request
FastAPI Backend
  ↓ HTTP response
API Client
  ↓ parse JSON
Model (fromJson)
  ↓ returns Either<Failure, Model>
UseCase
  ↓ returns
Bloc
  ↓ emits state
UI (BlocBuilder)
  ↓ rebuilds
Widget Tree
```

### Offline Support Strategy

```dart
class PatientRepository {
  final PatientApi api;
  final CacheManager cache;
  final NetworkInfo networkInfo;

  Future<Either<Failure, List<Patient>>> getPatients() async {
    if (await networkInfo.isConnected) {
      try {
        final patients = await api.getPatients();
        await cache.savePatients(patients); // Cache for offline
        return Right(patients);
      } catch (e) {
        return Left(ServerFailure());
      }
    } else {
      // Return cached data if offline
      final cachedPatients = await cache.getPatients();
      if (cachedPatients != null) {
        return Right(cachedPatients);
      }
      return Left(NetworkFailure());
    }
  }
}
```

---

## API Integration Strategy

### Dio Configuration

```dart
class DioClient {
  late Dio _dio;
  final SecureStorage _storage;

  DioClient(this._storage) {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: Duration(seconds: 30),
        receiveTimeout: Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.addAll([
      AuthInterceptor(_storage),
      LoggingInterceptor(),
      RetryInterceptor(),
    ]);
  }
}
```

### Auth Interceptor (JWT Token Management)

```dart
class AuthInterceptor extends Interceptor {
  final SecureStorage storage;

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await storage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    // Add request ID for audit logging
    options.headers['X-Request-ID'] = Uuid().v4();

    handler.next(options);
  }

  @override
  void onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      // Token expired, try to refresh
      final refreshed = await _refreshToken();
      if (refreshed) {
        // Retry original request
        final opts = err.requestOptions;
        final token = await storage.getAccessToken();
        opts.headers['Authorization'] = 'Bearer $token';

        try {
          final response = await Dio().fetch(opts);
          return handler.resolve(response);
        } catch (e) {
          return handler.reject(err);
        }
      }
    }
    handler.next(err);
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await storage.getRefreshToken();
      final response = await Dio().post(
        '${ApiConstants.baseUrl}/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      await storage.saveAccessToken(response.data['access_token']);
      await storage.saveRefreshToken(response.data['refresh_token']);
      return true;
    } catch (e) {
      // Refresh failed, logout user
      await storage.clear();
      return false;
    }
  }
}
```

### Retrofit API Clients

```dart
@RestApi(baseUrl: ApiConstants.baseUrl)
abstract class AuthApi {
  factory AuthApi(Dio dio) = _AuthApi;

  @POST('/auth/login')
  @FormUrlEncoded()
  Future<TokenResponse> login(
    @Field('username') String username,
    @Field('password') String password,
  );

  @POST('/auth/register')
  Future<UserResponse> register(@Body() UserCreate user);

  @POST('/auth/refresh')
  Future<TokenResponse> refreshToken(
    @Body() Map<String, String> body,
  );

  @GET('/auth/me')
  Future<UserResponse> getCurrentUser();

  @POST('/auth/logout')
  Future<void> logout();
}

@RestApi(baseUrl: ApiConstants.baseUrl)
abstract class PatientApi {
  factory PatientApi(Dio dio) = _PatientApi;

  @GET('/healthcare/patients')
  Future<PatientListResponse> getPatients(
    @Query('skip') int skip,
    @Query('limit') int limit,
    @Query('search') String? search,
    @Query('gender') String? gender,
  );

  @GET('/healthcare/patients/{id}')
  Future<PatientResponse> getPatient(@Path('id') String id);

  @POST('/healthcare/patients')
  Future<PatientResponse> createPatient(@Body() PatientCreate patient);

  @PUT('/healthcare/patients/{id}')
  Future<PatientResponse> updatePatient(
    @Path('id') String id,
    @Body() PatientUpdate patient,
  );

  @DELETE('/healthcare/patients/{id}')
  Future<void> deletePatient(
    @Path('id') String id,
    @Query('reason') String reason,
  );
}

@RestApi(baseUrl: ApiConstants.baseUrl)
abstract class DashboardApi {
  factory DashboardApi(Dio dio) = _DashboardApi;

  @POST('/dashboard/refresh')
  Future<BulkDashboardResponse> bulkRefresh(
    @Body() BulkRefreshRequest request,
  );

  @GET('/dashboard/stats')
  Future<DashboardStats> getStats();

  @GET('/dashboard/activities')
  Future<DashboardActivities> getActivities(
    @Query('limit') int limit,
    @Query('time_range_hours') int timeRange,
  );
}
```

---

## Security & Compliance

### Secure Token Storage

```dart
class SecureStorage {
  final FlutterSecureStorage _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
    ),
  );

  Future<void> saveAccessToken(String token) async {
    await _storage.write(key: 'access_token', value: token);
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: 'access_token');
  }

  Future<void> saveRefreshToken(String token) async {
    await _storage.write(key: 'refresh_token', value: token);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: 'refresh_token');
  }

  Future<void> clear() async {
    await _storage.deleteAll();
  }
}
```

### PHI Protection

```dart
class PHIProtection {
  // Prevent screenshots when viewing PHI
  static void enableScreenProtection() {
    if (Platform.isAndroid) {
      SystemChrome.setEnabledSystemUIMode(
        SystemUiMode.immersive,
        overlays: [SystemUiOverlay.bottom],
      );
    }
  }

  static void disableScreenProtection() {
    SystemChrome.setEnabledSystemUIMode(
      SystemUiMode.edgeToEdge,
      overlays: SystemUiOverlay.values,
    );
  }

  // Auto-lock on app background
  static void setupAppLifecycleObserver() {
    WidgetsBinding.instance.addObserver(
      AppLifecycleObserver(),
    );
  }
}

class AppLifecycleObserver extends WidgetsBindingObserver {
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      // Clear sensitive data from memory
      // Lock the app
      // Require biometric/PIN to unlock
    }
  }
}
```

### Audit Logging

```dart
class AuditLogger {
  final AuditApi _api;

  Future<void> logPHIAccess({
    required String patientId,
    required List<String> fields,
    required String purpose,
  }) async {
    await _api.logEvent(
      AuditLogCreate(
        eventType: 'PHI_ACCESS',
        severity: 'INFO',
        category: 'phi',
        details: {
          'patient_id': patientId,
          'fields': fields,
          'purpose': purpose,
        },
      ),
    );
  }

  Future<void> logSecurityEvent({
    required String eventType,
    required String message,
    Map<String, dynamic>? details,
  }) async {
    await _api.logEvent(
      AuditLogCreate(
        eventType: eventType,
        severity: 'WARNING',
        category: 'security',
        message: message,
        details: details,
      ),
    );
  }
}
```

---

## UI/UX Design Guidelines

### Material Design 3 Theme

```dart
class AppTheme {
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.light,
    ),
    cardTheme: CardTheme(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
    appBarTheme: AppBarTheme(
      centerTitle: false,
      elevation: 0,
      backgroundColor: Colors.blue,
      foregroundColor: Colors.white,
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      filled: true,
      fillColor: Colors.grey[100],
    ),
  );

  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.dark,
    ),
    // ... dark theme config
  );
}
```

### Color Coding for Healthcare

```dart
class HealthcareColors {
  // Risk Levels
  static const Color riskHigh = Colors.red;
  static const Color riskModerate = Colors.orange;
  static const Color riskLow = Colors.green;
  static const Color riskUnknown = Colors.grey;

  // Status Indicators
  static const Color statusHealthy = Color(0xFF4CAF50);
  static const Color statusWarning = Color(0xFFFF9800);
  static const Color statusCritical = Color(0xFFF44336);
  static const Color statusInfo = Color(0xFF2196F3);

  // Document Types
  static const Color docLab = Color(0xFF9C27B0);
  static const Color docClinical = Color(0xFF3F51B5);
  static const Color docImmunization = Color(0xFF009688);

  // Compliance
  static const Color compliant = Color(0xFF4CAF50);
  static const Color partialCompliant = Color(0xFFFFC107);
  static const Color nonCompliant = Color(0xFFF44336);
}
```

### Typography

```dart
class AppTextStyles {
  static const TextStyle heading1 = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    color: Colors.black87,
  );

  static const TextStyle heading2 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w600,
    color: Colors.black87,
  );

  static const TextStyle bodyLarge = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.normal,
    color: Colors.black87,
  );

  static const TextStyle caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.normal,
    color: Colors.grey,
  );

  static const TextStyle labelPHI = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w500,
    color: Colors.red,
  );
}
```

### Reusable Components

**MetricCard Widget:**
```dart
class MetricCard extends StatelessWidget {
  final String title;
  final String value;
  final String? change;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 24),
                SizedBox(width: 8),
                Text(title, style: AppTextStyles.caption),
              ],
            ),
            SizedBox(height: 12),
            Text(value, style: AppTextStyles.heading2),
            if (change != null)
              Text(change!, style: AppTextStyles.caption),
          ],
        ),
      ),
    );
  }
}
```

**PHI Label Widget:**
```dart
class PHILabel extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.red[50],
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.red[300]!),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.lock, size: 12, color: Colors.red),
          SizedBox(width: 4),
          Text(
            'PHI',
            style: TextStyle(
              fontSize: 10,
              color: Colors.red,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Project setup with clean architecture
- [ ] Configure dependencies
- [ ] Setup Dio client with interceptors
- [ ] Implement secure storage
- [ ] Create base models and entities
- [ ] Setup navigation/routing
- [ ] Implement Material Design 3 theme
- [ ] Create reusable UI components

### Phase 2: Authentication (Weeks 3-4)
- [ ] Login screen UI
- [ ] Register screen UI
- [ ] AuthBloc implementation
- [ ] API integration (login, register, refresh)
- [ ] Token management
- [ ] Biometric authentication (optional)
- [ ] Logout functionality
- [ ] Session management

### Phase 3: Dashboard (Weeks 5-6)
- [ ] Dashboard screen UI
- [ ] Role-based tab navigation
- [ ] Metric cards implementation
- [ ] Activity feed
- [ ] System health indicators
- [ ] API integration (bulk refresh)
- [ ] Real-time updates
- [ ] Pull-to-refresh

### Phase 4: Patient Management (Weeks 7-9)
- [ ] Patient list screen
- [ ] Search and filter functionality
- [ ] Patient detail screen
- [ ] Patient form (create/edit)
- [ ] FHIR R4 validation
- [ ] PHI encryption/decryption
- [ ] Symptom input screen
- [ ] Voice input integration

### Phase 5: Healthcare Records (Weeks 10-11)
- [ ] Clinical documents tab
- [ ] Immunizations tab
- [ ] FHIR validation tab
- [ ] Document viewer
- [ ] Immunization form
- [ ] API integrations

### Phase 6: Additional Features (Weeks 12-14)
- [ ] Document management screen
- [ ] File upload with progress
- [ ] IRIS integration screen
- [ ] Sync operations
- [ ] Audit logs screen
- [ ] Compliance dashboard
- [ ] Settings screen

### Phase 7: Security & Compliance (Weeks 15-16)
- [ ] Screen capture prevention
- [ ] Auto-lock implementation
- [ ] Audit logging integration
- [ ] PHI access tracking
- [ ] Security headers
- [ ] Rate limiting
- [ ] Error handling

### Phase 8: Testing & Polish (Weeks 17-18)
- [ ] Unit tests for blocs
- [ ] Widget tests for screens
- [ ] Integration tests
- [ ] API mock testing
- [ ] Performance optimization
- [ ] Accessibility improvements
- [ ] Dark mode support

### Phase 9: Deployment (Weeks 19-20)
- [ ] iOS build configuration
- [ ] Android build configuration
- [ ] App signing
- [ ] Beta testing (TestFlight, Firebase)
- [ ] Bug fixes
- [ ] Documentation
- [ ] App Store submission
- [ ] Play Store submission

---

## Estimated Timeline

**Total Development Time:** 4-6 months (with 2-3 developers)

- **Phase 1-2:** Foundation & Auth (4 weeks)
- **Phase 3-4:** Dashboard & Patients (6 weeks)
- **Phase 5-6:** Healthcare & Features (5 weeks)
- **Phase 7:** Security (2 weeks)
- **Phase 8:** Testing (2 weeks)
- **Phase 9:** Deployment (2 weeks)

**Total:** ~21 weeks (5 months)

---

## Next Steps

1. **Review this document** with the team
2. **Approve architecture** and design approach
3. **Setup development environment** (Flutter SDK, IDE)
4. **Create project** with clean architecture
5. **Start Phase 1** (Foundation)
6. **Weekly progress reviews**
7. **Iterative development** with continuous feedback

---

## Conclusion

This comprehensive architecture document provides a complete blueprint for migrating the VitalCore Healthcare Platform to Flutter mobile apps while maintaining the existing React web application. The hybrid approach ensures:

✅ **No disruption** to current web users
✅ **Native mobile** experience on iOS and Android
✅ **Shared backend** minimizes development effort
✅ **HIPAA compliance** with secure PHI handling
✅ **Clean architecture** for maintainability
✅ **Scalable design** for future enhancements

The estimated 4-6 month timeline provides a realistic schedule for delivering a production-ready Flutter mobile application that mirrors the functionality of the existing React web app.

---

**Document Version:** 1.0
**Last Updated:** November 11, 2025
**Author:** VitalCore Development Team
