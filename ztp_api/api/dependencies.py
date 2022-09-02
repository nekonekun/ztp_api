from ztp_api.api.db.session import get_async_session
from pyuserside.api.asynchronous import UsersideAPI
import aiohttp
from functools import lru_cache
from ztp_api.api.settings import Settings
from fastapi import Depends
from ftplib import FTP


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
    session = aiohttp.ClientSession(base_url=netbox_url, headers=auth_header)
    try:
        yield session
    finally:
        await session.close()


def get_tftp_session(settings: Settings = Depends(get_settings)):
    tftp_server = settings.TFTP_SERVER
    tftp_username = settings.TFTP_USERNAME
    tftp_password = settings.TFTP_PASSWORD
    ftp_session = FTP(tftp_server, tftp_username, tftp_password)
    ftp_session.connect()
    ftp_session.login(tftp_username, tftp_password)
    try:
        yield ftp_session
    finally:
        ftp_session.close()
