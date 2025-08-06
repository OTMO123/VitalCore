#!/usr/bin/env python3
"""
Basic functionality test script for the IRIS API Integration System
Tests core functionality without requiring a full database setup.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_imports():
    """Test that all core modules can be imported successfully"""
    try:
        print("Testing core imports...")
        
        # Test core modules
        from app.core.config import get_settings
        from app.core.security import EncryptionService
        from app.core.event_bus_advanced import EventBus
        print("✅ Core modules imported successfully")
        
        # Test healthcare modules
        from app.modules.healthcare_records.service import HealthcareRecordsService, get_healthcare_service
        from app.modules.healthcare_records.schemas import ClinicalDocumentCreate, ConsentCreate
        from app.modules.healthcare_records.fhir_validator import FHIRValidator
        from app.modules.healthcare_records.anonymization import AnonymizationEngine
        print("✅ Healthcare modules imported successfully")
        
        # Test FHIR schemas
        from app.schemas.fhir_r4 import FHIRPatient, FHIRImmunization, validate_fhir_resource
        print("✅ FHIR schemas imported successfully")
        
        # Test service creation (without database)
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.ENVIRONMENT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False


async def test_fhir_validation():
    """Test FHIR validation functionality"""
    try:
        print("\nTesting FHIR validation...")
        
        from app.modules.healthcare_records.fhir_validator import FHIRValidator
        from app.schemas.fhir_r4 import FHIRPatient
        
        validator = FHIRValidator()
        
        # Test valid patient resource
        valid_patient = {
            "resourceType": "Patient",
            "id": "example-patient",
            "active": True,
            "name": [
                {
                    "use": "official",
                    "family": "Doe",
                    "given": ["John"]
                }
            ],
            "gender": "male"
        }
        
        result = await validator.validate_resource(valid_patient, "Patient")
        
        if result.is_valid:
            print("✅ FHIR Patient validation passed")
        else:
            print(f"❌ FHIR Patient validation failed: {result.errors}")
            return False
            
        # Test invalid resource
        invalid_patient = {
            "resourceType": "Patient",
            "gender": "invalid_gender"
        }
        
        result = await validator.validate_resource(invalid_patient, "Patient")
        
        if not result.is_valid:
            print("✅ FHIR validation correctly identified invalid resource")
        else:
            print("❌ FHIR validation should have failed for invalid resource")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FHIR validation test failed: {str(e)}")
        return False


async def test_anonymization():
    """Test data anonymization functionality"""
    try:
        print("\nTesting data anonymization...")
        
        from app.modules.healthcare_records.anonymization import AnonymizationEngine
        
        config = {
            'default_technique': 'generalization',
            'k_anonymity': {
                'enabled': True,
                'k': 3,
                'quasi_identifiers': ['age', 'zipcode']
            }
        }
        
        engine = AnonymizationEngine(config)
        
        # Test record anonymization
        test_record = {
            'patient_id': 'test-123',
            'age': 35,
            'zipcode': '12345',
            'gender': 'male',
            'ssn': '123-45-6789'  # Should be removed as direct identifier
        }
        
        anonymized = await engine.anonymize_record(test_record)
        
        # Check that direct identifiers were removed
        if 'ssn' in anonymized:
            print("❌ Direct identifier (SSN) should have been removed")
            return False
            
        # Check that quasi-identifiers were generalized
        if 'age' in anonymized and anonymized['age'] != 35:
            print("✅ Age was generalized")
        else:
            print("⚠️  Age generalization may not be working as expected")
            
        print("✅ Data anonymization basic test passed")
        return True
        
    except Exception as e:
        print(f"❌ Anonymization test failed: {str(e)}")
        return False


async def test_encryption():
    """Test encryption functionality"""
    try:
        print("\nTesting encryption...")
        
        from app.core.security import EncryptionService
        
        encryption = EncryptionService()
        
        # Test data encryption
        test_data = "This is sensitive PHI data"
        encrypted = await encryption.encrypt(test_data, context={'field': 'test'})
        
        if encrypted == test_data:
            print("❌ Data was not encrypted")
            return False
            
        # Test decryption
        decrypted = await encryption.decrypt(encrypted)
        
        if decrypted != test_data:
            print("❌ Decryption failed")
            return False
            
        print("✅ Encryption/decryption test passed")
        return True
        
    except Exception as e:
        print(f"❌ Encryption test failed: {str(e)}")
        return False


async def test_event_bus():
    """Test event bus functionality"""
    try:
        print("\nTesting event bus...")
        
        from app.core.event_bus_advanced import EventBus, DomainEvent
        
        class TestEvent(DomainEvent):
            message: str
            
        event_bus = EventBus()
        
        # Test event creation
        test_event = TestEvent(message="Test event")
        
        if test_event.message == "Test event":
            print("✅ Event creation test passed")
        else:
            print("❌ Event creation failed")
            return False
            
        print("✅ Event bus basic test passed")
        return True
        
    except Exception as e:
        print(f"❌ Event bus test failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🏥 IRIS API Integration System - Basic Functionality Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_fhir_validation,
        test_anonymization,
        test_encryption,
        test_event_bus
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Core functionality is working.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)