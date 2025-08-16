#!/usr/bin/env python3
"""
Fix FHIR REST API audit security functionality.
This script restores proper SOC2/HIPAA compliant audit logging that was corrupted.

SECURITY CRITICAL: This script restores essential audit logging for compliance.
"""

import re

def fix_fhir_audit_security():
    """Fix corrupted audit logging calls in FHIR REST API to restore security compliance."""
    
    file_path = "app/modules/healthcare_records/fhir_rest_api.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔒 Restoring SOC2/HIPAA audit security functionality...")
        
        # Pattern 1: Fix CREATE audit (already correctly restored)
        # This one is already correct, skip it
        
        # Pattern 2: Fix corrupted READ audit
        read_pattern = r'(# Create audit log entry\s*\n\s*# Use SOC2 audit service for compliance logging\s*\n\s*try:\s*\n\s*from app\.modules\.audit_logger\.service import SOC2AuditService\s*\n\s*audit_service = SOC2AuditService\(\)\s*\n\s*await audit_service\.log_system_event\(\s*\n\s*event_type="FHIR_RESOURCE_CREATED",\s*\n\s*resource_type=f"fhir_\{resource_type\.lower\(\)\}",\s*\n\s*#\s*operation="READ",\s*\n\s*#\s*record_id=resource_id,\s*\n\s*#\s*old_values=None,\s*\n\s*#\s*new_values=\{"accessed_by": user_id\},\s*\n\s*#\s*user_id=user_id,\s*\n\s*#\s*session_id=None\s*\n\s*#\s*\))'
        
        read_replacement = '''            # Create audit log entry for HIPAA/SOC2 compliance
            await audit_change(
                self.db,
                table_name=f"fhir_{resource_type.lower()}",
                operation="READ",
                record_id=resource_id,
                old_values=None,
                new_values={"accessed_by": user_id},
                user_id=user_id,
                session_id=None
            )'''
        
        content = re.sub(read_pattern, read_replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        # Pattern 3: Fix corrupted UPDATE audit
        update_pattern = r'(# Create audit log entry\s*\n\s*# Use SOC2 audit service for compliance logging\s*\n\s*try:\s*\n\s*from app\.modules\.audit_logger\.service import SOC2AuditService\s*\n\s*audit_service = SOC2AuditService\(\)\s*\n\s*await audit_service\.log_system_event\(\s*\n\s*event_type="FHIR_RESOURCE_CREATED",\s*\n\s*resource_type=f"fhir_\{resource_type\.lower\(\)\}",\s*\n\s*#\s*operation="UPDATE",\s*\n\s*#\s*record_id=resource_id,\s*\n\s*#\s*old_values=old_data,\s*\n\s*#\s*new_values=db_data,\s*\n\s*#\s*user_id=user_id,\s*\n\s*#\s*session_id=None\s*\n\s*#\s*\))'
        
        update_replacement = '''            # Create audit log entry for HIPAA/SOC2 compliance
            await audit_change(
                self.db,
                table_name=f"fhir_{resource_type.lower()}",
                operation="UPDATE",
                record_id=resource_id,
                old_values=old_data,
                new_values=db_data,
                user_id=user_id,
                session_id=None
            )'''
        
        content = re.sub(update_pattern, update_replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        # Pattern 4: Fix corrupted DELETE audit
        delete_pattern = r'(# Create audit log entry\s*\n\s*# Use SOC2 audit service for compliance logging\s*\n\s*try:\s*\n\s*from app\.modules\.audit_logger\.service import SOC2AuditService\s*\n\s*audit_service = SOC2AuditService\(\)\s*\n\s*await audit_service\.log_system_event\(\s*\n\s*event_type="FHIR_RESOURCE_CREATED",\s*\n\s*resource_type=f"fhir_\{resource_type\.lower\(\)\}",\s*\n\s*#\s*operation="DELETE",\s*\n\s*#\s*record_id=resource_id,\s*\n\s*#\s*old_values=old_data,\s*\n\s*#\s*new_values=None,\s*\n\s*#\s*user_id=user_id,\s*\n\s*#\s*session_id=None\s*\n\s*#\s*\))'
        
        delete_replacement = '''            # Create audit log entry for HIPAA/SOC2 compliance
            await audit_change(
                self.db,
                table_name=f"fhir_{resource_type.lower()}",
                operation="DELETE",
                record_id=resource_id,
                old_values=old_data,
                new_values=None,
                user_id=user_id,
                session_id=None
            )'''
        
        content = re.sub(delete_pattern, delete_replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        # Pattern 5: Fix corrupted SEARCH audit (most complex due to mismatched braces)
        search_pattern = r'(# Create audit log entry\s*\n\s*# Use SOC2 audit service for compliance logging\s*\n\s*try:\s*\n\s*from app\.modules\.audit_logger\.service import SOC2AuditService\s*\n\s*audit_service = SOC2AuditService\(\)\s*\n\s*await audit_service\.log_system_event\(\s*\n\s*event_type="FHIR_RESOURCE_CREATED",\s*\n\s*resource_type=f"fhir_search_log",\s*\n\s*#\s*operation="SEARCH",\s*\n\s*#\s*record_id=None,\s*\n\s*#\s*old_values=None,\s*\n\s*#\s*new_values=\{\s*\n\s*"resource_type": search_params\.resource_type,\s*\n\s*"parameters": search_params\.parameters,\s*\n\s*"result_count": len\(results\)\s*\n\s*\},\s*\n\s*#\s*user_id=user_id,\s*\n\s*#\s*session_id=None\s*\n\s*#\s*\))'
        
        search_replacement = '''            # Create audit log entry for HIPAA/SOC2 compliance
            await audit_change(
                self.db,
                table_name=f"fhir_{resource_type.lower()}",
                operation="SEARCH",
                record_id=None,
                old_values=None,
                new_values={
                    "resource_type": search_params.resource_type,
                    "parameters": search_params.parameters,
                    "result_count": len(results)
                },
                user_id=user_id,
                session_id=None
            )'''
        
        content = re.sub(search_pattern, search_replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        # Fix any remaining commented user_id parameters in logger calls
        content = re.sub(r'#\s*user_id=user_id,', 'user_id=user_id,', content)
        
        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Successfully restored SOC2/HIPAA audit security functionality!")
        print("🔐 All database changes will now be properly audited for compliance.")
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to restore audit security - {e}")
        print("⚠️  WARNING: System may not be compliant without proper audit logging!")
        return False

if __name__ == "__main__":
    fix_fhir_audit_security()