# Set environment variables persistently for current user
# This will make them available in all new PowerShell sessions

$env:SECRET_KEY='hdMDdXQL8IZLczsjO94pKoKTCvHjCndVhM8vxgs+5azV1Xd6dyi2GyAuqrIT2fhoG2OIK+fVD9FMY+yfVaUFZw=='
$env:ENCRYPTION_KEY='4fcDOtTDpMdJ1kP8D+Hyv2TQkxk2N1sKpQfHp+cseWo='
$env:JWT_SECRET_KEY='cP0PU0PCPH9GPQwANXGQoYri/3vR+WHOdvG4LUMhjkayGWHcWXxWOPFkruHjZr2idkpHE3QZMkIcW6xN4ZncEg=='
$env:DATABASE_URL='postgresql://postgres:password@localhost:5432/iris_db'
$env:REDIS_URL='redis://localhost:6379/0'
$env:PHI_ENCRYPTION_KEY='kOOX16lKKs9sQVdTc+RTP3zhCinjIyXujgkmu1ijZ0s='
$env:MINIO_ACCESS_KEY='M5vI4GfN7HzJ0imDjP4g'
$env:MINIO_SECRET_KEY='/VPZbAacxAWRYD1fu5o0PE0Zd1DTIT6iPrhcwNob5g3ykTqwL8Ofuw=='
$env:AUDIT_SIGNING_KEY='3f8414129be81b54a92655b417f9a4c7632212f2f28078c03cb8e3d705c229e83c9e2ea86de33725301f9a9fe6810f08589fa78441b3f92481cad22decf6874e'
$env:SOC2_COMPLIANCE_MODE='true'

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "Now run: .\scripts\deployment_tests\quick_test.ps1" -ForegroundColor Cyan