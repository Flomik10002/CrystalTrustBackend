from aiogram import Bot

from settings import a_settings

bot = Bot(token=a_settings.BOT_TOKEN)

def get_bot():
    return bot
