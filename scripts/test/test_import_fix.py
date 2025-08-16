#!/usr/bin/env python3
"""Test script to verify ML dependencies are handled gracefully."""

try:
    print("Testing app.main import...")
    import app.main
    print("✅ SUCCESS: app.main imported successfully")
    
    print("\nTesting Clinical BERT service...")
    from app.modules.ml_prediction.clinical_bert import ClinicalBERTService, ML_DEPENDENCIES_AVAILABLE
    
    print(f"ML Dependencies Available: {ML_DEPENDENCIES_AVAILABLE}")
    
    # Test service initialization
    service = ClinicalBERTService()
    print("✅ SUCCESS: ClinicalBERTService initialized")
    
    print("\nAll import tests passed - Healthcare Backend should start successfully!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()