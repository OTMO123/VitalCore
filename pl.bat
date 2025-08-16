@echo off
REM =====================================================
REM IRIS Healthcare API - Pipeline Launcher (Batch)
REM Quick batch launcher for CI/CD pipeline operations
REM =====================================================

setlocal

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Check if PowerShell is available
powershell -Command "exit 0" >nul 2>&1
if errorlevel 1 (
    echo ❌ PowerShell is not available or accessible
    echo Please ensure PowerShell is installed and in your PATH
    exit /b 1
)

REM Execute the PowerShell launcher with all arguments
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%pl.ps1" %*

REM Exit with the same code as PowerShell
exit /b %errorlevel%