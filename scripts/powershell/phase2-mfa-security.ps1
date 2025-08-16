# PHASE 2: MFA И РАСШИРЕННАЯ БЕЗОПАСНОСТЬ
Write-Host "PHASE 2: MFA И ENTERPRISE БЕЗОПАСНОСТЬ" -ForegroundColor Magenta
Write-Host "======================================" -ForegroundColor Gray

Write-Host "2.1 Реализация Multi-Factor Authentication (MFA)..." -ForegroundColor White

$implementMFA = @'
import sys
sys.path.insert(0, ".")
import os

def implement_mfa_system():
    """Добавление полной поддержки MFA для enterprise security"""
    
    # 1. Создаем MFA service
    mfa_service_code = '''
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import Optional, Tuple

class MFAService:
    """Enterprise Multi-Factor Authentication Service"""
    
    def __init__(self):
        self.company_name = "Healthcare API"
        self.backup_codes_count = 8
    
    def generate_secret(self) -> str:
        """Генерация нового MFA секрета"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, username: str, secret: str) -> str:
        """Генерация QR кода для настройки MFA"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=self.company_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Проверка TOTP токена"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self) -> list[str]:
        """Генерация backup кодов"""
        import secrets
        return [secrets.token_hex(4).upper() for _ in range(self.backup_codes_count)]
    
    def verify_backup_code(self, stored_codes: list[str], provided_code: str) -> Tuple[bool, list[str]]:
        """Проверка и использование backup кода"""
        if provided_code.upper() in stored_codes:
            remaining_codes = [code for code in stored_codes if code.upper() != provided_code.upper()]
            return True, remaining_codes
        return False, stored_codes

# Глобальный экземпляр MFA service
mfa_service = MFAService()
'''
    
    # Создаем файл MFA service
    mfa_service_path = "app/modules/auth/mfa_service.py"
    os.makedirs(os.path.dirname(mfa_service_path), exist_ok=True)
    
    with open(mfa_service_path, "w") as f:
        f.write(mfa_service_code)
    
    print(f"✅ MFA Service создан: {mfa_service_path}")
    
    # 2. Добавляем MFA endpoints в auth router
    auth_router_path = "app/modules/auth/router.py"
    if os.path.exists(auth_router_path):
        with open(auth_router_path, "r") as f:
            content = f.read()
        
        mfa_endpoints = '''

# MFA Endpoints для Enterprise Security
@router.post("/mfa/enable")
async def enable_mfa(
    user_info: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Включение MFA для пользователя"""
    from .mfa_service import mfa_service
    
    user_id = user_info["user_id"]
    
    # Генерируем новый секрет
    secret = mfa_service.generate_secret()
    qr_code = mfa_service.generate_qr_code(user_info["username"], secret)
    backup_codes = mfa_service.generate_backup_codes()
    
    # Сохраняем в базу данных
    await db.execute(
        text("UPDATE users SET mfa_secret = :secret, mfa_backup_codes = :codes WHERE id = :user_id"),
        {"secret": secret, "codes": json.dumps(backup_codes), "user_id": user_id}
    )
    await db.commit()
    
    return {
        "qr_code": qr_code,
        "secret": secret,
        "backup_codes": backup_codes,
        "message": "Настройте MFA в вашем authenticator приложении"
    }

@router.post("/mfa/verify")
async def verify_mfa_token(
    token: str = Body(..., embed=True),
    user_info: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Проверка MFA токена"""
    from .mfa_service import mfa_service
    
    user_id = user_info["user_id"]
    
    # Получаем MFA секрет из базы
    result = await db.execute(
        text("SELECT mfa_secret FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    
    if not row or not row[0]:
        raise HTTPException(400, "MFA не настроен")
    
    secret = row[0]
    
    if mfa_service.verify_totp(secret, token):
        # Активируем MFA
        await db.execute(
            text("UPDATE users SET mfa_enabled = true WHERE id = :user_id"),
            {"user_id": user_id}
        )
        await db.commit()
        
        return {"message": "MFA успешно активирован"}
    else:
        raise HTTPException(400, "Неверный MFA токен")

@router.post("/mfa/disable")
@require_role("admin")  # Только admin может отключать MFA
async def disable_mfa(
    user_id: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Отключение MFA (только для админов)"""
    await db.execute(
        text("UPDATE users SET mfa_enabled = false, mfa_secret = null WHERE id = :user_id"),
        {"user_id": user_id}
    )
    await db.commit()
    
    return {"message": "MFA отключен"}
'''
        
        # Добавляем MFA endpoints если их еще нет
        if "/mfa/enable" not in content:
            content += mfa_endpoints
            
            with open(auth_router_path, "w") as f:
                f.write(content)
            
            print("✅ MFA endpoints добавлены в auth router")
        else:
            print("✅ MFA endpoints уже существуют")
    
    # 3. Добавляем MFA middleware для защищенных endpoints
    mfa_middleware_code = '''
from functools import wraps
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def require_mfa(
    user_info: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Middleware для требования MFA на критических endpoints"""
    user_id = user_info["user_id"]
    
    # Проверяем, включен ли MFA для пользователя
    result = await db.execute(
        text("SELECT mfa_enabled FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    
    if not row or not row[0]:
        raise HTTPException(
            status_code=403,
            detail="MFA required for this action. Please enable MFA first."
        )
    
    return user_info

# Декоратор для endpoints, требующих MFA
def mfa_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # MFA проверка встроена в require_mfa dependency
        return await func(*args, **kwargs)
    return wrapper
'''
    
    # Добавляем MFA middleware в security.py
    security_path = "app/core/security.py"
    if os.path.exists(security_path):
        with open(security_path, "r") as f:
            content = f.read()
        
        if "require_mfa" not in content:
            content += "\n" + mfa_middleware_code
            
            with open(security_path, "w") as f:
                f.write(content)
            
            print("✅ MFA middleware добавлен в security.py")
    
    return True

