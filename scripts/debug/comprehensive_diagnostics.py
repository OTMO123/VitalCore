#!/usr/bin/env python3
"""
Комплексная диагностика всей системы - найдем ВСЕ проблемы сразу.
"""

import urllib.request
import urllib.parse
import json
import time
import socket
import sys
from datetime import datetime

class HealthcareSystemDiagnostics:
    def __init__(self):
        self.results = []
        self.backend_host = "localhost"
        self.backend_port = 8003
        self.token = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {level}: {message}"
        print(formatted)
        self.results.append(formatted)
        
    def test_network_connectivity(self):
        """Проверяем сетевые соединения"""
        self.log("🌐 ПРОВЕРКА СЕТЕВЫХ СОЕДИНЕНИЙ", "SECTION")
        
        # Проверка порта
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.backend_host, self.backend_port))
            sock.close()
            
            if result == 0:
                self.log(f"✅ Порт {self.backend_port} доступен")
            else:
                self.log(f"❌ Порт {self.backend_port} недоступен (код: {result})", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Ошибка проверки порта: {e}", "ERROR")
            return False
            
        return True
    
    def test_basic_endpoints(self):
        """Проверяем базовые эндпоинты"""
        self.log("🏥 ПРОВЕРКА БАЗОВЫХ ЭНДПОИНТОВ", "SECTION")
        
        basic_endpoints = [
            ("Health Check", f"http://{self.backend_host}:{self.backend_port}/health"),
            ("API Docs", f"http://{self.backend_host}:{self.backend_port}/docs"),
            ("OpenAPI", f"http://{self.backend_host}:{self.backend_port}/openapi.json"),
        ]
        
        working_count = 0
        for name, url in basic_endpoints:
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'HealthcareDiagnostics/1.0')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    status = response.getcode()
                    if status == 200:
                        self.log(f"✅ {name}: {status}")
                        working_count += 1
                    else:
                        self.log(f"⚠️ {name}: {status}", "WARNING")
                        
            except urllib.error.HTTPError as e:
                self.log(f"❌ {name}: HTTP {e.code}", "ERROR")
            except Exception as e:
                self.log(f"❌ {name}: {str(e)[:50]}", "ERROR")
                
        self.log(f"Базовые эндпоинты: {working_count}/{len(basic_endpoints)} работают")
        return working_count > 0
    
    def test_authentication(self):
        """Проверяем аутентификацию"""
        self.log("🔐 ПРОВЕРКА АУТЕНТИФИКАЦИИ", "SECTION")
        
        login_url = f"http://{self.backend_host}:{self.backend_port}/api/v1/auth/login"
        login_data = urllib.parse.urlencode({
            "username": "admin",
            "password": "admin123"
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                login_url,
                data=login_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'HealthcareDiagnostics/1.0'
                },
                method='POST'
            )
            
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=15) as response:
                elapsed = time.time() - start_time
                
                if response.getcode() == 200:
                    response_data = json.loads(response.read().decode('utf-8'))
                    self.token = response_data.get("access_token")
                    
                    self.log(f"✅ Аутентификация успешна ({elapsed:.1f}s)")
                    self.log(f"✅ Токен получен: {self.token[:20] if self.token else 'None'}...")
                    
                    # Проверяем структуру ответа
                    expected_fields = ["access_token", "refresh_token", "token_type", "expires_in", "user"]
                    for field in expected_fields:
                        if field in response_data:
                            self.log(f"✅ Поле '{field}' присутствует")
                        else:
                            self.log(f"⚠️ Поле '{field}' отсутствует", "WARNING")
                    
                    return True
                else:
                    self.log(f"❌ Аутентификация неудачна: {response.getcode()}", "ERROR")
                    
        except urllib.error.HTTPError as e:
            error_data = e.read().decode('utf-8')
            self.log(f"❌ HTTP ошибка при входе: {e.code}", "ERROR")
            self.log(f"Детали: {error_data[:200]}", "ERROR")
        except Exception as e:
            self.log(f"❌ Ошибка аутентификации: {e}", "ERROR")
            
        return False
    
    def test_all_dashboard_endpoints(self):
        """Проверяем ВСЕ эндпоинты дашборда"""
        self.log("📊 ПРОВЕРКА ВСЕХ ЭНДПОИНТОВ ДАШБОРДА", "SECTION")
        
        if not self.token:
            self.log("❌ Нет токена для проверки защищенных эндпоинтов", "ERROR")
            return
            
        dashboard_endpoints = [
            # Основные эндпоинты дашборда
            ("Recent Activities", "/api/v1/audit/recent-activities?limit=5"),
            ("Audit Stats", "/api/v1/audit/stats"),
            ("Health Summary", "/api/v1/iris/health/summary"),
            ("IRIS Status", "/api/v1/iris/status"),
            ("IRIS Health", "/api/v1/iris/health"),
            ("Patients List", "/api/v1/healthcare/patients?limit=3"),
            
            # Управление пользователями
            ("Current User", "/api/v1/auth/me"),
            ("Users List", "/api/v1/auth/users?limit=5"),
            
            # Дополнительные эндпоинты
            ("Healthcare Records", "/api/v1/healthcare/documents?limit=1"),
            ("Patient Details", "/api/v1/healthcare/patients"),
        ]
        
        auth_headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'User-Agent': 'HealthcareDiagnostics/1.0'
        }
        
        working_endpoints = 0
        total_endpoints = len(dashboard_endpoints)
        
        for name, path in dashboard_endpoints:
            url = f"http://{self.backend_host}:{self.backend_port}{path}"
            
            try:
                req = urllib.request.Request(url, headers=auth_headers)
                start_time = time.time()
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    elapsed = time.time() - start_time
                    status = response.getcode()
                    response_data = response.read().decode('utf-8')
                    
                    if status == 200:
                        # Проверяем, что это валидный JSON
                        try:
                            json_data = json.loads(response_data)
                            data_size = len(response_data)
                            self.log(f"✅ {name}: {status} ({elapsed:.1f}s, {data_size}b)")
                            
                            # Показываем структуру данных для ключевых эндпоинтов
                            if "activities" in json_data:
                                activities_count = len(json_data.get("activities", []))
                                self.log(f"   📋 Найдено активностей: {activities_count}")
                            elif "total" in json_data:
                                total_items = json_data.get("total", 0)
                                self.log(f"   📊 Общее количество: {total_items}")
                                
                            working_endpoints += 1
                            
                        except json.JSONDecodeError:
                            self.log(f"⚠️ {name}: {status} (не JSON ответ)", "WARNING")
                            
                    else:
                        self.log(f"⚠️ {name}: {status}", "WARNING")
                        
            except urllib.error.HTTPError as e:
                error_data = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
                self.log(f"❌ {name}: HTTP {e.code}", "ERROR")
                if e.code == 500:
                    self.log(f"   500 детали: {error_data[:100]}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ {name}: {str(e)[:50]}", "ERROR")
        
        self.log(f"Эндпоинты дашборда: {working_endpoints}/{total_endpoints} работают")
        
        # Оценка готовности системы
        success_rate = working_endpoints / total_endpoints
        if success_rate >= 0.9:
            self.log("🎉 СИСТЕМА ГОТОВА К РАБОТЕ!", "SUCCESS")
        elif success_rate >= 0.7:
            self.log("⚠️ Система частично готова, есть минорные проблемы", "WARNING")
        else:
            self.log("❌ Система требует дополнительной настройки", "ERROR")
            
        return working_endpoints, total_endpoints
    
    def test_frontend_expectations(self):
        """Проверяем то, что ожидает фронтенд"""
        self.log("🖥️ ПРОВЕРКА ОЖИДАНИЙ ФРОНТЕНДА", "SECTION")
        
        # Проверяем CORS
        try:
            req = urllib.request.Request(f"http://{self.backend_host}:{self.backend_port}/health")
            req.add_header('Origin', 'http://localhost:3000')
            req.add_header('Access-Control-Request-Method', 'GET')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                headers = dict(response.headers)
                
                if 'Access-Control-Allow-Origin' in headers:
                    self.log("✅ CORS настроен")
                else:
                    self.log("⚠️ CORS может быть не настроен", "WARNING")
                    
        except Exception as e:
            self.log(f"⚠️ Не удалось проверить CORS: {e}", "WARNING")
    
    def generate_summary(self):
        """Генерируем итоговый отчет"""
        self.log("", "")
        self.log("=" * 60, "SECTION")
        self.log("📋 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ", "SECTION")
        self.log("=" * 60, "SECTION")
        
        error_count = len([r for r in self.results if "ERROR" in r])
        warning_count = len([r for r in self.results if "WARNING" in r])
        
        self.log(f"🔴 Критических ошибок: {error_count}")
        self.log(f"🟡 Предупреждений: {warning_count}")
        
        if error_count == 0:
            self.log("🎉 ВСЕ ОСНОВНЫЕ КОМПОНЕНТЫ РАБОТАЮТ!")
            self.log("💡 Рекомендации:")
            self.log("   1. Запустите фронтенд: cd frontend && npm run dev")
            self.log("   2. Откройте: http://localhost:3000")
            self.log("   3. Войдите: admin / admin123")
        elif error_count <= 3:
            self.log("⚠️ Есть минорные проблемы, но система может работать")
        else:
            self.log("❌ Много проблем - требуется дополнительная настройка")
            
        self.log("", "")
        self.log("📝 ПОЛНЫЙ ЛОГ СОХРАНЕН ДЛЯ АНАЛИЗА", "SECTION")
    
    def run_full_diagnostics(self):
        """Запуск полной диагностики"""
        print("🚀 КОМПЛЕКСНАЯ ДИАГНОСТИКА HEALTHCARE ПЛАТФОРМЫ")
        print("=" * 60)
        
        start_time = time.time()
        
        # Последовательная проверка всех компонентов
        if not self.test_network_connectivity():
            self.log("💥 КРИТИЧЕСКАЯ ОШИБКА: Нет соединения с бэкендом", "ERROR")
            self.generate_summary()
            return
            
        if not self.test_basic_endpoints():
            self.log("💥 КРИТИЧЕСКАЯ ОШИБКА: Базовые эндпоинты не работают", "ERROR")
            self.generate_summary()
            return
            
        if not self.test_authentication():
            self.log("💥 КРИТИЧЕСКАЯ ОШИБКА: Аутентификация не работает", "ERROR")
            self.generate_summary()
            return
            
        self.test_all_dashboard_endpoints()
        self.test_frontend_expectations()
        
        elapsed = time.time() - start_time
        self.log(f"⏱️ Диагностика завершена за {elapsed:.1f} секунд")
        
        self.generate_summary()
        
        # Сохраняем полный лог
        with open('healthcare_diagnostics.log', 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.results))
        
        return self.results

if __name__ == "__main__":
    diagnostics = HealthcareSystemDiagnostics()
    diagnostics.run_full_diagnostics()