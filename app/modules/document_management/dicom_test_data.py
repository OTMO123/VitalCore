"""
🏥 DICOM Test Data Generator
Generate realistic test data for Orthanc DICOM integration testing
Includes various user roles, patients, and DICOM studies for comprehensive testing

Security: All test data is synthetic - no real PHI
Compliance: Test scenarios cover SOC2 + HIPAA requirements
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import random

from app.modules.document_management.rbac_dicom import DicomRole
from app.core.database_unified import DocumentType


@dataclass
class TestUser:
    """Test user for DICOM integration testing."""
    id: str
    username: str
    email: str
    role: str
    dicom_role: DicomRole
    full_name: str
    department: str
    license_number: Optional[str] = None
    institution: str = "IRIS Medical Center"
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "dicom_role": self.dicom_role.value,
            "full_name": self.full_name,
            "department": self.department,
            "license_number": self.license_number,
            "institution": self.institution
        }


@dataclass
class TestPatient:
    """Test patient for DICOM testing."""
    id: str
    patient_id: str  # Hospital MRN
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    phone: str
    email: str
    address: Dict[str, str]
    mrn: str
    
    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth.isoformat(),
            "gender": self.gender,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "mrn": self.mrn
        }


@dataclass
class TestDicomStudy:
    """Test DICOM study data."""
    study_id: str
    patient_id: str
    study_date: datetime
    study_time: str
    modality: str
    study_description: str
    series_count: int
    instance_count: int
    referring_physician: str
    performing_physician: str
    institution_name: str
    study_instance_uid: str
    accession_number: str
    series_list: List[Dict]
    
    def to_dict(self):
        return {
            "study_id": self.study_id,
            "patient_id": self.patient_id,
            "study_date": self.study_date.date().isoformat(),
            "study_time": self.study_time,
            "modality": self.modality,
            "study_description": self.study_description,
            "series_count": self.series_count,
            "instance_count": self.instance_count,
            "referring_physician": self.referring_physician,
            "performing_physician": self.performing_physician,
            "institution_name": self.institution_name,
            "study_instance_uid": self.study_instance_uid,
            "accession_number": self.accession_number,
            "series_list": self.series_list
        }


class DicomTestDataGenerator:
    """Generate comprehensive test data for DICOM integration."""
    
    def __init__(self):
        self.users = []
        self.patients = []
        self.studies = []
        
        # Medical specialties and departments
        self.departments = [
            "Radiology", "Cardiology", "Oncology", "Emergency Medicine",
            "Internal Medicine", "Surgery", "Pediatrics", "Neurology",
            "Orthopedics", "Gastroenterology"
        ]
        
        # DICOM modalities with realistic study descriptions
        self.modality_descriptions = {
            "CT": [
                "CT Chest without Contrast",
                "CT Abdomen and Pelvis with Contrast", 
                "CT Head without Contrast",
                "CT Angiography Chest",
                "CT Colonography"
            ],
            "MR": [
                "MRI Brain without and with Contrast",
                "MRI Lumbar Spine without Contrast",
                "MRI Knee without Contrast",
                "MR Angiography Brain",
                "MRI Cardiac Function Study"
            ],
            "XR": [
                "Chest X-ray, 2 Views",
                "Knee X-ray, 3 Views", 
                "Lumbar Spine X-ray",
                "Hand X-ray, 3 Views",
                "Pelvis X-ray"
            ],
            "US": [
                "Abdominal Ultrasound Complete",
                "Echocardiogram Complete",
                "Pelvic Ultrasound",
                "Carotid Ultrasound Bilateral",
                "Thyroid Ultrasound"
            ],
            "CR": [
                "Computed Radiography Chest",
                "CR Abdomen KUB", 
                "CR Extremity",
                "CR Spine",
                "CR Pelvis"
            ],
            "DR": [
                "Digital Radiography Chest",
                "DR Orthopedic Hardware",
                "DR Post-Surgical Follow-up",
                "DR Trauma Series",
                "DR Pediatric Study"
            ]
        }
        
        # Physician names (synthetic)
        self.physician_names = [
            "Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez",
            "Dr. David Wilson", "Dr. Lisa Thompson", "Dr. James Brown",
            "Dr. Maria Garcia", "Dr. Robert Lee", "Dr. Jennifer Davis",
            "Dr. Christopher Miller", "Dr. Amanda Martinez", "Dr. Kevin Anderson"
        ]
    
    def generate_test_users(self) -> List[TestUser]:
        """Generate test users with different DICOM roles."""
        
        users_data = [
            # Radiologists
            ("dr.smith", "dr.smith@iris.hospital", "ADMIN", DicomRole.RADIOLOGIST, "Dr. John Smith", "Radiology", "RAD12345"),
            ("dr.williams", "dr.williams@iris.hospital", "ADMIN", DicomRole.RADIOLOGIST, "Dr. Sarah Williams", "Radiology", "RAD12346"),
            
            # Radiology Technicians
            ("tech.jones", "tech.jones@iris.hospital", "OPERATOR", DicomRole.RADIOLOGY_TECHNICIAN, "Mike Jones", "Radiology", "RT12345"),
            ("tech.brown", "tech.brown@iris.hospital", "OPERATOR", DicomRole.RADIOLOGY_TECHNICIAN, "Lisa Brown", "Radiology", "RT12346"),
            
            # Referring Physicians
            ("dr.garcia", "dr.garcia@iris.hospital", "USER", DicomRole.REFERRING_PHYSICIAN, "Dr. Maria Garcia", "Cardiology", "CARD12345"),
            ("dr.lee", "dr.lee@iris.hospital", "USER", DicomRole.REFERRING_PHYSICIAN, "Dr. Robert Lee", "Emergency Medicine", "EM12345"),
            
            # Clinical Staff
            ("nurse.davis", "nurse.davis@iris.hospital", "USER", DicomRole.CLINICAL_STAFF, "Jennifer Davis, RN", "Emergency Medicine", "RN12345"),
            ("pa.wilson", "pa.wilson@iris.hospital", "USER", DicomRole.CLINICAL_STAFF, "David Wilson, PA-C", "Internal Medicine", "PA12345"),
            
            # DICOM Administrator
            ("admin.dicom", "admin.dicom@iris.hospital", "ADMIN", DicomRole.DICOM_ADMINISTRATOR, "Alex Thompson", "IT - Medical Imaging", None),
            
            # PACS Operator
            ("pacs.operator", "pacs.operator@iris.hospital", "OPERATOR", DicomRole.PACS_OPERATOR, "Chris Miller", "IT - Medical Imaging", "PACS12345"),
            
            # System Administrator
            ("sysadmin", "sysadmin@iris.hospital", "SUPER_ADMIN", DicomRole.SYSTEM_ADMINISTRATOR, "System Administrator", "IT", None),
            
            # Integration Service (API)
            ("api.service", "api.service@iris.hospital", "OPERATOR", DicomRole.INTEGRATION_SERVICE, "API Integration Service", "IT", None),
            
            # Researcher
            ("researcher.kim", "researcher.kim@iris.hospital", "USER", DicomRole.RESEARCHER, "Dr. Anna Kim", "Research", "RES12345"),
            
            # Data Scientist
            ("datascientist", "ds.martinez@iris.hospital", "OPERATOR", DicomRole.DATA_SCIENTIST, "Dr. Luis Martinez", "Data Science", "DS12345"),
            
            # External Clinician
            ("external.doc", "external@partner.hospital", "USER", DicomRole.EXTERNAL_CLINICIAN, "Dr. External Partner", "External Facility", "EXT12345"),
            
            # Student
            ("student.taylor", "student.taylor@medschool.edu", "USER", DicomRole.STUDENT, "Taylor Student", "Medical School", "MED12345")
        ]
        
        users = []
        for username, email, role, dicom_role, full_name, dept, license_num in users_data:
            user = TestUser(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                role=role,
                dicom_role=dicom_role,
                full_name=full_name,
                department=dept,
                license_number=license_num
            )
            users.append(user)
        
        self.users = users
        return users
    
    def generate_test_patients(self, count: int = 20) -> List[TestPatient]:
        """Generate test patients with realistic data."""
        
        # Synthetic patient data
        first_names = ["John", "Sarah", "Michael", "Emily", "David", "Lisa", "James", "Maria", 
                      "Robert", "Jennifer", "William", "Amanda", "Christopher", "Michelle", 
                      "Daniel", "Jessica", "Matthew", "Ashley", "Anthony", "Elizabeth"]
        
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                     "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", 
                     "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
        
        patients = []
        for i in range(count):
            birth_date = datetime.now() - timedelta(days=random.randint(365*18, 365*80))  # 18-80 years old
            
            patient = TestPatient(
                id=str(uuid.uuid4()),
                patient_id=f"P{1000 + i:04d}",
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                date_of_birth=birth_date,
                gender=random.choice(["M", "F"]),
                phone=f"555-{random.randint(100,999):03d}-{random.randint(1000,9999):04d}",
                email=f"patient{i+1}@email.com",
                address={
                    "street": f"{random.randint(100,9999)} {random.choice(['Main', 'Oak', 'Elm', 'Park'])} St",
                    "city": random.choice(["Springfield", "Riverside", "Fairview", "Georgetown", "Madison"]),
                    "state": random.choice(["CA", "NY", "TX", "FL", "IL"]),
                    "zip": f"{random.randint(10000,99999)}"
                },
                mrn=f"MRN{100000 + i:06d}"
            )
            patients.append(patient)
        
        self.patients = patients
        return patients
    
    def generate_test_studies(self, patients: List[TestPatient], studies_per_patient: int = 3) -> List[TestDicomStudy]:
        """Generate test DICOM studies for patients."""
        
        studies = []
        
        for patient in patients:
            for study_num in range(studies_per_patient):
                # Random study date within last 2 years
                study_date = datetime.now() - timedelta(days=random.randint(1, 730))
                
                # Select random modality
                modality = random.choice(list(self.modality_descriptions.keys()))
                study_description = random.choice(self.modality_descriptions[modality])
                
                # Generate series data
                series_count = random.randint(1, 5)
                instance_count = series_count * random.randint(50, 200)
                
                series_list = []
                for series_num in range(series_count):
                    series_list.append({
                        "series_id": f"S{study_num:03d}{series_num:02d}",
                        "series_number": series_num + 1,
                        "series_description": f"{study_description} - Series {series_num + 1}",
                        "modality": modality,
                        "instance_count": random.randint(50, 200),
                        "series_instance_uid": f"1.2.826.0.1.3680043.8.498.{random.randint(100000, 999999)}"
                    })
                
                study = TestDicomStudy(
                    study_id=f"STU{patient.patient_id}{study_num:03d}",
                    patient_id=patient.patient_id,
                    study_date=study_date,
                    study_time=f"{random.randint(8,18):02d}{random.randint(0,59):02d}{random.randint(0,59):02d}",
                    modality=modality,
                    study_description=study_description,
                    series_count=series_count,
                    instance_count=instance_count,
                    referring_physician=random.choice(self.physician_names),
                    performing_physician=random.choice(self.physician_names),
                    institution_name="IRIS Medical Center",
                    study_instance_uid=f"1.2.826.0.1.3680043.8.498.{random.randint(100000000, 999999999)}",
                    accession_number=f"ACC{random.randint(1000000, 9999999)}",
                    series_list=series_list
                )
                studies.append(study)
        
        self.studies = studies
        return studies
    
    def get_test_scenario_data(self) -> Dict[str, Any]:
        """Get all test data organized for scenarios."""
        return {
            "users": [user.to_dict() for user in self.users],
            "patients": [patient.to_dict() for patient in self.patients],
            "studies": [study.to_dict() for study in self.studies],
            "scenarios": self._generate_test_scenarios()
        }
    
    def _generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate test scenarios for different user roles."""
        
        scenarios = [
            {
                "name": "Radiologist Full Access",
                "description": "Radiologist views and reports on multiple patient studies",
                "user_role": DicomRole.RADIOLOGIST.value,
                "permissions_tested": [
                    "dicom:view", "dicom:download", "metadata:read", "metadata:write",
                    "phi:dicom", "patient:cross", "qc:approve"
                ],
                "expected_access": "FULL",
                "test_patients": 5
            },
            {
                "name": "Technician Upload Workflow", 
                "description": "Radiology technician uploads new DICOM studies",
                "user_role": DicomRole.RADIOLOGY_TECHNICIAN.value,
                "permissions_tested": [
                    "dicom:view", "dicom:upload", "metadata:read", "phi:dicom", "qc:review"
                ],
                "expected_access": "LIMITED",
                "test_patients": 3
            },
            {
                "name": "Referring Physician Patient Access",
                "description": "Physician views studies for their own patients only", 
                "user_role": DicomRole.REFERRING_PHYSICIAN.value,
                "permissions_tested": [
                    "dicom:view", "dicom:download", "metadata:read", "phi:dicom"
                ],
                "expected_access": "PATIENT_SPECIFIC",
                "test_patients": 2
            },
            {
                "name": "Clinical Staff Limited View",
                "description": "Clinical staff views DICOM for immediate patient care",
                "user_role": DicomRole.CLINICAL_STAFF.value,
                "permissions_tested": [
                    "dicom:view", "metadata:read", "phi:dicom"
                ],
                "expected_access": "VIEW_ONLY",
                "test_patients": 1
            },
            {
                "name": "DICOM Administrator Management",
                "description": "DICOM admin manages system configuration and user access",
                "user_role": DicomRole.DICOM_ADMINISTRATOR.value,
                "permissions_tested": [
                    "dicom:view", "dicom:upload", "dicom:delete", "orthanc:config",
                    "orthanc:stats", "api:access", "webhook:manage"
                ],
                "expected_access": "ADMINISTRATIVE",
                "test_patients": 10
            },
            {
                "name": "Researcher De-identified Access",
                "description": "Researcher accesses de-identified DICOM data for studies",
                "user_role": DicomRole.RESEARCHER.value,
                "permissions_tested": [
                    "dicom:view", "dicom:download", "research:access", "analytics:read"
                ],
                "expected_access": "DE_IDENTIFIED_ONLY",
                "test_patients": 15
            },
            {
                "name": "Data Scientist ML Training",
                "description": "Data scientist accesses DICOM for machine learning training",
                "user_role": DicomRole.DATA_SCIENTIST.value,
                "permissions_tested": [
                    "dicom:view", "dicom:download", "metadata:generate", 
                    "ml:training", "api:access", "analytics:read"
                ],
                "expected_access": "ML_FOCUSED", 
                "test_patients": 20
            },
            {
                "name": "External Clinician Consultation",
                "description": "External clinician reviews specific studies for consultation",
                "user_role": DicomRole.EXTERNAL_CLINICIAN.value,
                "permissions_tested": [
                    "dicom:view", "metadata:read", "phi:dicom"
                ],
                "expected_access": "CONSULTATION_ONLY",
                "test_patients": 1
            },
            {
                "name": "Student Educational Access", 
                "description": "Medical student views studies for educational purposes",
                "user_role": DicomRole.STUDENT.value,
                "permissions_tested": [
                    "dicom:view", "metadata:read"
                ],
                "expected_access": "EDUCATIONAL_ONLY",
                "test_patients": 3
            },
            {
                "name": "Integration Service API Access",
                "description": "API service processes DICOM data for system integration", 
                "user_role": DicomRole.INTEGRATION_SERVICE.value,
                "permissions_tested": [
                    "dicom:view", "dicom:upload", "metadata:read", "metadata:write",
                    "metadata:generate", "api:access", "ml:training"
                ],
                "expected_access": "API_INTEGRATION",
                "test_patients": 10
            }
        ]
        
        return scenarios
    
    def save_test_data_to_files(self, output_dir: str = "test_data"):
        """Save test data to JSON files."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save all data
        test_data = self.get_test_scenario_data()
        
        with open(f"{output_dir}/test_users.json", "w") as f:
            json.dump(test_data["users"], f, indent=2, default=str)
        
        with open(f"{output_dir}/test_patients.json", "w") as f:
            json.dump(test_data["patients"], f, indent=2, default=str)
        
        with open(f"{output_dir}/test_studies.json", "w") as f:
            json.dump(test_data["studies"], f, indent=2, default=str)
        
        with open(f"{output_dir}/test_scenarios.json", "w") as f:
            json.dump(test_data["scenarios"], f, indent=2, default=str)
        
        with open(f"{output_dir}/complete_test_data.json", "w") as f:
            json.dump(test_data, f, indent=2, default=str)
        
        print(f"✅ Test data saved to {output_dir}/ directory")
        print(f"   - {len(test_data['users'])} test users")
        print(f"   - {len(test_data['patients'])} test patients")
        print(f"   - {len(test_data['studies'])} test studies") 
        print(f"   - {len(test_data['scenarios'])} test scenarios")


# Global instance
_test_data_generator: Optional[DicomTestDataGenerator] = None


def get_test_data_generator() -> DicomTestDataGenerator:
    """Get or create test data generator instance."""
    global _test_data_generator
    if _test_data_generator is None:
        _test_data_generator = DicomTestDataGenerator()
    return _test_data_generator


def generate_complete_test_dataset():
    """Generate complete test dataset for DICOM integration."""
    generator = get_test_data_generator()
    
    print("🏥 Generating DICOM Integration Test Dataset...")
    
    # Generate all test data
    users = generator.generate_test_users()
    patients = generator.generate_test_patients(count=20)
    studies = generator.generate_test_studies(patients, studies_per_patient=3)
    
    print(f"✅ Generated {len(users)} test users with DICOM roles")
    print(f"✅ Generated {len(patients)} test patients")
    print(f"✅ Generated {len(studies)} test DICOM studies")
    
    return generator.get_test_scenario_data()


if __name__ == "__main__":
    # Generate and save test data
    generator = get_test_data_generator()
    
    users = generator.generate_test_users()
    patients = generator.generate_test_patients(20)
    studies = generator.generate_test_studies(patients, 3)
    
    generator.save_test_data_to_files()
    
    print("🎯 Test data generation complete!")
    print("Ready for comprehensive DICOM integration testing")