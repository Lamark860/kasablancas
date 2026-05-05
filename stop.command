#!/usr/bin/env bash
# Остановка Hortus Animæ на Mac. Двойной клик из Finder.
set -u

cd "$(dirname "$0")/starter"

echo ""
echo "Останавливаю сервисы…"
echo ""

if ! docker compose down; then
  echo ""
  echo "Не получилось остановить (возможно, Docker Desktop уже не работает)."
  echo "Нажми Enter, чтобы закрыть это окно…"
  read -r _
  exit 1
fi

echo ""
echo "Готово. Данные (гостьи, подборы) сохранены —"
echo "при следующем старте всё на месте."
echo ""
echo "Нажми Enter, чтобы закрыть это окно…"
read -r _
