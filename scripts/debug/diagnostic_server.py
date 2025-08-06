#!/usr/bin/env python3
"""
Диагностический сервер для IRIS API с расширенным логированием
Запускается без внешних зависимостей для диагностики проблем
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Настройка расширенного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/iris_diagnostic.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('IRIS_DIAGNOSTIC')

class DiagnosticHandler(BaseHTTPRequestHandler):
    """Обработчик для диагностики проблем с аутентификацией"""
    
    def log_request_details(self):
        """Детальное логирование запроса"""
        logger.info("=" * 80)
        logger.info(f"🔍 DIAGNOSTIC REQUEST: {self.command} {self.path}")
        logger.info(f"📍 Client: {self.client_address}")
        logger.info(f"🕐 Timestamp: {datetime.now().isoformat()}")
        
        # Логирование заголовков
        logger.info("📋 Headers:")
        for header, value in self.headers.items():
            if 'authorization' in header.lower():
                logger.info(f"  {header}: Bearer [TOKEN_HIDDEN]")
            else:
                logger.info(f"  {header}: {value}")
        
        # Логирование query параметров
        parsed_url = urlparse(self.path)
        if parsed_url.query:
            query_params = parse_qs(parsed_url.query)
            logger.info(f"🔗 Query params: {query_params}")
        
        logger.info("=" * 80)
    
    def send_diagnostic_response(self, status_code, data, message=""):
        """Отправка диагностического ответа"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response = {
            "diagnostic_mode": True,
            "timestamp": datetime.now().isoformat(),
            "status": status_code,
            "message": message,
            "data": data,
            "server_info": {
                "version": "1.0.0-diagnostic",
                "mode": "DIAGNOSTIC_SERVER",
                "issues_detected": self.get_system_issues()
            }
        }
        
        response_json = json.dumps(response, indent=2)
        self.wfile.write(response_json.encode())
        
        logger.info(f"📤 Response sent: {status_code} - {message}")
    
    def get_system_issues(self):
        """Диагностика системных проблем"""
        issues = []
        
        # Проверка Python пакетов
        try:
            import fastapi
        except ImportError:
            issues.append("FastAPI not installed")
        
        try:
            import uvicorn
        except ImportError:
            issues.append("Uvicorn not installed")
        
        try:
            import asyncpg
        except ImportError:
            issues.append("AsyncPG not installed")
        
        try:
            import sqlalchemy
        except ImportError:
            issues.append("SQLAlchemy not installed")
        
        # Проверка файлов конфигурации
        import os
        if not os.path.exists('.env'):
            issues.append(".env file missing")
        
        if not os.path.exists('app/'):
            issues.append("app/ directory missing")
        
        return issues
    
    def do_GET(self):
        """Обработка GET запросов"""
        self.log_request_details()
        
        if self.path == '/health':
            self.send_diagnostic_response(200, 
                {"status": "diagnostic_mode"}, 
                "Diagnostic server running - main server issues detected")
        
        elif self.path == '/api/v1/auth/status':
            self.send_diagnostic_response(503, 
                {"auth_status": "unavailable", "reason": "main_server_down"}, 
                "Authentication service unavailable - server not running")
        
        elif self.path.startswith('/api/v1/auth'):
            self.send_diagnostic_response(503, 
                {"error": "service_unavailable"}, 
                "Main IRIS server not running - check dependencies and database")
        
        else:
            self.send_diagnostic_response(200, 
                {"diagnostic": "unknown_endpoint", "path": self.path}, 
                "Diagnostic server - endpoint not recognized")
    
    def do_POST(self):
        """Обработка POST запросов (включая логин)"""
        self.log_request_details()
        
        # Чтение тела запроса
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        
        logger.info(f"📝 POST Data length: {content_length}")
        if post_data and len(post_data) < 1000:  # Логируем только короткие данные
            logger.info(f"📝 POST Data: {post_data}")
        
        if self.path == '/api/v1/auth/login':
            logger.warning("🚨 LOGIN ATTEMPT ON DIAGNOSTIC SERVER")
            logger.warning("Main IRIS server is DOWN - authentication impossible")
            
            try:
                if post_data:
                    data = json.loads(post_data) if post_data.startswith('{') else {}
                    username = data.get('username', 'unknown')
                    logger.warning(f"👤 Login attempt for user: {username}")
            except:
                logger.warning("Could not parse login data")
            
            self.send_diagnostic_response(500, 
                {
                    "error": "main_server_unavailable",
                    "diagnostic_info": {
                        "issue": "IRIS API server not running",
                        "required_actions": [
                            "Install Python dependencies (pip install -r requirements.txt)",
                            "Setup database (PostgreSQL on port 5432 or 5433)",
                            "Apply database migrations (alembic upgrade head)",
                            "Start main server (uvicorn app.main:app --port 8003)"
                        ],
                        "current_issues": self.get_system_issues()
                    }
                }, 
                "Main server unavailable - check logs and dependencies")
        
        else:
            self.send_diagnostic_response(503, 
                {"error": "service_unavailable"}, 
                "Main IRIS server not running")
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Переопределение стандартного логирования"""
        logger.debug(f"HTTP: {format % args}")

def start_diagnostic_server():
    """Запуск диагностического сервера"""
    try:
        server = HTTPServer(('localhost', 8003), DiagnosticHandler)
        logger.info("🚀 DIAGNOSTIC SERVER STARTED")
        logger.info("=" * 80)
        logger.info("🔧 IRIS API DIAGNOSTIC MODE")
        logger.info("🌐 Server running on: http://localhost:8003")
        logger.info("📋 Available endpoints:")
        logger.info("  GET  /health - Server status")
        logger.info("  POST /api/v1/auth/login - Login diagnostic")
        logger.info("  GET  /api/v1/auth/status - Auth status")
        logger.info("📄 Logs saved to: /tmp/iris_diagnostic.log")
        logger.info("=" * 80)
        
        # Запуск мониторинга системы в отдельном потоке
        monitor_thread = threading.Thread(target=system_monitor, daemon=True)
        monitor_thread.start()
        
        logger.info("✅ System monitor started")
        logger.info("🔍 Waiting for requests...")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("🛑 Diagnostic server stopped by user")
    except Exception as e:
        logger.error(f"💥 Diagnostic server error: {e}")
        logger.error(traceback.format_exc())

def system_monitor():
    """Мониторинг системы в фоновом режиме"""
    while True:
        try:
            # Проверка каждые 30 секунд
            time.sleep(30)
            
            issues = []
            
            # Проверка основного сервера
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 8000))  # Стандартный FastAPI порт
                if result == 0:
                    logger.info("🔍 Main server detected on port 8000")
                sock.close()
            except:
                pass
            
            # Проверка базы данных
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 5432))
                if result == 0:
                    logger.info("🔍 PostgreSQL detected on port 5432")
                else:
                    result = sock.connect_ex(('localhost', 5433))
                    if result == 0:
                        logger.info("🔍 PostgreSQL detected on port 5433")
                sock.close()
            except:
                pass
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")

if __name__ == "__main__":
    print("🔧 Starting IRIS API Diagnostic Server...")
    print("This server will help diagnose authentication and connection issues")
    print("Access: http://localhost:8003")
    start_diagnostic_server()