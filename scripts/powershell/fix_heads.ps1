# Fix Multiple Heads Issue
Write-Host "Fixing multiple heads issue..." -ForegroundColor Yellow

# Show all heads
Write-Host "Current heads:"
docker exec -it iris_app alembic heads

# Merge heads into single head
Write-Host "Merging heads..."
docker exec -it iris_app alembic merge heads -m "merge_multiple_heads"

# Now upgrade to the merged head
Write-Host "Upgrading to merged head..."
docker exec -it iris_app alembic upgrade head

Write-Host "Multiple heads fix completed!" -ForegroundColor Green