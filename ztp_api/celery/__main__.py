from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import celery
from pathlib import Path
import os
from ztp_api.celery.settings import Settings


ENV_VAR_PREFIX = 'ZTPAPIRQ_'

parser = ArgumentParser(
    auto_env_var_prefix=ENV_VAR_PREFIX, allow_abbrev=False,
    formatter_class=ArgumentDefaultsHelpFormatter,
    add_help=True,
)

group = parser.add_argument_group('Configuration')
group.add_argument('--broker', '-b', default='amqp://localhost', help='Broker URL')
group.add_argument('--result', '-r', default='rpc://localhost', help='Result backend')

group = parser.add_argument_group('Config file')
group.add_argument('--config', '-c', default=str(Path(__file__).resolve().parent.parent.parent / 'settings.yml'), help='config file path')


def main():
    args = parser.parse_args()

    os.environ['ZTPAPIRQ_CONFIG'] = args.config

    s = Settings()

    app = celery.Celery(include=['ztp_api.celery.tasks'], broker=args.broker, backend=args.result)

    app.worker_main(argv=['worker', '--loglevel=info'])
