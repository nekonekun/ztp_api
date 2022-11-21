import yaml
import os
from pydantic import (
    BaseSettings,
    HttpUrl,
    IPvAnyAddress
)


def yaml_settings(settings: BaseSettings):
    with open(os.environ.get('ZTPAPIRQ_CONFIG')) as cfg_file:
        result = yaml.safe_load(cfg_file)
    return result


class Settings(BaseSettings):
    TFTP_SERVER: IPvAnyAddress
    TFTP_USERNAME: str
    TFTP_PASSWORD: str
    DEVICEAPI_URL: HttpUrl
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_IDS: list[int]
    SELF_URL: str

    class Config:
        env_prefix = 'ZTPAPIRQ_'
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
