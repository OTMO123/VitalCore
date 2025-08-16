#!/usr/bin/env python3
"""
Simple test data creation script using HTTP requests
Creates users and patients for testing the frontend
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_backend():
    """Test if backend is available"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_users():
    """Create test users"""
    users = [
        {
            "username": "admin",
            "email": "admin@healthcare.local",
            "password": "admin123",
            "role": "admin",
            "full_name": "System Administrator"
        },
        {
            "username": "doctor1",
            "email": "doctor1@healthcare.local", 
            "password": "doctor123",
            "role": "doctor",
            "full_name": "Dr. John Smith"
        },
        {
            "username": "nurse1",
            "email": "nurse1@healthcare.local",
            "password": "nurse123", 
            "role": "nurse",
            "full_name": "Nurse Jane Wilson"
        },
        {
            "username": "operator1",
            "email": "operator1@healthcare.local",
            "password": "operator123",
            "role": "operator",
            "full_name": "Medical Operator Sarah Brown"
        }
    ]
    
    created_users = []
    for user in users:
        try:
            response = requests.post(
                f"{API_BASE}/auth/register",
                json=user,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code in [200, 201]:
                created_users.append(user)
                print(f"✅ Created user: {user['username']} ({user['role']})")
            else:
                print(f"⚠️  User {user['username']} might already exist or failed: {response.status_code}")
                created_users.append(user)  # Add anyway for login credentials
        except Exception as e:
            print(f"❌ Failed to create user {user['username']}: {e}")
    
    return created_users

def login_admin():
    """Login as admin to get token"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={
                "username": "admin", 
                "password": "admin123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"⚠️  Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  Login error: {e}")
        return None

def create_patients(auth_headers=None):
    """Create test patients"""
    patients = [
        {
            "identifier": [{"use": "official", "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]}, "system": "http://hospital.smarthit.org", "value": "P001-2024"}],
            "name": [{"family": "Johnson", "given": ["Alice", "Marie"], "use": "official"}],
            "active": True,
            "birthDate": "1985-06-15",
            "gender": "female",
            "address": [{
                "use": "home",
                "line": ["123 Main Street", "Apt 4B"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62701",
                "country": "US"
            }],
            "telecom": [
                {"system": "phone", "value": "+1-555-0101", "use": "mobile"},
                {"system": "email", "value": "alice.johnson@email.com", "use": "home"}
            ],
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
            "identifier": [{"use": "official", "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]}, "system": "http://hospital.smarthit.org", "value": "P002-2024"}],
            "name": [{"family": "Smith", "given": ["Robert", "James"], "use": "official"}],
            "active": True,
            "birthDate": "1978-11-22",
            "gender": "male",
            "address": [{
                "use": "home",
                "line": ["456 Oak Avenue"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62702",
                "country": "US"
            }],
            "telecom": [
                {"system": "phone", "value": "+1-555-0201", "use": "mobile"},
                {"system": "email", "value": "robert.smith@email.com", "use": "home"}
            ],
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
            "identifier": [{"use": "official", "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]}, "system": "http://hospital.smarthit.org", "value": "P003-2024"}],
            "name": [{"family": "Williams", "given": ["Emily", "Rose"], "use": "official"}],
            "active": True,
            "birthDate": "1992-03-08",
            "gender": "female",
            "address": [{
                "use": "home",
                "line": ["789 Pine Street"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62703",
                "country": "US"
            }],
            "telecom": [
                {"system": "phone", "value": "+1-555-0301", "use": "mobile"},
                {"system": "email", "value": "emily.williams@email.com", "use": "home"}
            ],
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
            "identifier": [{"use": "official", "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]}, "system": "http://hospital.smarthit.org", "value": "P004-2024"}],
            "name": [{"family": "Brown", "given": ["Michael", "Andrew"], "use": "official"}],
            "active": True,
            "birthDate": "1965-09-14",
            "gender": "male",
            "address": [{
                "use": "home",
                "line": ["321 Elm Drive"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62704",
                "country": "US"
            }],
            "telecom": [
                {"system": "phone", "value": "+1-555-0401", "use": "mobile"},
                {"system": "email", "value": "michael.brown@email.com", "use": "home"}
            ],
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
            "identifier": [{"use": "official", "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]}, "system": "http://hospital.smarthit.org", "value": "P005-2024"}],
            "name": [{"family": "Davis", "given": ["Sarah", "Elizabeth"], "use": "official"}],
            "active": True,
            "birthDate": "1990-12-03",
            "gender": "female",
            "address": [{
                "use": "home",
                "line": ["654 Maple Court"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62705",
                "country": "US"
            }],
            "telecom": [
                {"system": "phone", "value": "+1-555-0501", "use": "mobile"},
                {"system": "email", "value": "sarah.davis@email.com", "use": "home"}
            ],
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
            "identifier": [{"use": "official", "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]}, "system": "http://hospital.smarthit.org", "value": "P006-2024"}],
            "name": [{"family": "Wilson", "given": ["Thomas", "Edward"], "use": "official"}],
            "active": True,
            "birthDate": "1972-07-28",
            "gender": "male",
            "address": [{
                "use": "home",
                "line": ["987 Cedar Lane"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62706",
                "country": "US"
            }],
            "telecom": [
                {"system": "phone", "value": "+1-555-0601", "use": "mobile"},
                {"system": "email", "value": "thomas.wilson@email.com", "use": "home"}
            ],
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    ]
    
    created_patients = []
    headers = {"Content-Type": "application/json"}
    if auth_headers:
        headers.update(auth_headers)
    
    for patient in patients:
        try:
            response = requests.post(
                f"{API_BASE}/healthcare/patients",
                json=patient,
                headers=headers
            )
            if response.status_code in [200, 201]:
                created_patients.append(patient)
                patient_name = f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"
                print(f"✅ Created patient: {patient_name} (ID: {patient['identifier'][0]['value']})")
            else:
                print(f"❌ Failed to create patient: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Failed to create patient: {e}")
    
    return created_patients

def main():
    print("🚀 Healthcare AI Platform - Test Data Creation")
    print("=" * 60)
    
    # Test backend availability
    print("\n🔍 Testing backend availability...")
    if not test_backend():
        print("❌ Backend is not available at http://localhost:8000")
        print("Please start the backend with: python app/main.py")
        return 1
    print("✅ Backend is available")
    
    # Create users
    print("\n👥 Creating test users...")
    created_users = create_users()
    
    # Login as admin
    print("\n🔑 Logging in as admin...")
    auth_headers = login_admin()
    if auth_headers:
        print("✅ Successfully logged in")
    else:
        print("⚠️  Will create patients without authentication")
    
    # Create patients
    print("\n🏥 Creating test patients...")
    created_patients = create_patients(auth_headers)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 Test Data Creation Complete!")
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"• Users created: {len(created_users)}")
    print(f"• Patients created: {len(created_patients)}")
    
    if created_users:
        print(f"\n🔑 Login Credentials:")
        print("-" * 30)
        for user in created_users:
            print(f"Username: {user['username']}")
            print(f"Password: {user['password']}")
            print(f"Role: {user['role']}")
            print("-" * 20)
    
    print(f"\n📝 Next Steps:")
    print("1. Navigate to http://localhost:3000/patients")
    print("2. Login with any of the created users")
    print("3. You should now see the test patients")
    
    print(f"\n🚀 Quick Login (Admin):")
    print("Username: admin")
    print("Password: admin123")
    
    print("\nDone! 🎯")
    return 0

if __name__ == "__main__":
    exit(main())