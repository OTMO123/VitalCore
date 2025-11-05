# File Upload Security Configuration Guide

## Overview

VitalCore implements comprehensive file upload security to prevent:
- **Malware uploads** (Remote Code Execution risk)
- **Storage exhaustion** (Denial of Service risk)
- **Unauthorized file types** (Security risk)
- **File-based attacks** (Path traversal, injection)

## Security Controls Implemented

### 1. File Type Validation (Whitelist)

**Location:** `app/core/validators.py`

**Allowed File Types:**
- Medical Images: `.dcm` (DICOM), `.jpg`, `.jpeg`, `.png`
- Documents: `.pdf`
- Clinical Data: `.xml`, `.json` (FHIR)
- Lab Results: `.hl7`, `.txt`

**How it works:**
```python
from app.core.validators import file_validator

# Validates extension and MIME type
is_valid, error, sanitized_name = file_validator.validate_upload(
    filename="report.pdf",
    content=file_bytes
)
```

### 2. File Size Limits

**Configuration:** `app/core/validators.py::MAX_FILE_SIZES`

**Limits by Type:**
- DICOM (`.dcm`): 500 MB
- PDF (`.pdf`): 100 MB
- Clinical data (`.hl7`, `.xml`, `.json`): 10 MB
- Images (`.jpg`, `.png`): 50 MB
- Default: 50 MB

**Customization:**
```python
# In app/core/validators.py
MAX_FILE_SIZES = {
    '.dcm': 500 * 1024 * 1024,  # Adjust as needed
    '.pdf': 100 * 1024 * 1024,
    # ...
}
```

### 3. Rate Limiting

**Location:** `app/modules/document_management/router.py`

**Default:** 10 uploads per minute per IP

**Applied to:**
```python
@router.post("/upload")
@rate_limit(max_requests=10, window_seconds=60)
async def upload_document(...):
    ...
```

**Customization:**
```python
# Strict: 5 uploads per minute
@rate_limit(max_requests=5, window_seconds=60)

# Generous: 30 uploads per minute
@rate_limit(max_requests=30, window_seconds=60)
```

### 4. Filename Sanitization

**Automatic:** All filenames are sanitized to prevent:
- Path traversal (`../../etc/passwd`)
- Command injection (`file;rm -rf`)
- Null byte attacks (`file\x00.pdf`)

**Example:**
```python
# Input: "../../etc/passwd.pdf"
# Output: "passwd.pdf"

# Input: "test<script>.pdf"
# Output: "test_script_.pdf"
```

### 5. Malware Scanning

**Location:** `app/core/security_scanning.py`

**Default:** NoOp scanner (logs warning)

**Production Options:**

#### Option A: ClamAV (Recommended for self-hosted)

```bash
# 1. Install ClamAV
sudo apt-get install clamav clamav-daemon

# 2. Install Python client
pip install pyclamd

# 3. Start ClamAV daemon
sudo systemctl start clamav-daemon

# 4. Configure in application
# In app/main.py or startup script:
from app.core.security_scanning import configure_scanner, ClamAVScanner

configure_scanner(ClamAVScanner(host="localhost", port=3310))
```

#### Option B: VirusTotal (Cloud-based)

```bash
# 1. Get API key from https://www.virustotal.com/

# 2. Install Python client
pip install vt-py

# 3. Configure in application
from app.core.security_scanning import configure_scanner, VirusTotalScanner

configure_scanner(VirusTotalScanner(api_key=settings.virustotal_api_key))
```

#### Option C: Hash-Based Scanner (Lightweight)

```python
from app.core.security_scanning import configure_scanner, HashBasedScanner

scanner = HashBasedScanner()

# Add known malware hashes from threat intelligence feeds
scanner.add_malware_hash("a123456...")  # SHA256 hash

configure_scanner(scanner)
```

## Security Flow

