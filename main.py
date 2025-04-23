import logging
from telebot import TeleBot
import config
from handlers import register_handlers
from database import Database

logging.basicConfig(level=logging.INFO)

def main():
    bot = TeleBot(config.BOT_TOKEN)
    db = Database(config.DATABASE_NAME)
    register_handlers(bot, db)
    print("Бот запущен...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()