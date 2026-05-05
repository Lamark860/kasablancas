#!/usr/bin/env bash
# Запуск Hortus Animæ на Mac. Двойной клик из Finder.
set -u

cd "$(dirname "$0")/starter"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Hortus Animæ — локальный запуск"
echo "═══════════════════════════════════════════════════════"
echo ""

# Проверка Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker не установлен."
  echo "Скачай Docker Desktop: https://www.docker.com/products/docker-desktop/"
  echo "Подробности — в файле START.txt"
  echo ""
  echo "Нажми Enter, чтобы закрыть это окно…"
  read -r _
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop не запущен."
  echo "Открой приложение Docker (значок кита в верхней панели Mac),"
  echo "подожди пока кит перестанет шевелиться, и запусти этот файл снова."
  echo ""
  echo "Нажми Enter, чтобы закрыть это окно…"
  read -r _
  exit 1
fi

# .env (на случай чистой распаковки)
if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Поднимаем сервисы…"
echo "(первый запуск — 5–10 минут, скачивается всё нужное; следующие — секунды)"
echo ""
if ! docker compose up -d --build; then
  echo ""
  echo "Не удалось поднять контейнеры. Проверь, что Docker Desktop"
  echo "работает (значок кита спокойный) и попробуй ещё раз."
  echo ""
  echo "Нажми Enter, чтобы закрыть это окно…"
  read -r _
  exit 1
fi

echo ""
echo "Ждём, пока API оживёт…"
for _ in $(seq 1 90); do
  if curl -fsS -o /dev/null http://localhost:8100/ 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "Накатываем эзотерические данные (растения, оракулы)…"
docker compose exec -T api python -m vlad.seed >/dev/null 2>&1 || true

echo ""
echo "Готово. Открываю в браузере: http://localhost:3100/"
echo ""
echo "Чтобы остановить — двойной клик по файлу stop.command"
echo "Это окно можно закрыть."
echo ""

open http://localhost:3100/ 2>/dev/null || true

# Не закрываем мгновенно, чтобы коллега успел прочитать
sleep 5
