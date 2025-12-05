# VitalCore Docker Deployment Fixes

**Date:** 2025-12-05
**Session:** Full Docker deployment with frontend, backend, and infrastructure

---

## Summary

Successfully deployed VitalCore healthcare AI platform in Docker with:
- FastAPI backend
- React frontend (Vite)
- PostgreSQL 15
- Redis 7
- MinIO object storage

---

## Issues Fixed

### 1. Missing SQL Init Files

**Problem:** Docker compose referenced `init.sql` and `init-enterprise.sql` but files were in `scripts/migrations/`

**Fix:** Copied files to Docker directory
```bash
cp scripts/migrations/init.sql infrastructure/docker/
cp scripts/migrations/init-enterprise.sql infrastructure/docker/
```

---

### 2. Missing Models Directory

**Problem:** AI services required models directory structure

**Fix:** Created directory structure
```bash
mkdir -p models/gemma-3n-medical
mkdir -p models/whisper
mkdir -p models/ner
```

---

### 3. Docker Compose Relative Paths

**Problem:** Build contexts and volume mounts used `.` which resolved to docker directory, not project root

**Files Modified:**
- `infrastructure/docker/docker-compose.yml`
- `infrastructure/docker/docker-compose.frontend.yml`

**Fix:** Changed all relative paths from `.` to `../..`

```yaml
# Before
app:
  build: .
  volumes:
    - .:/app

# After
app:
  build: ../..
  volumes:
    - ../..:/app
```

---

### 4. Port 5432 Conflict

**Problem:** PostgreSQL port 5432 already in use by another project

**File:** `infrastructure/docker/docker-compose.frontend.yml`

**Fix:** Changed external port to 5433
```yaml
ports:
  - "5433:5432"  # Using 5433 to avoid conflict
```

---

### 5. ALLOWED_ORIGINS Format

**Problem:** Pydantic settings expected JSON array, not comma-separated string

**File:** `infrastructure/docker/docker-compose.frontend.yml`

**Fix:**
```yaml
# Before
- ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000

# After
- ALLOWED_ORIGINS=["http://localhost:3000","http://frontend:3000","http://127.0.0.1:3000","http://localhost:5173"]
```

---

### 6. Missing @/lib/utils

**Problem:** shadcn/ui components required `@/lib/utils` with `cn()` function

**Fix:** Created `frontend/src/lib/utils.ts`
```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

### 7. CORS Error - API Base URL

**Problem:** Frontend tried to access `http://app:8000` (Docker internal hostname) from browser

**Files Modified:**
- `infrastructure/docker/docker-compose.frontend.yml`
- `frontend/src/services/api.ts`

**Fix:** Use relative URLs for Vite proxy

```yaml
# docker-compose.frontend.yml
- VITE_API_BASE_URL=
- VITE_WS_URL=/ws
```

```typescript
// api.ts
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const baseURL = apiBaseUrl ? `${apiBaseUrl}/api/v1` : '/api/v1';
```

---

### 8. Login Format Mismatch

**Problem:** Frontend sent form-urlencoded but backend expected JSON

**File:** `frontend/src/services/api.ts`

**Fix:**
```typescript
// Before
async login(username: string, password: string): Promise<ApiResponse> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  const response = await this.client.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  ...
}

// After
async login(username: string, password: string): Promise<ApiResponse> {
  const response = await this.client.post('/auth/login', {
    username,
    password,
  });
  ...
}
```

---

### 9. Bcrypt/Passlib Version Incompatibility

**Problem:** passlib incompatible with newer bcrypt versions, causing password verification to fail

**File:** `app/core/security.py`

**Fix:** Use bcrypt directly instead of passlib

```python
# Before
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(self, password: str) -> str:
    return pwd_context.hash(password)

def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# After
import bcrypt

def hash_password(self, password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
```

---

### 10. Non-existent PyPI Package

**Problem:** `hl7-fhir-r4-core` package doesn't exist on PyPI

**File:** `requirements-ner.txt`

**Fix:** Removed the line (FHIR support provided by `fhir.resources` package)

---

## Demo Users Created

```sql
INSERT INTO users (username, email, password_hash, role, ...)
VALUES
  ('admin', 'admin@vitalcore.local', '<bcrypt_hash>', 'admin', ...),
  ('doctor', 'doctor@vitalcore.local', '<bcrypt_hash>', 'doctor', ...),
  ('nurse', 'nurse@vitalcore.local', '<bcrypt_hash>', 'nurse', ...);
```

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| doctor | operator123 | doctor |
| nurse | viewer123 | nurse |

---

## Services & Ports

| Service | Container | Port | URL |
|---------|-----------|------|-----|
| Frontend | vitalcore_frontend | 5173 | http://localhost:5173 |
| Backend API | iris_app | 8000 | http://localhost:8000 |
| PostgreSQL | iris_postgres | 5433 | localhost:5433 |
| Redis | iris_redis | 6379 | localhost:6379 |
| MinIO | iris_minio | 9000/9001 | http://localhost:9001 |

---

## Commands

### Start Stack
```bash
docker-compose -f infrastructure/docker/docker-compose.frontend.yml up -d db redis minio app frontend
```

### Stop Stack
```bash
docker-compose -f infrastructure/docker/docker-compose.frontend.yml down
```

### View Logs
```bash
docker logs iris_app --tail 50
docker logs vitalcore_frontend --tail 50
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## Files Modified

1. `infrastructure/docker/docker-compose.yml` - Fixed paths
2. `infrastructure/docker/docker-compose.frontend.yml` - Fixed paths, ports, env vars
3. `infrastructure/docker/init.sql` - Copied from migrations
4. `infrastructure/docker/init-enterprise.sql` - Copied from migrations
5. `frontend/src/lib/utils.ts` - Created for shadcn/ui
6. `frontend/src/services/api.ts` - Fixed API URL and login format
7. `app/core/security.py` - Fixed bcrypt compatibility
8. `requirements-ner.txt` - Removed non-existent package
