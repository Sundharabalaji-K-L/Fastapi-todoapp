"""add apt_num

Revision ID: 1a0092f243bb
Revises: 
Create Date: 2024-07-26 10:42:25.662298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a0092f243bb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("address", sa.Column('apt_num', sa.Integer(), nullable=True))


def downgrade() -> None:
    pass
