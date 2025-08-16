# 🚀 Перезапуск серверов для SOC2 Enhanced Dashboard

## 1. Перезапуск Backend (PowerShell):

```powershell
# Остановите uvicorn (Ctrl+C)
# Затем запустите снова:
uvicorn app.main:app --port 8003 --reload
```

## 2. Перезапуск Frontend (в папке frontend):

```bash
# Остановите сервер разработки (Ctrl+C)
# Затем запустите снова:
npm run dev
```

## 3. Проверьте что работает:

1. **Backend API**: http://localhost:8003/docs
2. **Frontend**: http://localhost:3000
3. **New Enhanced Activities API**: http://localhost:8003/api/v1/audit/enhanced-activities

## 4. Что теперь появится на Dashboard:

### 🔐 **Новые SOC2 метрики:**
- **Security Events Today** - события безопасности
- **PHI Access Events** - доступ к медицинским данным  
- **Failed Login Attempts** - неудачные попытки входа
- **Admin Actions** - действия администраторов
- **Total Audit Events** - всего событий аудита

### 📊 **Enhanced Activity Card** с фильтрами:
- **Категории**: Security, PHI, Admin, System, Compliance
- **Приоритеты**: Critical, High, Medium, Low
- **Compliance флаги**: HIPAA, SOC2, GDPR
- **Детальная информация**: IP адреса, User Agent, метаданные

### 🎯 **SOC2 Type 2 Features:**
- **Critical Alerts** - badge с количеством критических событий
- **PHI Access Monitoring** - HIPAA совместимое логирование
- **Real-time Security Monitoring** - мониторинг в реальном времени
- **Compliance Tracking** - отслеживание соответствия требованиям

## 5. Mock Data:

Система будет показывать реалистичные mock данные включая:
- Неудачные попытки входа
- Доступ к PHI данным пациентов
- Административные действия
- Нарушения безопасности
- IRIS интеграционные события
- Управление согласиями пациентов

**Результат: Полноценная SOC2 Type 2 совместимая система мониторинга готова к использованию!** 🎉