```
User Upload
    ↓
[1] Rate Limit Check (10/min)
    ↓
[2] File Type Validation (whitelist)
    ↓
[3] File Size Check (type-specific limits)
    ↓
[4] MIME Type Verification (magic numbers)
    ↓
[5] Filename Sanitization
    ↓
[6] Malware Scan (if configured)
    ↓
[7] Encryption at Rest (AES-256)
    ↓
[8] Storage + Audit Log
    ↓
Success Response
```

## Testing

Run security tests:

```bash
# Run all security tests
pytest app/tests/core/document_management/test_file_upload_security.py -v -m security

# Run specific test class
pytest app/tests/core/document_management/test_file_upload_security.py::TestFileTypeValidation -v

# Run with coverage
pytest app/tests/core/document_management/test_file_upload_security.py --cov=app.core.validators --cov=app.core.security_scanning
```

## API Response

Successful upload response includes security validation status:

```json
{
  "id": "uuid",
  "status": "uploaded",
  "filename": "patient_report.pdf",
  "original_filename": "Patient Report (Final).pdf",
  "file_size": 1048576,
  "security_checks": {
    "file_type_validated": true,
    "file_size_validated": true,
    "filename_sanitized": true,
    "malware_scanned": true,
    "encrypted": true
  },
  "message": "Document uploaded successfully with comprehensive security validation"
}
```

## Error Responses

### File Type Rejected
```json
{
  "detail": "File upload rejected: File type not allowed. Extension: .exe"
}
```

### File Too Large
```json
{
  "detail": "File upload rejected: File too large. Size: 150.0MB, Max: 100.0MB for .pdf files"
}
```

### Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Max 10 requests per 60 seconds."
}
```

### Malware Detected
```json
{
  "detail": "File upload rejected: Malware detected: Trojan.Generic"
}
```

## Monitoring and Alerts

All security events are logged with structured logging:

```python
# File validation failure
logger.warning(
    "File upload rejected - validation failed",
    filename=file.filename,
    error=validation_error,
    user_id=str(current_user_id)
)

# Malware detection
logger.error(
    "Malware detected in uploaded file",
    filename=sanitized_filename,
    threat=threat_info,
    user_id=str(current_user_id),
    patient_id=patient_id
)

# Rate limit exceeded
logger.warning(
    "Rate limit exceeded",
    client_ip=client_ip,
    endpoint=request.url.path
)
```

## Compliance

These security controls help meet:

- **HIPAA Security Rule** - § 164.308(a)(5)(ii)(B) - Protection from malicious software
- **HIPAA Security Rule** - § 164.312(a)(1) - Access controls
- **SOC 2 Type II** - CC6.6 - Protection against malicious software
- **SOC 2 Type II** - CC7.2 - System monitoring
- **NIST 800-53** - SI-3 - Malicious Code Protection

## Production Checklist

- [ ] Configure production malware scanner (ClamAV or VirusTotal)
- [ ] Adjust rate limits based on expected usage
- [ ] Monitor security event logs
- [ ] Set up alerts for repeated validation failures
- [ ] Review and update file type whitelist as needed
- [ ] Test with actual healthcare file formats (DICOM, HL7, FHIR)
- [ ] Configure automated malware signature updates (ClamAV)
- [ ] Document file upload limits for users
- [ ] Implement file upload monitoring dashboard

## Support

For issues or questions:
- Review logs: `logger.warning/error` messages
- Check ClamAV status: `sudo systemctl status clamav-daemon`
- Verify configuration: `from app.core.security_scanning import get_scanner`
- Test validation: `pytest test_file_upload_security.py -v`

## Future Enhancements

Planned improvements:
- [ ] Deep content inspection for PDFs
- [ ] Image analysis for embedded threats
- [ ] Integration with threat intelligence feeds
- [ ] Automated quarantine for suspicious files
- [ ] Machine learning-based anomaly detection
- [ ] S3 bucket scanning integration
- [ ] Real-time file reputation checking
