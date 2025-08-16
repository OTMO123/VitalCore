# Windows PowerShell Commands for Final Integration

## Step 1: Apply Database Migration
```powershell
# You're already in the virtual environment (venv), so run:
python -m alembic upgrade head
```

## Step 2: Run Targeted Endpoint Tests
```powershell
# Run the endpoint fixer script
python fix_remaining_endpoints.py
```

## Step 3: Start Backend Server (if needed)
```powershell
# Start the FastAPI backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

## Step 4: Run Full Integration Test
```powershell
# Run the complete SOC2 integration test
python test_frontend_integration_soc2.py
```

## Alternative Commands if Above Don't Work

### If alembic module not found:
```powershell
# Install alembic first
pip install alembic

# Then run migration
python -m alembic upgrade head
```

### If uvicorn module not found:
```powershell
# Install uvicorn
pip install uvicorn

# Then start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

### Check if you have the right Python environment:
```powershell
# Verify you're in the right environment
python --version
pip list | findstr alembic
pip list | findstr uvicorn
```

## Database Connection Check
```powershell
# If you need to check database connection
python -c "import asyncpg; print('asyncpg available')"
```

## Quick Fix Commands
```powershell
# Install all required packages at once
pip install uvicorn fastapi sqlalchemy asyncpg alembic pydantic structlog

# Then run the migration
python -m alembic upgrade head

# Start backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

# In another terminal, run the tests
python fix_remaining_endpoints.py
```