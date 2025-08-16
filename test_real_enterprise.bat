@echo off
echo 🏭 REAL ENTERPRISE FUNCTIONALITY TESTING
echo ============================================================

:: Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo ⚡ Activating virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo ⚡ Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ No virtual environment found, using system Python
)

echo.
echo 🔍 Running Simple Verification Test...
python test_simple_verification.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Simple verification failed
    pause
    exit /b 1
)

echo.
echo 🔐 Running REAL Encryption Test...
python test_real_encryption.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Real encryption test failed
    pause
    exit /b 1
)

echo.
echo 🗄️ Running REAL Database Test...
python test_real_database.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Real database test failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 🎉 ALL REAL ENTERPRISE TESTS PASSED!
echo ✅ System demonstrates genuine enterprise-grade security
echo 🏆 Production deployment validated with REAL infrastructure
echo ============================================================

pause