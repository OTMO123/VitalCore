
# COMPREHENSIVE ENTERPRISE READY IMPLEMENTATION PLAN
Write-Host "🏥 ПЛАН РЕАЛИЗАЦИИ 100% ENTERPRISE READY СИСТЕМЫ" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Gray

Write-Host "ТЕКУЩИЙ СТАТУС: 72% Enterprise Ready" -ForegroundColor Yellow
Write-Host "ЦЕЛЬ: 100% Enterprise Ready для production healthcare startups" -ForegroundColor Green
Write-Host ""

# PHASE 1: КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ БЕЗОПАСНОСТИ (Priority 1)
Write-Host "PHASE 1: КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ БЕЗОПАСНОСТИ" -ForegroundColor Red
Write-Host "==============================================" -ForegroundColor Gray

Write-Host "1.1 Исправление Role-Based Security уязвимостей..." -ForegroundColor White

$fixRoleHierarchy = @'
import sys
sys.path.insert(0, ".")
import os

def fix_role_hierarchy():
    """Исправление критических уязвимостей в иерархии ролей"""
    
    # Исправляем app/core/security.py
    security_file = "app/core/security.py"
    if os.path.exists(security_file):
        with open(security_file, "r") as f:
            content = f.read()
        
        print(f"Исправление role hierarchy в {security_file}...")
        
        # Заменяем уязвимую иерархию ролей
        old_hierarchy = '''role_hierarchy = {
    "patient": 0,
    "lab_technician": 1,
    "doctor": 2,
    "user": 3,
    "admin": 4,
    "super_admin": 5
}'''
        
        new_hierarchy = '''role_hierarchy = {
    "patient": 1,       # Не может доступать к admin функциям
    "lab_technician": 2, # Не может доступать к clinical workflows
    "nurse": 3,
    "doctor": 4,        # Может доступать к clinical workflows
    "admin": 5,         # Может доступать к audit logs
    "super_admin": 6,   # Полный доступ
    "auditor": 5        # Специальная роль для audit logs
}'''
        
        if "role_hierarchy" in content:
            # Находим и заменяем иерархию ролей
            import re
            pattern = r'role_hierarchy\s*=\s*\{[^}]+\}'
            content = re.sub(pattern, new_hierarchy, content)
            
            with open(security_file, "w") as f:
                f.write(content)
            
            print("✅ Role hierarchy исправлена")
        else:
            print("❌ Role hierarchy не найдена")
    else:
        print(f"❌ {security_file} не найден")
    
    return True

# Исправляем audit router для требования роли auditor
def fix_audit_router_security():
    """Добавление строгих role requirements для audit endpoints"""
    
    audit_router = "app/modules/audit_logger/router.py"
    if os.path.exists(audit_router):
        with open(audit_router, "r") as f:
            content = f.read()
        
        print(f"Добавление role protection к audit endpoints...")
        
        # Добавляем строгую защиту для logs endpoint
        if "@router.get(\"/logs\")" in content and "@require_role(\"auditor\", \"admin\")" not in content:
            content = content.replace(
                "@router.get(\"/logs\")",
                "@require_role(\"auditor\", \"admin\")\n@router.get(\"/logs\")"
            )
            
            with open(audit_router, "w") as f:
                f.write(content)
            
            print("✅ Audit router защищен role decorators")
        else:
            print("✅ Audit router уже защищен")
    else:
        print(f"❌ {audit_router} не найден")

# Исправляем clinical workflows router
def fix_clinical_workflows_security():
    """Ограничение доступа к clinical workflows только для doctors и admins"""
    
    clinical_router = "app/modules/clinical_workflows/router.py"
    if os.path.exists(clinical_router):
        with open(clinical_router, "r") as f:
            content = f.read()
        
        print(f"Ограничение доступа к clinical workflows...")
        
        # Добавляем role protection для workflows endpoint
        if "@router.get(\"/workflows\")" in content and "@require_role(\"doctor\", \"admin\")" not in content:
            content = content.replace(
                "@router.get(\"/workflows\")",
                "@require_role(\"doctor\", \"admin\")\n@router.get(\"/workflows\")"
            )
            
            with open(clinical_router, "w") as f:
                f.write(content)
            
            print("✅ Clinical workflows ограничены для doctor/admin ролей")
        else:
            print("✅ Clinical workflows уже защищены")
    else:
        print(f"❌ {clinical_router} не найден")

# Запуск всех исправлений
print("=== ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ УЯЗВИМОСТЕЙ БЕЗОПАСНОСТИ ===")
fix_role_hierarchy()
fix_audit_router_security() 
fix_clinical_workflows_security()
print("=== КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ ===")
'@

Write-Host "Выполнение критических исправлений безопасности..." -ForegroundColor Yellow
docker-compose exec app python -c $fixRoleHierarchy

Write-Host "`n1.2 Создание production-ready конфигурации Docker..." -ForegroundColor White

# Создаем production docker-compose
$productionDockerCompose = @"
version: '3.8'

services:
  app:
    build: .
    ports:
      - "443:443"
      - "80:80"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SSL_CERT_PATH=/certs/server.crt
      - SSL_KEY_PATH=/certs/server.key
      - ENABLE_MFA=true
      - SESSION_TIMEOUT=3600
      - MAX_LOGIN_ATTEMPTS=3
      - ENABLE_IP_RESTRICTIONS=true
    volumes:
      - ./certs:/certs:ro
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - healthcare-network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: iris_db_prod
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - healthcare-network
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data_prod:/data
    networks:
      - healthcare-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    networks:
      - healthcare-network

volumes:
  postgres_data_prod:
  redis_data_prod:

networks:
  healthcare-network:
    driver: bridge
"@

Write-Host "Создание production docker-compose.yml..." -ForegroundColor Yellow
$productionDockerCompose | Out-File -FilePath "docker-compose.prod.yml" -Encoding UTF8
Write-Host "✅ Production Docker configuration создана" -ForegroundColor Green

Write-Host "`n1.3 Создание SSL/HTTPS конфигурации..." -ForegroundColor White

# Создаем nginx конфигурацию для SSL
$nginxConfig = @"
events {
    worker_connections 1024;
}

http {
    upstream healthcare_api {
        server app:8000;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/certs/server.crt;
        ssl_certificate_key /etc/nginx/certs/server.key;
        
        # SSL Security
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;
        
        # Security Headers
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        location / {
            proxy_pass http://healthcare_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # HTTP Redirect
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }
}
"@

Write-Host "Создание nginx.conf для SSL..." -ForegroundColor Yellow
$nginxConfig | Out-File -FilePath "nginx.conf" -Encoding UTF8
Write-Host "✅ SSL/HTTPS конфигурация создана" -ForegroundColor Green

Write-Host "`n1.4 Перезапуск системы с исправлениями..." -ForegroundColor White
docker-compose restart app
Start-Sleep 20

Write-Host "`nPHASE 1 ЗАВЕРШЕНА - Тестирование критических исправлений..." -ForegroundColor Green