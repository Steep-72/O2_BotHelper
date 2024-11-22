# -*- coding: utf-8 -*-
# database_manager.py

import sqlite3
from bot_config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаем таблицу для уведомлений
    cursor.execute(
        '''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company TEXT,
        product TEXT,
        expiry_date TEXT,
        notify_date TEXT,
        quantity TEXT,
        notification_type TEXT
    )
    '''
    )

    # Создаем таблицу для сайтов
    cursor.execute(
        '''
    CREATE TABLE IF NOT EXISTS monitored_sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site TEXT UNIQUE COLLATE NOCASE,
        expiry_date TEXT,
        common_name TEXT
    )
    '''
    )

    # Создаем таблицу для разрешенных пользователей
    cursor.execute(
        '''
    CREATE TABLE IF NOT EXISTS allowed_users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT
    )
    '''
    )

    # Создаем таблицу для запросов на доступ
    cursor.execute(
        '''
    CREATE TABLE IF NOT EXISTS access_requests (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT
    )
    '''
    )

    # Создаем таблицу для разрешенных чатов
    cursor.execute(
        '''
    CREATE TABLE IF NOT EXISTS allowed_chats (
        chat_id INTEGER PRIMARY KEY
    )
    '''
    )

    conn.commit()
    conn.close()


# Функции для работы с уведомлениями о лицензиях
def save_notification_to_db(
    user_id, company, product, expiry_date, notify_date, quantity, notification_type
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO notifications (user_id, company, product, expiry_date, notify_date, quantity, notification_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
            (user_id, company, product, expiry_date, notify_date, quantity, notification_type),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_notification_from_db(notif_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notifications WHERE id = ?', (notif_id,))
    conn.commit()
    conn.close()


def get_notifications_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, user_id, company, product, expiry_date, notify_date, quantity, notification_type FROM notifications'
    )
    notifications = cursor.fetchall()
    conn.close()
    return notifications


# Функции для работы с мониторингом сайтов
def add_monitored_site(site):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO monitored_sites (site) VALUES (?)', (site.lower(),))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def add_monitored_sites(sites):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    added_sites = []
    failed_sites = []
    for site in sites:
        try:
            cursor.execute('INSERT INTO monitored_sites (site) VALUES (?)', (site.lower(),))
            added_sites.append(site)
        except sqlite3.IntegrityError:
            failed_sites.append(site)
    conn.commit()
    conn.close()
    return added_sites, failed_sites


def get_monitored_sites():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT site FROM monitored_sites')
    sites = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sites


def remove_monitored_site(site):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM monitored_sites WHERE site = ?', (site.lower(),))
    conn.commit()
    conn.close()


def update_certificate_info(site, expiry_date, common_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE monitored_sites SET expiry_date = ?, common_name = ? WHERE site = ?
    ''',
        (expiry_date, common_name, site.lower()),
    )
    conn.commit()
    conn.close()


def get_certificate_info(site):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT expiry_date, common_name FROM monitored_sites WHERE site = ?
    ''',
        (site.lower(),),
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return {'expiry_date': result[0], 'common_name': result[1]}
    else:
        return None


# Функции для управления разрешенными пользователями
def add_allowed_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT OR IGNORE INTO allowed_users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''',
        (user_id, username, first_name, last_name),
    )
    conn.commit()
    conn.close()


def get_allowed_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM allowed_users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return set(users)


def is_user_allowed(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM allowed_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


# Функции для управления запросами на доступ
def add_access_request(user_id, username, first_name, last_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT OR IGNORE INTO access_requests (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''',
        (user_id, username, first_name, last_name),
    )
    conn.commit()
    conn.close()


def remove_access_request(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM access_requests WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def is_access_request_pending(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM access_requests WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_access_request_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT username, first_name, last_name FROM access_requests WHERE user_id = ?',
        (user_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result


# Функции для управления разрешенными чатами
def add_allowed_chat(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO allowed_chats (chat_id) VALUES (?)', (chat_id,))
    conn.commit()
    conn.close()


def is_chat_allowed(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM allowed_chats WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_allowed_chats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id FROM allowed_chats')
    chats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chats
