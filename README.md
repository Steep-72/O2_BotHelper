Конечно! Ниже приведён полный файл `README.md` для вашего проекта **BotHelper**. Вы можете скопировать этот текст и вставить его в ваш репозиторий на GitHub через веб-интерфейс.

---

# BotHelper

**BotHelper** — Telegram-бот для мониторинга лицензий и SSL-сертификатов. Он помогает отслеживать сроки действия лицензий на продукты компании и срок действия SSL-сертификатов сайтов, отправляя уведомления администраторам.

## 📋 Содержание

- [Описание](#-описание)
- [Возможности](#возможности)
- [Требования](#🛠-требования)
- [Установка](#📦-установка)
- [Настройка](#🔧-настройка)
- [Использование](#📝-использование)
- [Управление ботом](#🔧-управление-ботом)
- [Лицензия](#📜-лицензия)
- [Контакты](#📞-контакты)
- [Безопасность](#🔒-безопасность)

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
```

### 2. Создание виртуального окружения

Создайте и активируйте виртуальное окружение для проекта:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

Установите необходимые Python-библиотеки:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка конфигурации

1. **Создайте файл `config.ini` на основе примера:**

   ```bash
   cp config.ini.example config.ini
   ```

2. **Отредактируйте `config.ini`, заполнив необходимые поля:**

   ```bash
   nano config.ini
   ```

   **Пример содержимого `config.ini`:**

   ```ini
   [Telegram]
   TOKEN = ваш_токен_бота
   ADMIN_ID = ваш_telegram_id

   [Database]
   DB_PATH = database.db
   ```

### 5. Инициализация базы данных

Инициализируйте базу данных:

```bash
python3 -c "from database_manager import init_db; init_db()"
```

### 6. Запуск установочного скрипта

Запустите скрипт установки с правами `root` или используя `sudo`:

```bash
sudo ./install.sh
```

*Если вы уже находитесь под пользователем `root`, можно запустить без `sudo`:*

```bash
./install.sh
```

---

## 🔧 Настройка

После выполнения скрипта установки, бот будет настроен как системная служба и запущен автоматически. Убедитесь, что служба работает корректно:

```bash
systemctl status bothelper.service
```

---

## 📝 Использование

### Добавление сайта для мониторинга

1. Отправьте команду `добавить сайт` в чат с ботом.
2. Введите URL сайта, например: `https://example.com`.

### Просмотр списка сайтов

Отправьте команду `список сайтов` в чат с ботом, чтобы увидеть все добавленные для мониторинга сайты.

### Обновление информации о сертификатах

Отправьте команду `обновить информацию`, чтобы вручную запустить проверку SSL-сертификатов.

---

## 🔧 Управление ботом

Используйте следующие команды для управления ботом через `systemd`:

- **Проверка статуса службы:**

  ```bash
  systemctl status bothelper.service
  ```

- **Запуск службы:**

  ```bash
  sudo systemctl start bothelper.service
  ```

- **Остановка службы:**

  ```bash
  sudo systemctl stop bothelper.service
  ```

- **Перезапуск службы:**

  ```bash
  sudo systemctl restart bothelper.service
  ```

- **Просмотр логов службы:**

  ```bash
  journalctl -u bothelper.service -f
  ```

### Обновление зависимостей

Если вы изменили `requirements.txt`, обновите зависимости в виртуальном окружении:

1. **Активируйте виртуальное окружение:**

   ```bash
   source venv/bin/activate
   ```

2. **Установите обновленные зависимости:**

   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Деактивируйте виртуальное окружение:**

   ```bash
   deactivate
   ```

4. **Перезапустите бота:**

   ```bash
   sudo systemctl restart bothelper.service
   ```

---

## 📜 Лицензия

Этот проект лицензирован под [MIT License](LICENSE).

---

## 📞 Контакты

Если у вас возникли вопросы или предложения, свяжитесь со мной по [ваш_email@example.com](mailto:ваш_email@example.com).

---

## 🔒 Безопасность

- **Не загружайте** файл `config.ini` в публичный репозиторий.
- Убедитесь, что файл `config.ini` добавлен в `.gitignore`.
- Используйте пример конфигурационного файла `config.ini.example` для предоставления шаблона другим пользователям.
