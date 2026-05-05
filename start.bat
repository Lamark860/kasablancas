@echo off
REM Запуск Hortus Animae на Windows. Двойной клик из Проводника.
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0starter"

echo.
echo =======================================================
echo   Hortus Animae - локальный запуск
echo =======================================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker не установлен.
  echo Скачай Docker Desktop: https://www.docker.com/products/docker-desktop/
  echo Подробности — в файле START.txt
  echo.
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop не запущен.
  echo Открой приложение Docker, подожди пока значок кита успокоится,
  echo и запусти этот файл снова.
  echo.
  pause
  exit /b 1
)

if not exist .env copy .env.example .env >nul

echo Поднимаем сервисы...
echo ^(первый запуск — 5–10 минут, скачивается всё нужное; следующие — секунды^)
echo.

docker compose up -d --build
if errorlevel 1 (
  echo.
  echo Не удалось поднять контейнеры. Проверь, что Docker Desktop работает.
  echo.
  pause
  exit /b 1
)

echo.
echo Ждём, пока API оживёт...
set /a tries=0
:wait_loop
curl -fsS -o NUL http://localhost:8100/ >nul 2>nul
if not errorlevel 1 goto api_up
set /a tries+=1
if !tries! GEQ 90 goto api_up
timeout /t 2 /nobreak >nul
goto wait_loop
:api_up

echo Накатываем эзотерические данные ^(растения, оракулы^)...
docker compose exec -T api python -m vlad.seed >nul 2>nul

echo.
echo Готово. Открываю в браузере: http://localhost:3100/
echo.
echo Чтобы остановить — двойной клик по файлу stop.bat
echo Это окно можно закрыть.
echo.

start "" http://localhost:3100/

timeout /t 5 /nobreak >nul
