#!/bin/bash

echo "=== BotHelper Installer ==="

# Проверка, что скрипт запущен с правами root
if [ "$EUID" -ne 0 ]; then
  echo "Пожалуйста, запустите этот скрипт с правами root или используя sudo."
  exit 1
fi

# Функция для определения пакетного менеджера
get_package_manager() {
  if command -v apt-get &>/dev/null; then
    echo "apt-get"
  elif command -v yum &>/dev/null; then
    echo "yum"
  elif command -v dnf &>/dev/null; then
    echo "dnf"
  elif command -v pacman &>/dev/null; then
    echo "pacman"
  elif command -v zypper &>/dev/null; then
    echo "zypper"
  elif command -v brew &>/dev/null; then
    echo "brew"
  else
    echo ""
  fi
}

PACKAGE_MANAGER=$(get_package_manager)

# Функция для установки системных пакетов
install_system_package() {
  PACKAGE_NAME=$1
  if [ -n "$PACKAGE_MANAGER" ]; then
    echo "Устанавливаем $PACKAGE_NAME..."
    case $PACKAGE_MANAGER in
      apt-get)
        apt-get install -y $PACKAGE_NAME
        ;;
      yum)
        yum install -y $PACKAGE_NAME
        ;;
      dnf)
        dnf install -y $PACKAGE_NAME
        ;;
      pacman)
        pacman -S --noconfirm $PACKAGE_NAME
        ;;
      zypper)
        zypper install -y $PACKAGE_NAME
        ;;
      brew)
        brew install $PACKAGE_NAME
        ;;
      *)
        echo "Неизвестный пакетный менеджер. Установите $PACKAGE_NAME вручную."
        exit 1
        ;;
    esac
    if [ $? -ne 0 ]; then
      echo "Ошибка установки $PACKAGE_NAME. Прекращение установки."
      exit 1
    fi
  else
    echo "Не удалось определить пакетный менеджер. Установите $PACKAGE_NAME вручную."
    exit 1
  fi
}

# Проверка и установка python3
if ! command -v python3 &>/dev/null; then
  echo "Python 3 не установлен. Устанавливаем..."
  install_system_package python3
fi

# Проверка и установка pip3
if ! command -v pip3 &>/dev/null; then
  echo "pip для Python 3 не установлен. Устанавливаем..."
  install_system_package python3-pip
fi

# Проверка и установка venv
if ! python3 -m venv --help &>/dev/null; then
  echo "Модуль venv для Python 3 не установлен. Устанавливаем..."
  install_system_package python3-venv
fi

# Создание и активация виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv
if [ $? -ne 0 ]; then
  echo "Ошибка при создании виртуального окружения. Прекращение установки."
  exit 1
fi
source venv/bin/activate

# Обновление pip внутри виртуального окружения
echo "Обновление pip..."
pip install --upgrade pip
if [ $? -ne 0 ]; then
  echo "Ошибка при обновлении pip. Прекращение установки."
  exit 1
fi

# Установка необходимых Python-библиотек
echo "Установка Python-библиотек..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
  echo "Ошибка при установке Python-библиотек. Прекращение установки."
  exit 1
fi

# Запрос конфигурационных данных
echo "Настройка конфигурации..."

read -p "Введите токен вашего Telegram бота: " TOKEN
read -p "Введите ваш Telegram ID (ADMIN_ID): " ADMIN_ID
read -p "Введите путь к базе данных (по умолчанию 'database.db'): " DB_PATH
DB_PATH=${DB_PATH:-database.db}

# Запись конфигурационных данных в config.ini
echo "Сохранение конфигурации в config.ini..."
cat > config.ini << EOL
[Telegram]
TOKEN = $TOKEN
ADMIN_ID = $ADMIN_ID

[Database]
DB_PATH = $DB_PATH
EOL

echo "Инициализация базы данных..."
python3 -c "from database_manager import init_db; init_db()"
if [ $? -ne 0 ]; then
  echo "Ошибка при инициализации базы данных. Прекращение установки."
  exit 1
fi

# Настройка системной службы
echo "Настройка системной службы..."

SERVICE_FILE="/etc/systemd/system/bothelper.service"

cat > $SERVICE_FILE << EOL
[Unit]
Description=BotHelper Telegram Bot Service
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$(pwd)
ExecStart=$(which bash) -c 'source $(pwd)/venv/bin/activate && exec python3 $(pwd)/bot_license_scheduler.py'
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

if [ $? -ne 0 ]; then
  echo "Ошибка при создании файла службы. Прекращение установки."
  exit 1
fi

systemctl daemon-reload
systemctl enable bothelper.service
systemctl start bothelper.service

if [ $? -ne 0 ]; then
  echo "Ошибка при настройке или запуске службы. Прекращение установки."
  exit 1
fi

echo "Установка завершена."
echo "Бот настроен как системная служба и запущен."

