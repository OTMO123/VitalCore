#!/usr/bin/env python3
"""
Fix Role Import Issues in Test Files
Fixes missing Role enum imports and references in test files
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def find_test_files_with_role_issues() -> List[Path]:
    """Find all test files that reference 'Role' but don't import it"""
    test_files = []
    
    # Search patterns for test files
    patterns = [
        "app/modules/clinical_workflows/tests/**/*.py",
        "app/tests/**/*.py"
    ]
    
    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_file() and path.name.endswith('.py'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check if file uses Role but doesn't import it
                    if 'Role.' in content and 'from' not in content and 'import' not in content:
                        test_files.append(path)
                    elif 'Role.' in content and 'UserRole' not in content:
                        test_files.append(path)
                        
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    
    return test_files

def fix_role_imports_in_file(file_path: Path) -> bool:
    """Fix Role imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if file needs UserRole import
        if 'Role.' in content:
            # Add the import if not present
            if 'from app.core.database_unified import' in content:
                # Add UserRole to existing import
                content = re.sub(
                    r'(from app\.core\.database_unified import[^)]+)',
                    r'\1, UserRole',
                    content
                )
            elif 'import' in content and 'from' in content:
                # Add new import line after other imports
                import_lines = []
                other_lines = []
                in_imports = True
                
                for line in content.split('\n'):
                    if line.strip().startswith(('import ', 'from ')) and in_imports:
                        import_lines.append(line)
                    elif line.strip() == '' and in_imports:
                        import_lines.append(line)
                    else:
                        if in_imports:
                            import_lines.append('from app.core.database_unified import UserRole')
                            import_lines.append('')
                            in_imports = False
                        other_lines.append(line)
                
                content = '\n'.join(import_lines + other_lines)
            else:
                # Add import at the beginning
                content = 'from app.core.database_unified import UserRole\n\n' + content
            
            # Replace Role references with UserRole
            content = re.sub(r'\bRole\.', 'UserRole.', content)
            content = re.sub(r'\bRole\b(?!\.)', 'UserRole', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed Role imports in {file_path}")
            return True
        else:
            print(f"ℹ️ No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def fix_conftest_files():
    """Fix conftest.py files specifically"""
    conftest_files = [
        Path("app/modules/clinical_workflows/tests/conftest.py"),
        Path("app/tests/conftest.py")
    ]
    
    for conftest_file in conftest_files:
        if conftest_file.exists():
            try:
                with open(conftest_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add UserRole import if not present
                if 'UserRole' not in content and 'database_unified' in content:
                    # Find the database_unified import line
                    content = re.sub(
                        r'(from app\.core\.database_unified import[^)]+)',
                        r'\1, UserRole',
                        content
                    )
                elif 'UserRole' not in content:
                    # Add new import
                    lines = content.split('\n')
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith('from app.'):
                            insert_index = i + 1
                    
                    lines.insert(insert_index, 'from app.core.database_unified import UserRole')
                    content = '\n'.join(lines)
                
                # Add UserRole fixtures
                if '@pytest.fixture' in content and 'def user_' not in content:
                    fixture_code = '''

# ======================== USER ROLE FIXTURES ========================

@pytest.fixture
def admin_user_data():
    """Test data for admin user."""
    return {
        "email": "admin@test.com",
        "username": "admin",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "is_active": True
    }

@pytest.fixture
def physician_user_data():
    """Test data for physician user."""
    return {
        "email": "physician@test.com", 
        "username": "physician",
        "password": "physician123",
        "role": UserRole.USER,  # Physicians are typically USER role with specific permissions
        "is_active": True
    }

@pytest.fixture
def nurse_user_data():
    """Test data for nurse user."""
    return {
        "email": "nurse@test.com",
        "username": "nurse", 
        "password": "nurse123",
        "role": UserRole.OPERATOR,
        "is_active": True
    }
'''
                    content += fixture_code
                
                with open(conftest_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed conftest.py: {conftest_file}")
                
            except Exception as e:
                print(f"❌ Error fixing conftest {conftest_file}: {e}")

def create_role_alias_file():
    """Create a role alias file for backward compatibility"""
    alias_content = '''"""
Role Alias for Backward Compatibility
Provides Role alias for UserRole to fix import issues
"""

from app.core.database_unified import UserRole

# Backward compatibility alias
Role = UserRole

# Export for easy import
__all__ = ['Role', 'UserRole']
'''
    
    alias_file = Path("app/core/role_alias.py")
    with open(alias_file, 'w', encoding='utf-8') as f:
        f.write(alias_content)
    print(f"✅ Created role alias file: {alias_file}")

def fix_specific_test_files():
    """Fix specific test files that are known to have Role issues"""
    files_to_fix = [
        "app/modules/clinical_workflows/tests/e2e/test_complete_workflow_e2e.py",
        "app/modules/clinical_workflows/tests/integration/test_api_integration.py", 
        "app/modules/clinical_workflows/tests/performance/test_api_performance.py",
        "app/modules/clinical_workflows/tests/unit/test_service_unit.py",
        "app/modules/clinical_workflows/tests/test_models_validation.py",
        "app/modules/clinical_workflows/tests/test_schemas_validation.py"
    ]
    
    for file_path in files_to_fix:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add import if missing
                if 'Role' in content and 'from app.core.database_unified import' not in content:
                    # Add import at the top
                    lines = content.split('\n')
                    
                    # Find where to insert import
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith('from app.') or line.startswith('import '):
                            insert_index = i + 1
                    
                    lines.insert(insert_index, 'from app.core.database_unified import UserRole as Role')
                    content = '\n'.join(lines)
                    
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Fixed Role import in {path}")
                    
            except Exception as e:
                print(f"❌ Error fixing {path}: {e}")

def main():
    """Main function to fix all Role import issues"""
    print("🔧 Fixing Role import issues in test files...")
    print("=" * 50)
    
    # Create role alias for backward compatibility
    create_role_alias_file()
    
    # Fix conftest files
    fix_conftest_files()
    
    # Fix specific test files
    fix_specific_test_files()
    
    # Find and fix other test files
    test_files = find_test_files_with_role_issues()
    
    fixed_count = 0
    for file_path in test_files:
        if fix_role_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Role import fixes completed!")
    print(f"✅ Fixed {fixed_count} files")
    print(f"📁 Created role alias file for backward compatibility")
    print("\nNext steps:")
    print("1. Run: python -m pytest app/modules/clinical_workflows/tests/ -v")
    print("2. Check for any remaining Role import errors")

if __name__ == "__main__":
    main()