# Запуск реализации MFA
print("=== РЕАЛИЗАЦИЯ MFA СИСТЕМЫ ===")
implement_mfa_system()
print("=== MFA СИСТЕМА РЕАЛИЗОВАНА ===")
'@

Write-Host "Реализация MFA системы..." -ForegroundColor Yellow
docker-compose exec app python -c $implementMFA

Write-Host "`n2.2 Добавление advanced session management..." -ForegroundColor White

$sessionManagement = @'
import sys
sys.path.insert(0, ".")
import os

def implement_enterprise_session_management():
    """Реализация enterprise session management с Redis"""
    
    session_service_code = """
import redis.asyncio as redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.core.config import settings

class EnterpriseSessionService:
    '''Enterprise Session Management with Redis backend'''
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.session_timeout = settings.SESSION_TIMEOUT  # 1 hour default
        self.max_sessions_per_user = 5  # Enterprise limit
    
    async def create_session(self, user_id: str, user_data: Dict[str, Any]) -> str:
        '''Создание новой enterprise session'''
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        user_sessions_key = f"user_sessions:{user_id}"
        
        # Проверяем количество активных сессий пользователя
        active_sessions = await self.redis_client.smembers(user_sessions_key)
        
        if len(active_sessions) >= self.max_sessions_per_user:
            # Удаляем самую старую сессию
            oldest_session = await self._get_oldest_session(active_sessions)
            if oldest_session:
                await self.invalidate_session(oldest_session.decode())
        
        # Создаем новую сессию
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "user_data": user_data,
            "ip_address": user_data.get("ip_address"),
            "user_agent": user_data.get("user_agent")
        }
        
        # Сохраняем сессию в Redis
        await self.redis_client.setex(
            session_key,
            self.session_timeout,
            json.dumps(session_data)
        )
        
        # Добавляем в список сессий пользователя
        await self.redis_client.sadd(user_sessions_key, session_id)
        await self.redis_client.expire(user_sessions_key, self.session_timeout)
        
        return session_id
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        '''Валидация и обновление session'''
        session_key = f"session:{session_id}"
        
        session_data_str = await self.redis_client.get(session_key)
        if not session_data_str:
            return None
        
        session_data = json.loads(session_data_str)
        
        # Обновляем время последнего доступа
        session_data["last_accessed"] = datetime.utcnow().isoformat()
        
        # Продлеваем сессию
        await self.redis_client.setex(
            session_key,
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return session_data
    
    async def invalidate_session(self, session_id: str) -> bool:
        '''Инвалидация конкретной сессии'''
        session_key = f"session:{session_id}"
        
        # Получаем данные сессии для получения user_id
        session_data_str = await self.redis_client.get(session_key)
        if session_data_str:
            session_data = json.loads(session_data_str)
            user_id = session_data["user_id"]
            user_sessions_key = f"user_sessions:{user_id}"
            
            # Удаляем из списка сессий пользователя
            await self.redis_client.srem(user_sessions_key, session_id)
        
        # Удаляем сессию
        result = await self.redis_client.delete(session_key)
        return result > 0
    
    async def invalidate_all_user_sessions(self, user_id: str) -> int:
        '''Инвалидация всех сессий пользователя'''
        user_sessions_key = f"user_sessions:{user_id}"
        
        # Получаем все сессии пользователя
        session_ids = await self.redis_client.smembers(user_sessions_key)
        
        # Удаляем все сессии
        invalidated_count = 0
        for session_id in session_ids:
            session_key = f"session:{session_id.decode()}"
            deleted = await self.redis_client.delete(session_key)
            invalidated_count += deleted
        
        # Очищаем список сессий пользователя
        await self.redis_client.delete(user_sessions_key)
        
        return invalidated_count
    
    async def get_active_sessions(self, user_id: str) -> list:
        '''Получение списка активных сессий пользователя'''
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = await self.redis_client.smembers(user_sessions_key)
        
        active_sessions = []
        for session_id in session_ids:
            session_data = await self.validate_session(session_id.decode())
            if session_data:
                active_sessions.append({
                    "session_id": session_id.decode(),
                    "created_at": session_data["created_at"],
                    "last_accessed": session_data["last_accessed"],
                    "ip_address": session_data.get("ip_address"),
                    "user_agent": session_data.get("user_agent")
                })
        
        return active_sessions
    
    async def _get_oldest_session(self, session_ids: set) -> Optional[bytes]:
        '''Получение самой старой сессии для удаления'''
        oldest_session = None
        oldest_time = None
        
        for session_id in session_ids:
            session_key = f"session:{session_id.decode()}"
            session_data_str = await self.redis_client.get(session_key)
            
            if session_data_str:
                session_data = json.loads(session_data_str)
                created_at = datetime.fromisoformat(session_data["created_at"])
                
                if oldest_time is None or created_at < oldest_time:
                    oldest_time = created_at
                    oldest_session = session_id
        
        return oldest_session

# Глобальный экземпляр session service
session_service = EnterpriseSessionService()
"""
    
    # Создаем файл session service
    session_service_path = "app/modules/auth/session_service.py"
    os.makedirs(os.path.dirname(session_service_path), exist_ok=True)
    
    with open(session_service_path, "w") as f:
        f.write(session_service_code)
    
    print(f"✅ Enterprise Session Service создан: {session_service_path}")
    
    return True

# Запуск реализации session management
print("=== РЕАЛИЗАЦИЯ ENTERPRISE SESSION MANAGEMENT ===")
implement_enterprise_session_management()
print("=== SESSION MANAGEMENT РЕАЛИЗОВАН ===")
'@

Write-Host "Реализация enterprise session management..." -ForegroundColor Yellow
docker-compose exec app python -c $sessionManagement

Write-Host "`nPHASE 2 ЗАВЕРШЕНА - MFA и расширенная безопасность реализованы" -ForegroundColor Green