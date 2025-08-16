#!/usr/bin/env python3
"""
Fix Unicode encoding issues in test files
Replace problematic Unicode characters with ASCII equivalents
"""

import os
import sys

def fix_unicode_in_file(filepath):
    """Fix Unicode characters in a Python test file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace Unicode checkmarks and X marks with ASCII
        unicode_fixes = {
            '✅': '[PASS]',
            '❌': '[FAIL]', 
            '⚠️': '[WARN]',
            '✓': '[OK]',
            '✗': '[ERROR]',
            '🚀': '[SUCCESS]',
            '🔒': '[SECURITY]',
            '🏥': '[HEALTHCARE]',
            '📊': '[DATA]',
            '⏭️': '[SKIP]',
            '🎉': '[COMPLETE]'
        }
        
        fixed_content = content
        for unicode_char, ascii_replacement in unicode_fixes.items():
            fixed_content = fixed_content.replace(unicode_char, ascii_replacement)
        
        # Write back the fixed content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"[PASS] Fixed Unicode in: {filepath}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error fixing {filepath}: {e}")
        return False

def main():
    """Fix Unicode issues in test files"""
    print("Fixing Unicode encoding issues in test files...")
    print("=" * 50)
    
    # Files that need Unicode fixes
    test_files = [
        'test_clinical_workflows_complete.py',
        'comprehensive_security_test.py',
        'system_status_final.py'
    ]
    
    fixed_count = 0
    
    for filename in test_files:
        if os.path.exists(filename):
            if fix_unicode_in_file(filename):
                fixed_count += 1
        else:
            print(f"[SKIP] File not found: {filename}")
    
    print(f"\n[SUMMARY] Fixed {fixed_count}/{len(test_files)} files")
    
    # Also set proper encoding for Python
    print("\nSetting Python encoding environment variables...")
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    print("[PASS] PYTHONIOENCODING set to utf-8")
    
    print("\n[COMPLETE] Unicode fixes applied!")
    print("You can now run the test suite without encoding errors.")

if __name__ == "__main__":
    main()