#!/usr/bin/env python3
"""
Debug script to verify UUID generation for HIPAA compliance test
"""
import uuid

# Show what UUIDs are generated for the system users
supervisor_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "supervisor_system"))
compliance_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "compliance_system"))

print(f"supervisor_system UUID: {supervisor_uuid}")
print(f"compliance_system UUID: {compliance_uuid}")

# Show the original strings
print(f"Original supervisor_system: supervisor_system")
print(f"Original compliance_system: compliance_system")