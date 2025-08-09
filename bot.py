import asyncio
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from api.main import app as fastapi_app
from handlers import register, admin
from uvicorn import Config as UvicornConfig, Server as UvicornServer
from bot_instance import bot
from logging.config import dictConfig

dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s | %(levelprefix)s | %(name)s | %(message)s",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": "%(asctime)s | %(levelprefix)s | %(client_addr)s - \"%(request_line)s\" %(status_code)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        "crystal": {"handlers": ["default"], "level": "DEBUG"},
    },
})

async def main():
    dp = Dispatcher(memory=MemoryStorage())

    dp.include_routers(
        register.router,
        admin.router,
    )

    config = UvicornConfig(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = UvicornServer(config)
    fastapi_task = asyncio.create_task(server.serve())

    await dp.start_polling(bot)

    await fastapi_task


if __name__ == "__main__":
    asyncio.run(main())
