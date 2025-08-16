# Fix Migration Issue and Run Database Setup
Write-Host "🔧 Fixing migration issue..." -ForegroundColor Yellow

# Reset migration state and try again
Write-Host "Resetting migration state..."
docker exec -it iris_app alembic stamp head --sql

Write-Host "Running migrations..."
docker exec -it iris_app alembic upgrade head

Write-Host "Checking current migration..."
docker exec -it iris_app alembic current

Write-Host "✅ Migration fix completed!" -ForegroundColor Green