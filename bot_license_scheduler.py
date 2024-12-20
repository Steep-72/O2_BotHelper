# -*- coding: utf-8 -*-
# bot_license_scheduler.py

import logging
import asyncio
import os
import subprocess
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from bot_config import TOKEN, ADMIN_ID, DB_PATH
from database_manager import (
    save_notification_to_db,
    delete_notification_from_db,
    get_notifications_from_db,
    add_monitored_site,
    add_monitored_sites,
    get_monitored_sites,
    remove_monitored_site,
    init_db,
    add_allowed_user,
    is_user_allowed,
    add_access_request,
    remove_access_request,
    is_access_request_pending,
    get_access_request_info,
    update_certificate_info,
    get_certificate_info,
    add_allowed_chat,
    is_chat_allowed,
)
from datetime import datetime, timedelta, time
import pytz
import re
import sys
from ssl_certificate_checker import check_certificates
from urllib.parse import urlparse
from git import Repo, GitCommandError

# Настройки логирования
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Настройки бота
TIMEZONE = pytz.timezone("Asia/Yekaterinburg")

# Инициализация базы данных при запуске
init_db()


def adjust_for_weekend(date):
    # Если дата приходится на субботу или воскресенье, переносим на предыдущий рабочий день (пятницу)
    weekday = date.weekday()
    if weekday == 5:  # Суббота
        return date - timedelta(days=1)
    elif weekday == 6:  # Воскресенье
        return date - timedelta(days=2)
    else:
        return date


async def send_license_notification(
    context, user_id, company, product, expiry_date, quantity
):
    message = (
        f"Напоминание! Лицензия для компании '{company}' на продукт '{product}' истекает {expiry_date.strftime('%d.%m.%Y')}."
    )
    if quantity:
        message += f" Количество: {quantity}."
    await context.bot.send_message(chat_id=user_id, text=message)


