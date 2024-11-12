import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

TOKEN = config.get('Telegram', 'TOKEN')
ADMIN_ID = int(config.get('Telegram', 'ADMIN_ID'))
DB_PATH = config.get('Database', 'DB_PATH')
