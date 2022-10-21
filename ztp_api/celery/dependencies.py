import aiohttp
import aioftp
from ztp_api.celery.settings import Settings
from functools import lru_cache


@lru_cache
def get_settings():
    return Settings()


def get_deviceapi_session():
    settings = get_settings()
    session = aiohttp.ClientSession(settings.DEVICEAPI_URL)
    return session


async def get_ftp_session():
    settings = get_settings()
    session = aioftp.Client()
    await session.connect(settings.TFTP_SERVER)
    await session.login(settings.TFTP_USERNAME, settings.TFTP_PASSWORD)
    return session
