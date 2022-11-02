import celery

from ztp_api.api.db.session import get_async_session
from pyuserside.api.asynchronous import UsersideAPI
import aiohttp
from functools import lru_cache
from ztp_api.api.settings import Settings
from fastapi import Depends
from ztp_api.api.services.tftp import TftpWrapper


@lru_cache()
def get_settings():
    return Settings()


async def get_db(settings: Settings = Depends(get_settings)):
    database_url = settings.PROJECT_DB
    session = get_async_session(database_url)()
    try:
        yield session
    finally:
        await session.close()


async def get_kea_db(settings: Settings = Depends(get_settings)):
    database_url = settings.DHCP_DB
    session = get_async_session(database_url)()
    try:
        yield session
    finally:
        await session.close()


async def get_us_api(settings: Settings = Depends(get_settings)):
    userside_url = settings.USERSIDE_URL
    userside_key = settings.USERSIDE_KEY
    usapi = UsersideAPI(url=userside_url, key=userside_key)
    usapi._session = aiohttp.ClientSession()
    try:
        yield usapi
    finally:
        await usapi._session.close()


async def get_netbox_session(settings: Settings = Depends(get_settings)):
    netbox_url = settings.NETBOX_URL
    netbox_token = settings.NETBOX_TOKEN
    auth_header = {'Authorization': f'Token {netbox_token}'}
    session = aiohttp.ClientSession(base_url=netbox_url, headers=auth_header, connector=aiohttp.TCPConnector(verify_ssl=False))
    try:
        yield session
    finally:
        await session.close()


def get_tftp_session(settings: Settings = Depends(get_settings)):
    tftp_server = settings.TFTP_SERVER
    tftp_username = settings.TFTP_USERNAME
    tftp_password = settings.TFTP_PASSWORD
    ftp_session = TftpWrapper(tftp_server, tftp_username, tftp_password)
    ftp_session.start()
    try:
        yield ftp_session
    finally:
        ftp_session.finish()


@lru_cache()
def get_celery(settings=Depends(get_settings)):
    cel = celery.Celery(backend=settings.CELERY_BACKEND, broker=settings.CELERY_BROKER)
    try:
        yield cel
    finally:
        cel.close()
