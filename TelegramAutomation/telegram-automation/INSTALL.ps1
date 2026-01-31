# ============================================================
# Telegram Automation Pro - Автоматический установщик
# Version: 4.0.0
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Telegram Automation Pro - Автоматическая установка" -ForegroundColor Cyan
Write-Host "  Version: 4.0.0" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Требуются права администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора и повторите попытку." -ForegroundColor Yellow
    exit 1
}

# Функция для проверки команды
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

# Шаг 1: Проверка Python
Write-Host "[1/7] Проверка Python..." -ForegroundColor Yellow
if (Test-Command python) {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python установлен: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python не найден!" -ForegroundColor Red
    Write-Host "Установите Python 3.11+ с https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Не забудьте отметить 'Add Python to PATH' при установке!" -ForegroundColor Yellow
    exit 1
}

# Шаг 2: Проверка PostgreSQL
Write-Host "[2/7] Проверка PostgreSQL..." -ForegroundColor Yellow
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($pgService) {
    Write-Host "✅ PostgreSQL установлен" -ForegroundColor Green
    
    # Проверка запущен ли сервис
    if ($pgService.Status -ne "Running") {
        Write-Host "⚠️  PostgreSQL не запущен. Запускаем..." -ForegroundColor Yellow
        Start-Service $pgService.Name
        Write-Host "✅ PostgreSQL запущен" -ForegroundColor Green
    }
} else {
    Write-Host "❌ PostgreSQL не найден!" -ForegroundColor Red
    Write-Host "Установите PostgreSQL 15+ с https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "При установке запомните пароль для пользователя postgres!" -ForegroundColor Yellow
    exit 1
}

# Шаг 3: Создание виртуального окружения
Write-Host "[3/7] Создание виртуального окружения..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "⚠️  Виртуальное окружение уже существует, пересоздаём..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

python -m venv venv
Write-Host "✅ Виртуальное окружение создано" -ForegroundColor Green

# Активация venv
Write-Host "[4/7] Активация виртуального окружения..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✅ Виртуальное окружение активировано" -ForegroundColor Green

# Шаг 5: Установка зависимостей
Write-Host "[5/7] Установка зависимостей Python..." -ForegroundColor Yellow
Write-Host "Это может занять несколько минут..." -ForegroundColor Gray

# Создаём requirements.txt если его нет
if (-not (Test-Path "requirements.txt")) {
    @"
flask==3.0.0
flask-cors==4.0.0
asyncpg==0.29.0
bcrypt==4.1.2
PyJWT==2.8.0
python-dotenv==1.0.0
"@ | Set-Content "requirements.txt"
}

pip install --upgrade pip | Out-Null
pip install -r requirements.txt

Write-Host "✅ Зависимости установлены" -ForegroundColor Green

# Шаг 6: Настройка базы данных
Write-Host "[6/7] Настройка базы данных..." -ForegroundColor Yellow

# Запрос пароля PostgreSQL
$pgPassword = Read-Host "Введите пароль PostgreSQL (по умолчанию: postgres)" -AsSecureString
$pgPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pgPassword))
if ([string]::IsNullOrEmpty($pgPasswordPlain)) {
    $pgPasswordPlain = "postgres"
}

# Создание .env файла
@"
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=$pgPasswordPlain
DB_NAME=telegram_automation

# Flask Configuration
SECRET_KEY=telegram_automation_secret_key_$(Get-Random)
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
"@ | Set-Content ".env"

Write-Host "✅ Конфигурация создана" -ForegroundColor Green

# Инициализация базы данных
Write-Host "Инициализация базы данных..." -ForegroundColor Gray

$env:PGPASSWORD = $pgPasswordPlain

# Создание базы данных
$createDbCommand = "CREATE DATABASE telegram_automation;"
echo $createDbCommand | psql -U postgres -h localhost 2>$null

# Выполнение SQL скрипта
if (Test-Path "database\init.sql") {
    psql -U postgres -h localhost -d telegram_automation -f "database\init.sql" 2>$null | Out-Null
    Write-Host "✅ База данных инициализирована" -ForegroundColor Green
} else {
    Write-Host "⚠️  Файл database\init.sql не найден, создаём таблицы вручную..." -ForegroundColor Yellow
    
    # Создаём таблицу users напрямую
    $createUserTable = @"
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

INSERT INTO users (username, password_hash, role)
VALUES ('admin', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIq.Zu6W8u', 'admin')
ON CONFLICT (username) DO NOTHING;
"@
    
    echo $createUserTable | psql -U postgres -h localhost -d telegram_automation 2>$null | Out-Null
    Write-Host "✅ Таблица users создана" -ForegroundColor Green
}

# Шаг 7: Запуск сервера
Write-Host "[7/7] Запуск сервера..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ✅ Установка завершена успешно!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Данные для входа:" -ForegroundColor Cyan
Write-Host "   Имя пользователя: admin" -ForegroundColor White
Write-Host "   Пароль: admin123" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Адреса:" -ForegroundColor Cyan
Write-Host "   Веб-интерфейс: http://localhost:8000/" -ForegroundColor White
Write-Host "   API: http://localhost:8000/api/" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Запуск сервера..." -ForegroundColor Yellow
Write-Host "   Нажмите Ctrl+C для остановки" -ForegroundColor Gray
Write-Host ""

# Запуск Flask сервера
python backend\app.py
