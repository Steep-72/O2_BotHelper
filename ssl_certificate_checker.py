# -*- coding: utf-8 -*-
# ssl_certificate_checker.py

import logging
import ssl
import socket
from datetime import datetime
import pytz
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from database_manager import get_monitored_sites, update_certificate_info, get_allowed_chats
import asyncio
from bot_config import ADMIN_ID
from urllib.parse import urlparse

# Настройки логирования
logger = logging.getLogger(__name__)

# Настройки проверки сертификатов
TIMEZONE = pytz.timezone("Asia/Yekaterinburg")
cert_notification_status = {}


async def check_certificates(context):
    sites = get_monitored_sites()
    tasks = []
    for site in sites:
        tasks.append(process_site_certificate(site, context))

    await asyncio.gather(*tasks)


async def process_site_certificate(site, context):
    try:
        expiry_date, common_name = await get_ssl_expiry_date(site)
        expiry_date_str = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        update_certificate_info(site, expiry_date_str, common_name)

        days_to_expiry = (expiry_date.date() - datetime.now(TIMEZONE).date()).days

        message = ""
        if days_to_expiry < 0:
            days_since_expired = abs(days_to_expiry)
            message = (
                f"⚠️ Внимание! Сертификат для сайта {site} (CN: {common_name}) истёк "
                f"{expiry_date.strftime('%d.%m.%Y')} ({days_since_expired} дней назад)."
            )
        elif days_to_expiry == 0:
            message = (
                f"⚠️ Внимание! Сертификат для сайта {site} (CN: {common_name}) истекает сегодня "
                f"{expiry_date.strftime('%d.%m.%Y')}."
            )
        elif days_to_expiry <= 7 and days_to_expiry not in cert_notification_status.get(site, []):
            message = (
                f"⚠️ Внимание! Сертификат для сайта {site} (CN: {common_name}) истекает "
                f"{expiry_date.strftime('%d.%m.%Y')} (через {days_to_expiry} дней)."
            )
            cert_notification_status.setdefault(site, []).append(days_to_expiry)
        else:
            # Сброс уведомлений, если до истечения больше 10 дней
            cert_notification_status[site] = []
            logger.info(
                f"Сертификат для {site} в порядке, истекает через {days_to_expiry} дней."
            )

        if message:
            await send_notification(context, message)

    except Exception as e:
        logger.error(f"Ошибка при проверке SSL-сертификата для {site}: {e}")
        message = f"❗️ Ошибка при проверке сертификата для {site}: {e}"
        await send_notification(context, message)


async def get_ssl_expiry_date(site):
    try:
        parsed_url = urlparse(site)
        hostname = parsed_url.hostname or parsed_url.path
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Игнорируем ошибки сертификата
        # Устанавливаем тайм-аут для подключения
        sock = socket.create_connection((hostname, 443), timeout=5)
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            der_cert = ssock.getpeercert(binary_form=True)
            cert = x509.load_der_x509_certificate(der_cert, default_backend())
            expiry_date = cert.not_valid_after.replace(tzinfo=pytz.UTC).astimezone(TIMEZONE)
            common_name = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
            return expiry_date, common_name
    except socket.timeout:
        raise Exception("Тайм-аут при попытке подключения")
    except Exception as e:
        raise Exception(f"Ошибка при получении сертификата: {e}")


async def send_notification(context, message):
    allowed_chats = get_allowed_chats()
    for chat_id in allowed_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления в чат {chat_id}: {e}")
    # Отправляем уведомление админу
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)
