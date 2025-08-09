import random
import string

from config import Config
from settings import a_settings


def generate_code(length=6) -> str:
    return ''.join(random.choices(string.digits, k=length))

def is_admin(tg_id: int) -> bool:
    return tg_id in Config.ADMIN_IDS

def is_debug() -> bool:
    return a_settings.DEBUG