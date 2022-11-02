import yaml
import os
from pydantic import (
    BaseSettings,
    PostgresDsn,
    FilePath,
    HttpUrl,
    RedisDsn
)


def yaml_settings(settings: BaseSettings):
    with open(os.environ.get('ZTPAPI_CONFIG')) as cfg_file:
        result = yaml.safe_load(cfg_file)
    return result


class Settings(BaseSettings):
    CONFIG: FilePath
    PROJECT_DB: PostgresDsn
    DHCP_DB: PostgresDsn
    USERSIDE_URL: HttpUrl
    USERSIDE_KEY: str
    NETBOX_URL: HttpUrl
    NETBOX_TOKEN: str
    TFTP_SERVER: str
    TFTP_USERNAME: str
    TFTP_PASSWORD: str
    TFTP_FOLDER_STRUCTURE: dict[str, str]
    DEVICEAPI_URL: HttpUrl
    CELERY_BROKER: RedisDsn
    CELERY_BACKEND: RedisDsn

    class Config:
        env_prefix = 'ZTPAPI_'
        env_file = None
        extra = 'ignore'

        @classmethod
        def customise_sources(
                cls,
                init_settings,
                env_settings,
                file_secret_settings,
        ):
            return (
                init_settings,
                yaml_settings,
                env_settings,
                file_secret_settings,
            )
