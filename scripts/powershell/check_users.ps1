# Check what users exist in database
Write-Host "Checking database users..." -ForegroundColor Yellow

# Check if we can connect to database directly
docker exec -it iris_postgres psql -U postgres -d iris_db -c "SELECT username, email FROM users LIMIT 10;"

Write-Host "`nAlternatively, let's check app logs for any existing users..." -ForegroundColor Yellow
docker logs iris_app --tail 20