# HEMA3N Frontend Server Startup Script
# Healthcare AI Platform - React TypeScript Interface

Write-Host "Starting HEMA3N Frontend Interface..." -ForegroundColor Green
Write-Host "React 18 + TypeScript + Vite Dev Server" -ForegroundColor Cyan
Write-Host "Google-Style Minimalist Medical UI" -ForegroundColor Cyan

# Set working directory
Set-Location -Path "C:\Users\aurik\Code_Projects\2_scraper\frontend"

Write-Host "Starting Vite dev server on http://localhost:3001..." -ForegroundColor Yellow
Write-Host "Patient Demo: http://localhost:3001/symptom-demo.html" -ForegroundColor Yellow
Write-Host "Doctor Demo: http://localhost:3001/doctor-demo" -ForegroundColor Yellow
Write-Host "Full App: http://localhost:3001/" -ForegroundColor Yellow
Write-Host ""

# Start the frontend development server
npm run dev

Write-Host "Frontend server stopped." -ForegroundColor Red