def get_current_version():
    try:
        repo_path = os.path.abspath('.')
        repo = Repo(repo_path)
        current_commit = repo.head.commit
        commit_hash = current_commit.hexsha[:7]
        commit_date = datetime.fromtimestamp(current_commit.committed_date).strftime('%d.%m.%Y %H:%M')
        commit_message = current_commit.message.strip()
        version_info = f"{commit_hash} от {commit_date}\n\"{commit_message}\""
        return version_info
    except Exception as e:
        logger.error(f"Ошибка при получении версии бота: {e}")
        return "неизвестно"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    user_id = update.effective_user.id

    if is_user_allowed(user_id) or user_id == ADMIN_ID:
        version = get_current_version()
        keyboard = [
            [KeyboardButton("Запланировать уведомление")],
            [KeyboardButton("Список запланированных уведомлений")],
            [KeyboardButton("Список сайтов"), KeyboardButton("Обновить информацию о сайтах")],
            [KeyboardButton("Добавить сайт")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=False
        )
        await update.message.reply_text(
            f"Привет! Я помогу вам следить за сроками лицензий и SSL-сертификатов.\n\n"
            f"Версия бота: {version}\n\n"
            "Основные функции:\n"
            "- Запланировать уведомления о сроке действия лицензии.\n"
            "- Автоматическое напоминание за неделю до истечения срока.\n"
            "- Учет выходных: уведомления переносятся на ближайший рабочий день.\n"
            "- Напоминание в день окончания срока.\n"
            "- Мгновенное напоминание, если срок уже истек.\n"
            "- Просмотр и управление списком сайтов для мониторинга SSL-сертификатов.",
            reply_markup=reply_markup,
        )
    else:
        await request_access(update, context)


async def request_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Проверяем, не был ли запрос уже отправлен
    if is_access_request_pending(user_id):
        await update.message.reply_text(
            "Ваш запрос на доступ уже отправлен и ожидает рассмотрения."
        )
        return

    # Проверяем, не является ли пользователь уже одобренным
    if is_user_allowed(user_id):
        await update.message.reply_text(
            "У вас уже есть доступ. Введите /start для начала работы."
        )
        return

    # Добавляем запрос в базу данных
    add_access_request(user_id, user.username, user.first_name, user.last_name)
    logger.info(f"Пользователь {user.first_name} {user.last_name} ({user.id}) запросил доступ.")

    await update.message.reply_text(
        "У вас нет доступа к этому боту. Запрос отправлен администратору."
    )

    # Уведомить администратора с кнопками одобрения
    keyboard = [
        [
            InlineKeyboardButton("Одобрить", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("Отклонить", callback_data=f"reject_{user.id}"),
        ]
    ]
    message_text = (
        f"Пользователь {user.first_name} {user.last_name} (@{user.username}, ID: {user.id}) "
        "запросил доступ."
    )
    await context.bot.send_message(
        chat_id=ADMIN_ID, text=message_text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action, user_id = query.data.split('_')
    user_id = int(user_id)
    if action == 'approve':
        # Получаем информацию о пользователе из базы данных
        result = get_access_request_info(user_id)
        if result:
            username, first_name, last_name = result
            add_allowed_user(user_id, username, first_name, last_name)
            remove_access_request(user_id)
            await context.bot.send_message(
                chat_id=user_id,
                text="Ваш запрос на доступ одобрен. Введите /start для начала работы.",
            )
            await query.answer("Пользователь одобрен.")
        else:
            await query.answer("Запрос пользователя не найден.")
    elif action == 'reject':
        remove_access_request(user_id)
        await context.bot.send_message(
            chat_id=user_id, text="Ваш запрос на доступ отклонен."
        )
        await query.answer("Пользователь отклонен.")
    else:
        await query.answer("Неизвестное действие.")
    await query.message.delete()


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    context.user_data.clear()  # Очищаем данные, чтобы избежать конфликтов
    await update.message.reply_text(
        "Введите данные о лицензии в формате:\n"
        "Название компании\n"
        "Продукт\n"
        "Дата истечения срока (ДД.ММ.ГГГГ)\n"
        "Количество (опционально)"
    )
    context.user_data['awaiting_license_data'] = True


async def process_license_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    text = update.message.text.strip()
    # Проверяем, не является ли введенный текст командой
    if text.lower() in [
        "запланировать уведомление",
        "список запланированных уведомлений",
        "список сайтов",
        "обновить информацию о сайтах",
        "добавить сайт",
    ]:
        context.user_data.clear()
        await handle_message(update, context)
        return

    lines = text.split('\n')
    if len(lines) < 3:
        await update.message.reply_text(
            "Недостаточно данных. Пожалуйста, введите данные в указанном формате."
        )
        return

    company = lines[0].strip()
    product = lines[1].strip()
    expiry_date_str = lines[2].strip()
    quantity = lines[3].strip() if len(lines) > 3 else ""

    # Проверяем формат даты
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%d.%m.%Y').date()
    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты. Пожалуйста, используйте формат ДД.ММ.ГГГГ."
        )
        return

    # Проверяем, что дата истечения не в прошлом
    current_date = datetime.now(TIMEZONE).date()
    if expiry_date < current_date:
        await update.message.reply_text(
            "Дата истечения уже прошла. Пожалуйста, введите корректную дату."
        )
        return

    # Проверяем, не существует ли уже уведомление для этой компании и продукта
    notifications = get_notifications_from_db()
    for notif in notifications:
        if notif[2] == company and notif[3] == product:
            await update.message.reply_text(
                f"Уведомление для компании '{company}' и продукта '{product}' уже существует. "
                "Проверьте список уведомлений или измените данные.\n"
                "Введите данные о лицензии в указанном формате:"
            )
            return

    # Планируем уведомления
    notify_dates = []

    # Уведомление за 7 дней
    notify_date_7_days = expiry_date - timedelta(days=7)
    notify_date_7_days = adjust_for_weekend(notify_date_7_days)

    # Проверяем, что уведомление за 7 дней еще не прошло
    if notify_date_7_days > current_date:
        notify_dates.append(notify_date_7_days)
    elif notify_date_7_days == current_date:
        # Проверяем время (уведомление в 09:00)
        current_time = datetime.now(TIMEZONE).time()
        if current_time < time(9, 0):
            notify_dates.append(notify_date_7_days)

    # Уведомление в день истечения
    if expiry_date > current_date:
        notify_dates.append(expiry_date)
    elif expiry_date == current_date:
        current_time = datetime.now(TIMEZONE).time()
        if current_time < time(9, 0):
            notify_dates.append(expiry_date)

    if not notify_dates:
        await update.message.reply_text(
            "Указанные даты уведомлений уже прошли. Пожалуйста, введите корректную дату истечения."
        )
        return

    # Сохраняем уведомление в базе данных
    success = save_notification_to_db(
        update.effective_user.id,  # user_id
        company,
        product,
        expiry_date.strftime('%Y-%m-%d'),
        '',  # notify_date будет рассчитана при проверке уведомлений
        quantity,
        'лицензия',  # Тип уведомления всегда 'лицензия' для этой функции
    )

    if success:
        messages = []
        for date in notify_dates:
            messages.append(f"- {date.strftime('%d.%m.%Y')} в 09:00")
        await update.message.reply_text(
            "Уведомления запланированы на следующие даты:\n" + "\n".join(messages)
        )
    else:
        await update.message.reply_text("Не удалось сохранить уведомление. Попробуйте снова.")
    context.user_data.pop('awaiting_license_data', None)


async def list_scheduled(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    notifications = get_notifications_from_db()
    if not notifications:
        await update.message.reply_text("Нет запланированных уведомлений.")
        return
    message = "Список запланированных уведомлений:\n"
    for notif in notifications:
        expiry_date = datetime.strptime(notif[4], '%Y-%m-%d').strftime('%d.%m.%Y')
        quantity_info = f"Количество: {notif[6]}" if notif[6] else ""
        message += (
            f"{notif[0]}. Клиент: {notif[2]}\n"
            f"Лицензия на: {notif[3]}\n"
            f"{quantity_info}\n"
            f"Истекает: {expiry_date}\n"
            f"Команда для удаления: /delete_{notif[0]}\n\n"
        )
    await update.message.reply_text(message)


async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    message_text = update.message.text.strip()
    match = re.match(r'^/delete_(\d+)$', message_text)
    if match:
        notif_id = match.group(1)
        delete_notification_from_db(notif_id)
        await update.message.reply_text(f"Уведомление с ID {notif_id} удалено.")
    else:
        await update.message.reply_text(
            "Неверная команда удаления уведомления. Используйте /delete_ID, где ID - номер уведомления."
        )


async def list_sites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    sites = get_monitored_sites()
    if not sites:
        await update.message.reply_text("Список сайтов для мониторинга пуст.")
        return

    message = "Список сайтов, за которыми ведется наблюдение:\n\n"
    buttons = []

    for site in sites:
        cert_info = get_certificate_info(site)
        if cert_info and cert_info['expiry_date']:
            expiry_date = datetime.strptime(
                cert_info['expiry_date'], '%Y-%m-%d %H:%M:%S'
            )
            days_to_expiry = (expiry_date.date() - datetime.now(TIMEZONE).date()).days
            message += (
                f"Сайт: {site}\n"
                f"CN: {cert_info['common_name']}\n"
                f"Сертификат истекает: {expiry_date.strftime('%d.%m.%Y %H:%M:%S')} "
                f"(через {days_to_expiry} дней)\n\n"
            )
        else:
            message += f"Сайт: {site}\nИнформация о сертификате отсутствует. Нажмите 'Обновить информацию о сайтах'.\n\n"
        # Добавляем кнопку удаления для каждого сайта
        buttons.append(
            [InlineKeyboardButton(f"Удалить {site}", callback_data=f"delete_site|{site}")]
        )

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(message, reply_markup=reply_markup)


async def handle_delete_site_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data.startswith('delete_site|'):
        site = data.split('|', 1)[1]
        sites = get_monitored_sites()
        if site.lower() in [s.lower() for s in sites]:
            remove_monitored_site(site)
            await query.answer(f"Сайт {site} удален из списка мониторинга.")
            await query.edit_message_text(f"Сайт {site} был удален из списка мониторинга.")
        else:
            await query.answer("Сайт не найден в списке мониторинга.")
    else:
        await query.answer("Неверная команда.")


async def update_sites_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    await update.message.reply_text(
        "Обновление информации о сертификатах. Пожалуйста, подождите..."
    )
    await check_certificates(context)
    await update.message.reply_text("Информация о сертификатах обновлена.")
    # После обновления выводим список сайтов
    await list_sites(update, context)


async def add_site_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    context.user_data.clear()  # Очищаем данные, чтобы избежать конфликтов
    await update.message.reply_text(
        "Введите адрес сайта или список сайтов, которые вы хотите добавить для мониторинга SSL-сертификата. Каждый сайт с новой строки:"
    )
    context.user_data['adding_site'] = True


async def process_add_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    sites_input = update.message.text.strip()
    # Проверяем, не является ли введенный текст командой
    if sites_input.lower() in [
        "запланировать уведомление",
        "список запланированных уведомлений",
        "список сайтов",
        "обновить информацию о сайтах",
        "добавить сайт",
    ]:
        context.user_data.clear()
        await handle_message(update, context)
        return

    sites = sites_input.split('\n')
    normalized_sites = []
    for site in sites:
        site = site.strip()
        if not site:
            continue
        # Нормализуем сайт
        if not re.match(r'^https?://', site):
            site = 'https://' + site
        parsed_url = urlparse(site)
        hostname = parsed_url.hostname or parsed_url.path
        normalized_site = hostname.lower()
        normalized_sites.append(normalized_site)

    # Добавляем сайты
    added_sites, failed_sites = add_monitored_sites(normalized_sites)
    message = ""
    if added_sites:
        message += "Следующие сайты были успешно добавлены для мониторинга:\n"
        for site in added_sites:
            message += f"- {site}\n"
    if failed_sites:
        message += "Следующие сайты не были добавлены (возможно, уже существуют):\n"
        for site in failed_sites:
            message += f"- {site}\n"

    await update.message.reply_text(message)
    context.user_data.pop('adding_site', None)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    chat = update.effective_chat

    if chat.type != 'private':
        await update.message.reply_text("Пожалуйста, используйте личный чат для взаимодействия со мной.")
        return

    if not is_user_allowed(user_id) and user_id != ADMIN_ID:
        await request_access(update, context)
        return

    # Если пользователь вводит новую команду, прерываем текущую операцию
    if text.lower() in [
        "запланировать уведомление",
        "список запланированных уведомлений",
        "список сайтов",
        "обновить информацию о сайтах",
        "добавить сайт",
    ]:
        context.user_data.clear()

    if context.user_data.get('awaiting_license_data'):
        await process_license_data(update, context)
    elif context.user_data.get('adding_site'):
        await process_add_site(update, context)
    elif text.lower() == "запланировать уведомление":
        await schedule(update, context)
    elif text.lower() == "список запланированных уведомлений":
        await list_scheduled(update, context)
    elif text.lower() == "список сайтов":
        await list_sites(update, context)
    elif text.lower() == "обновить информацию о сайтах":
        await update_sites_info(update, context)
    elif text.lower() == "добавить сайт":
        await add_site_start(update, context)
    elif re.match(r'^/delete_\d+$', text):
        await delete_notification(update, context)
    else:
        await update.message.reply_text("Извините, я не понимаю эту команду.")


async def approve_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return
    add_allowed_chat(chat.id)
    await update.message.reply_text("Этот чат успешно одобрен для получения уведомлений.")


async def update_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    await update.message.reply_text("Проверка наличия обновлений...")
    await check_for_updates_manual(context)


async def check_for_updates_manual(context: ContextTypes.DEFAULT_TYPE):
    repo_path = os.path.abspath('.')
    repo = Repo(repo_path)

    # Получаем текущий коммит
    current_commit = repo.head.commit

    try:
        # Получаем обновления из удаленного репозитория
        origin = repo.remotes.origin
        origin.fetch()
        remote_commit = repo.commit('origin/main')

        if current_commit.hexsha != remote_commit.hexsha:
            # Есть обновления
            diff = current_commit.diff(remote_commit)
            changes = '\n'.join([f"- {item.a_path}" for item in diff])
            message = (
                f"Доступно обновление бота.\n"
                f"Измененные файлы:\n{changes}\n\n"
                f"Новая версия: {remote_commit.hexsha[:7]}"
            )
            keyboard = [[InlineKeyboardButton("Обновить бота", callback_data='update_bot')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=ADMIN_ID, text=message, reply_markup=reply_markup)
        else:
            # Нет обновлений
            await context.bot.send_message(chat_id=ADMIN_ID, text="Установлена последняя версия бота. Обновления отсутствуют.")
    except GitCommandError as e:
        logger.error(f"Ошибка при проверке обновлений: {e}")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Ошибка при проверке обновлений: {e}")


async def update_bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    if user.id != ADMIN_ID:
        await query.answer("У вас нет прав для выполнения этой операции.", show_alert=True)
        return

    await query.answer()
    await query.edit_message_text(text="Обновление бота...")

    try:
        # Останавливаем службу бота
        subprocess.run(['sudo', 'systemctl', 'stop', 'bothelper.service'], check=True)

        # Обновляем код из репозитория
        repo_path = os.path.abspath('.')
        repo = Repo(repo_path)
        origin = repo.remotes.origin
        origin.pull()

        # Обновляем зависимости
        subprocess.run(['bash', '-c', 'source venv/bin/activate && pip install --upgrade -r requirements.txt'], check=True)

        # Перезапускаем службу бота
        subprocess.run(['sudo', 'systemctl', 'start', 'bothelper.service'], check=True)

        await context.bot.send_message(chat_id=ADMIN_ID, text="Бот успешно обновлен и перезапущен.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении бота: {e}")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Ошибка при обновлении бота: {e}")


def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve_chat", approve_chat))
    application.add_handler(CommandHandler("update_bot", update_bot_command))
    application.add_handler(CallbackQueryHandler(handle_approval, pattern='^(approve|reject)_'))
    application.add_handler(CallbackQueryHandler(update_bot_callback, pattern='^update_bot$'))
    application.add_handler(CallbackQueryHandler(handle_delete_site_callback, pattern='^delete_site\|'))
    application.add_handler(MessageHandler(filters.Regex(r'^/delete_\d+$'), delete_notification))
    application.add_handler(MessageHandler(filters.ALL, handle_message))


def schedule_license_checks(application):
    # Запланировать регулярную проверку лицензий
    application.job_queue.run_repeating(
        check_licenses,
        interval=60 * 60,  # Проверка каждый час
        first=10,  # Первое выполнение через 10 секунд после запуска бота
    )


async def check_licenses(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Проверка запланированных уведомлений по лицензиям")
    notifications = get_notifications_from_db()
    current_date = datetime.now(TIMEZONE).date()
    current_time = datetime.now(TIMEZONE).time()

    for notif in notifications:
        (
            notif_id,
            user_id,
            company,
            product,
            expiry_date_str,
            notify_date_str,
            quantity,
            notification_type,
        ) = notif
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        # Вычисляем дату уведомления за 7 дней
        notify_date = adjust_for_weekend(expiry_date - timedelta(days=7))

        send_notification = False

        if current_date == notify_date:
            if time(9, 0) <= current_time < time(10, 0):
                send_notification = True
        elif current_date == expiry_date:
            if time(9, 0) <= current_time < time(10, 0):
                send_notification = True
        elif current_date > expiry_date:
            send_notification = True
            message = (
                f"Срок действия лицензии для компании '{company}' на продукт '{product}' "
                f"истек {expiry_date.strftime('%d.%m.%Y')}."
            )
            if quantity:
                message += f" Количество: {quantity}."
            await context.bot.send_message(chat_id=user_id, text=message)
            logger.info(f"Отправлено уведомление об истечении для {company} - {product}")
            continue  # Переходим к следующему уведомлению

        if send_notification:
            await send_license_notification(
                context, user_id, company, product, expiry_date, quantity
            )
            logger.info(f"Отправлено уведомление для {company} - {product}")


def schedule_update_checks(application):
    # Запланировать проверку обновлений раз в неделю в 3:00 утра по понедельникам
    target_time = time(3, 0, tzinfo=TIMEZONE)
    application.job_queue.run_daily(
        check_for_updates,
        time=target_time,
        days=(0,)  # 0 соответствует понедельнику
    )


async def check_for_updates(context: ContextTypes.DEFAULT_TYPE):
    repo_path = os.path.abspath('.')
    repo = Repo(repo_path)

    # Получаем текущий коммит
    current_commit = repo.head.commit

    try:
        # Получаем обновления из удаленного репозитория
        origin = repo.remotes.origin
        origin.fetch()
        remote_commit = repo.commit('origin/main')

        if current_commit.hexsha != remote_commit.hexsha:
            # Есть обновления
            diff = current_commit.diff(remote_commit)
            changes = '\n'.join([f"- {item.a_path}" for item in diff])
            message = (
                f"Доступно обновление бота.\n"
                f"Измененные файлы:\n{changes}\n\n"
                f"Новая версия: {remote_commit.hexsha[:7]}"
            )
            keyboard = [[InlineKeyboardButton("Обновить бота", callback_data='update_bot')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=ADMIN_ID, text=message, reply_markup=reply_markup)
        else:
            # Нет обновлений
            logger.info("Обновлений не найдено.")
    except GitCommandError as e:
        logger.error(f"Ошибка при проверке обновлений: {e}")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Ошибка при проверке обновлений: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


def main():
    # Создаем приложение бота
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    # Регистрируем обработчики
    register_handlers(application)

    # Запускаем проверку лицензий
    schedule_license_checks(application)

    # Запускаем проверку сертификатов каждые 12 часов
    application.job_queue.run_repeating(
        check_certificates,
        interval=12 * 60 * 60,  # Каждые 12 часов
        first=10,  # Первое выполнение через 10 секунд после запуска бота
    )

    # Запускаем планировщик проверки обновлений
    schedule_update_checks(application)

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()
