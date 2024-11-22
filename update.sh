#!/bin/bash

# Путь к директории с ботом
BOT_DIR="$(dirname "$(readlink -f "$0")")"

# Переходим в директорию с ботом
cd "$BOT_DIR" || exit

echo "Обновляем код из репозитория GitHub..."
git pull origin main

echo "Активируем виртуальное окружение..."
source venv/bin/activate

echo "Обновляем зависимости..."
pip install --upgrade -r requirements.txt

echo "Деактивируем виртуальное окружение..."
deactivate

echo "Перезапускаем службу бота..."
sudo systemctl restart bothelper.service

echo "Обновление завершено!"
