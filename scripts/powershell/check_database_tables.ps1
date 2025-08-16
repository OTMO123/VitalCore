# Check what tables exist in the database
Write-Host "Checking database structure..." -ForegroundColor Yellow

# Check all tables
Write-Host "All tables in database:" -ForegroundColor Cyan
docker exec -it iris_postgres psql -U postgres -d iris_db -c "\dt"

Write-Host "`nChecking if patients table exists:" -ForegroundColor Cyan
docker exec -it iris_postgres psql -U postgres -d iris_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%patient%';"

Write-Host "`nChecking table structure if patients table exists:" -ForegroundColor Cyan
docker exec -it iris_postgres psql -U postgres -d iris_db -c "\d patients" 2>$null

Write-Host "`nChecking all enum types:" -ForegroundColor Cyan
docker exec -it iris_postgres psql -U postgres -d iris_db -c "SELECT typname FROM pg_type WHERE typtype = 'e';"

Write-Host "`nChecking migration history:" -ForegroundColor Cyan
docker exec -it iris_postgres psql -U postgres -d iris_db -c "SELECT * FROM alembic_version;"

Write-Host "`nDatabase check completed!" -ForegroundColor Green