from fastapi import FastAPI
import uvicorn
from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from setproctitle import setproctitle
import os
import sys
from pathlib import Path
from ztp_api.api.routers.entries import entries_router
from ztp_api.api.routers.models import models_router
from ztp_api.api.settings import Settings


ENV_VAR_PREFIX = 'ZTPAPI_'

app = FastAPI(docs_url="/documentation", redoc_url=None, )


app.include_router(entries_router, prefix='/entries', tags=['Entries'])

app.include_router(models_router, prefix='/models', tags=['Models'])


parser = ArgumentParser(
    auto_env_var_prefix=ENV_VAR_PREFIX, allow_abbrev=False,
    formatter_class=ArgumentDefaultsHelpFormatter,
    add_help=True,
)

group = parser.add_argument_group('Bind')
group.add_argument('--bind', '-b', default='ipport',
                   choices=('socket', 'ipport'))
group.add_argument('--ip-address', '-i', default='0.0.0.0',
                   help='IP address to listen')
group.add_argument('--port', '-p', type=int, default=8000,
                   help='Port to listen')
group.add_argument('--socket', '-s', default='deviceapi.sock',
                   help='UNIX socket')

group = parser.add_argument_group('Config file')
group.add_argument('--config', '-c', default=str(Path(__file__).resolve().parent.parent.parent / 'settings.yml'), help='config file path')


def main():
    args = parser.parse_args()
    uvicorn_params = {'proxy_headers': True,
                      'forwarded_allow_ips': '*'}
    if args.bind == 'socket':
        uvicorn_params['uds'] = args.socket
    else:
        uvicorn_params['host'] = args.ip_address
        uvicorn_params['port'] = args.port

    os.environ['ZTPAPI_CONFIG'] = args.config

    setproctitle(os.path.basename(sys.argv[0]))

    uvicorn.run(app=app, **uvicorn_params)
