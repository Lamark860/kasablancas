"""add share_token to recommendations

Revision ID: f3fdcc78116e
Revises: cba770d7f617
Create Date: 2026-05-12 11:44:16.880668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3fdcc78116e'
down_revision: Union[str, Sequence[str], None] = 'cba770d7f617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('share_token', sa.String(length=48), nullable=True))
        batch_op.create_unique_constraint('uq_recommendations_share_token', ['share_token'])


def downgrade() -> None:
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.drop_constraint('uq_recommendations_share_token', type_='unique')
        batch_op.drop_column('share_token')
