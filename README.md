# BotHelper

**BotHelper** — Telegram-бот для мониторинга лицензий и SSL-сертификатов. Он помогает отслеживать сроки действия лицензий на продукты компании и срок действия SSL-сертификатов сайтов, отправляя уведомления администраторам.

## 📋 Содержание

- [Описание](#-описание)
- [Возможности](#возможности)
- [Требования](#требования)
- [Установка](#установка)
- [Настройка](#настройка)
- [Использование](#использование)
- [Управление ботом](#управление-ботом)
- [Лицензия](#лицензия)
- [Контакты](#контакты)

## 📖 Описание

BotHelper — это инструмент для автоматизации мониторинга сроков действия лицензий и SSL-сертификатов. Бот уведомляет администратора о приближении даты истечения сроков, позволяя своевременно обновлять необходимые ресурсы.

## 🚀 Возможности

- **Мониторинг лицензий**: Отслеживание сроков действия лицензий на продукты компании.
- **Мониторинг SSL-сертификатов**: Проверка сроков действия SSL-сертификатов сайтов.
- **Уведомления**: Отправка уведомлений администраторам о приближении сроков истечения.
- **Управление сайтами**: Добавление, удаление и просмотр сайтов для мониторинга.
- **Безопасность**: Ограничение доступа к боту только для разрешенных пользователей.

## 🛠 Требования

- **Python 3.7+**
- **SQLite3**
- **Git**
- **Telegram-бот** с полученным токеном от [@BotFather](https://t.me/BotFather)

## 📦 Установка

### 1. Клонирование репозитория

Скачайте проект на ваш сервер или локальную машину:

```bash
git clone https://github.com/ваш_логин/BotHelper.git
cd BotHelper
2. Создание виртуального окружения
Создайте и активируйте виртуальное окружение для проекта:

bash
Копировать код
python3 -m venv venv
source venv/bin/activate
3. Установка зависимостей
Установите необходимые Python-библиотеки:

bash
Копировать код
pip install --upgrade pip
pip install -r requirements.txt
4. Настройка конфигурации
Создайте файл config.ini на основе примера и заполните необходимые поля:

bash
Копировать код
cp config.ini.example config.ini
nano config.ini
Пример содержимого config.ini:

ini
Копировать код
[Telegram]
TOKEN = ваш_токен_бота
ADMIN_ID = ваш_telegram_id

[Database]
DB_PATH = database.db
5. Инициализация базы данных
Инициализируйте базу данных:

bash
Копировать код
python3 -c "from database_manager import init_db; init_db()"
6. Запуск установочного скрипта
Запустите скрипт установки с правами root или используя sudo:

bash
Копировать код
sudo ./install.sh
Если вы уже находитесь под пользователем root, можно запустить без sudo:

bash
Копировать код
./install.sh
⚙️ Настройка
После выполнения скрипта установки, бот будет настроен как системная служба и запущен автоматически. Убедитесь, что служба работает корректно:

bash
Копировать код
systemctl status bothelper.service
📝 Использование
Добавление сайта для мониторинга
Отправьте команду добавить сайт в чат с ботом.
Введите URL сайта, например: https://example.com.
Просмотр списка сайтов
Отправьте команду список сайтов в чат с ботом, чтобы увидеть все добавленные для мониторинга сайты.

Обновление информации о сертификатах
Отправьте команду обновить информацию, чтобы вручную запустить проверку SSL-сертификатов.

🔧 Управление ботом
Используйте следующие команды для управления ботом:

Проверка статуса службы:

bash
Копировать код
systemctl status bothelper.service
Запуск службы:

bash
Копировать код
sudo systemctl start bothelper.service
Остановка службы:

bash
Копировать код
sudo systemctl stop bothelper.service
Перезапуск службы:

bash
Копировать код
sudo systemctl restart bothelper.service
Просмотр логов службы:

bash
Копировать код
journalctl -u bothelper.service -f
📜 Лицензия
Этот проект лицензирован под MIT License.

📞 Контакты
Если у вас возникли вопросы или предложения, свяжитесь со мной по ваш_email@example.com.
