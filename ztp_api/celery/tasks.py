from celery import current_app


def get_port_vlan(ip, port):
    pass


def modify_port_vlan(ip, port, vlan, action, mode) -> None:
    pass


def ping(ip) -> bool:
    pass


def check_files_downloaded(ip) -> bool:
    pass


@current_app.task
def ztp(ip: str,
        autochange_vlan: bool = False,
        parent_switch: str = None,
        parent_port: str = None,
        management_vlan: str = None,
        pull_full_config: bool = False,
        full_config_commands: list[str] = None,
        full_config_filename: str = None):
    # TODO Сменить влан на вышестоящем (optional)
    # TODO Дождаться пока начнет пинговаться
    # TODO Дождаться пока скачает оба файла и перестанет пинговаться
    # TODO Сменить влан на вышестоящем (optional)
    # TODO Дождаться пока начнет пинговаться
    # TODO Залить полный конфиг (optional)
    pass
