# Fix Database Configuration - Simple Version
Write-Host "🚀 Fixing Database Configuration..." -ForegroundColor Green

# Step 1: Test config in container
Write-Host "Testing config loading..."
docker exec -it iris_app python3 -c "from app.core.config import Settings; print('Config OK')"

# Step 2: Run migrations
Write-Host "Running database migrations..."
docker exec -it iris_app alembic upgrade head

# Step 3: Check status
Write-Host "Checking migration status..."
docker exec -it iris_app alembic current

Write-Host "✅ Database fix completed!" -ForegroundColor Green