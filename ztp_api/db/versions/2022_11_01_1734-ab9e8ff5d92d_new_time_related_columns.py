"""new time-related columns

Revision ID: ab9e8ff5d92d
Revises: 7e3019b69df5
Create Date: 2022-11-01 17:34:38.800005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab9e8ff5d92d'
down_revision = '7e3019b69df5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('entries', sa.Column('created_at', sa.DateTime(), server_default=sa.sql.func.now(), nullable=True))
    op.add_column('entries', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('entries', sa.Column('finished_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('entries', 'created_at')
    op.drop_column('entries', 'started_at')
    op.drop_column('entries', 'finished_at')

