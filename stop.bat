@echo off
REM Остановка Hortus Animae на Windows. Двойной клик из Проводника.
chcp 65001 >nul

cd /d "%~dp0starter"

echo.
echo Останавливаю сервисы...
echo.

docker compose down
if errorlevel 1 (
  echo.
  echo Не получилось остановить ^(возможно, Docker Desktop уже не работает^).
  pause
  exit /b 1
)

echo.
echo Готово. Данные ^(гостьи, подборы^) сохранены —
echo при следующем старте всё на месте.
echo.
pause
