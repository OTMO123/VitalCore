#!/usr/bin/env python3
"""
Fix SQLAlchemy Table Definition Conflict - Immunization Model
CRITICAL: This blocks all Phase 2 compliance testing
"""

def fix_immunization_conflicts():
    """Remove duplicate Immunization class definitions to resolve SQLAlchemy conflicts"""
    
    print("=" * 60)
    print("FIXING IMMUNIZATION TABLE DEFINITION CONFLICTS")  
    print("=" * 60)
    
    fixes_applied = []
    
    # Fix 1: Comment out Immunization in database_advanced.py
    print("\n1. Fixing database_advanced.py...")
    try:
        with open("app/core/database_advanced.py", "r") as f:
            content = f.read()
        
        # Find and comment out the Immunization class
        lines = content.split('\n')
        in_immunization_class = False
        modified_lines = []
        
        for line in lines:
            if line.strip().startswith('class Immunization(BaseModel):'):
                in_immunization_class = True
                modified_lines.append(f"# REMOVED: Duplicate Immunization class - use healthcare_records.models instead")
                modified_lines.append(f"# {line}")
                continue
            elif in_immunization_class and line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                # End of class - we've reached a new top-level definition
                in_immunization_class = False
                modified_lines.append(line)
                continue
            elif in_immunization_class:
                modified_lines.append(f"# {line}")
                continue
            else:
                modified_lines.append(line)
        
        with open("app/core/database_advanced.py", "w") as f:
            f.write('\n'.join(modified_lines))
        
        fixes_applied.append("✅ Commented out Immunization in database_advanced.py")
        
    except Exception as e:
        fixes_applied.append(f"❌ Failed to fix database_advanced.py: {str(e)}")
    
    # Fix 2: Comment out Immunization in database_unified.py  
    print("\n2. Fixing database_unified.py...")
    try:
        with open("app/core/database_unified.py", "r") as f:
            content = f.read()
        
        # Find and comment out the Immunization class
        lines = content.split('\n')
        in_immunization_class = False
        modified_lines = []
        
        for line in lines:
            if line.strip().startswith('class Immunization(BaseModel):'):
                in_immunization_class = True
                modified_lines.append(f"# REMOVED: Duplicate Immunization class - use healthcare_records.models instead")
                modified_lines.append(f"# {line}")
                continue
            elif in_immunization_class and line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                # End of class - we've reached a new top-level definition
                in_immunization_class = False
                modified_lines.append(line)
                continue
            elif in_immunization_class:
                modified_lines.append(f"# {line}")
                continue
            else:
                modified_lines.append(line)
        
        with open("app/core/database_unified.py", "w") as f:
            f.write('\n'.join(modified_lines))
        
        fixes_applied.append("✅ Commented out Immunization in database_unified.py")
        
    except Exception as e:
        fixes_applied.append(f"❌ Failed to fix database_unified.py: {str(e)}")
    
    # Fix 3: Update imports to use healthcare_records.models
    print("\n3. Fixing iris_api router import...")
    try:
        with open("app/modules/iris_api/router.py", "r") as f:
            content = f.read()
        
        # Replace the problematic import
        old_import = "from app.core.database_advanced import Patient, Immunization"
        new_import = "from app.modules.healthcare_records.models import Patient, Immunization"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            
            with open("app/modules/iris_api/router.py", "w") as f:
                f.write(content)
                
            fixes_applied.append("✅ Updated iris_api router import")
        else:
            fixes_applied.append("ℹ️ iris_api router import already correct")
        
    except Exception as e:
        fixes_applied.append(f"❌ Failed to fix iris_api router: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("IMMUNIZATION CONFLICT FIX SUMMARY")
    print("=" * 60)
    
    for fix in fixes_applied:
        print(fix)
    
    success_count = len([f for f in fixes_applied if f.startswith("✅")])
    total_fixes = len(fixes_applied)
    
    if success_count == total_fixes or success_count >= 2:
        print(f"\n🎉 Immunization conflicts resolved! ({success_count}/{total_fixes} fixes applied)")
        print("✅ Phase 2 compliance testing should now work")
        print("\n📋 Next step: Run compliance tests:")
        print("   pytest app/tests/compliance/test_soc2_compliance.py -v")
        return True
    else:
        print(f"\n❌ Some fixes failed ({success_count}/{total_fixes} successful)")
        print("⚠️ Manual intervention may be required")
        return False

if __name__ == "__main__":
    fix_immunization_conflicts()