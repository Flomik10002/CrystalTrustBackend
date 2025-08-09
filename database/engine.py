from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from settings import a_settings
from utils import is_debug

if is_debug():
    engine = create_async_engine(a_settings.POSTGRES_DSN_TEST, echo=a_settings.DEBUG)
else:
    engine = create_async_engine(a_settings.POSTGRES_DSN, echo=a_settings.DEBUG)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass