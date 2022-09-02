import os
from alembic.config import CommandLine, Config
from pathlib import Path


PROJECT_PATH = Path(__file__).parent.parent.resolve()


def main():
    alembic = CommandLine()
    alembic.parser.add_argument(
        '--pg-url', default=os.getenv('ZTP_API_PG_URL'),
        help='Database URL [env var: ZTP_API_PG_URL]'
    )

    # Transforming relative path to absolute.
    options = alembic.parser.parse_args()
    if not os.path.isabs(options.config):
        options.config = os.path.join(PROJECT_PATH, options.config)

    # Creating Alembic configuration object.
    config = Config(file_=options.config, ini_section=options.name,
                    cmd_opts=options)

    # Substituting path to alembic folder to absolute path.
    # Needed for Alembic to locate env.py, migration genetion templates and migrations themselves.
    alembic_location = config.get_main_option('script_location')
    if not os.path.isabs(alembic_location):
        config.set_main_option('script_location',
                               os.path.join(PROJECT_PATH, alembic_location))

    # Changing sqlalchemy.url value from Alembic config
    config.set_main_option('sqlalchemy.url', options.pg_url)

    # Run Alembic command
    exit(alembic.run_cmd(config, options))


if __name__ == '__main__':
    main()
