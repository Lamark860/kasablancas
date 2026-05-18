"""add leads table

Revision ID: a1b2c3d4e5f6
Revises: 7e5936341e96
Create Date: 2026-05-18 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7e5936341e96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact', sa.String(length=128), nullable=False),
        sa.Column('want_consultation', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('first_name', sa.String(length=64), nullable=False),
        sa.Column('birth_date', sa.String(length=10), nullable=False),
        sa.Column('birth_place', sa.String(length=128), nullable=True),
        sa.Column('birth_lat', sa.Float(), nullable=True),
        sa.Column('birth_lon', sa.Float(), nullable=True),
        sa.Column('birth_tz', sa.String(length=64), nullable=True),
        sa.Column('eye_color', sa.String(length=16), nullable=True),
        sa.Column('main_plant_slug', sa.String(length=64), nullable=True),
        sa.Column('main_plant_name', sa.String(length=128), nullable=True),
        sa.Column('companions', sa.JSON(), nullable=True),
        sa.Column('city', sa.String(length=64), nullable=True),
        sa.Column('source', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=16), server_default='new', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('new','contacted','won','lost')", name='ck_leads_status'),
    )
    op.create_index('idx_leads_status', 'leads', ['status'])
    op.create_index('idx_leads_created_at', 'leads', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_leads_created_at', table_name='leads')
    op.drop_index('idx_leads_status', table_name='leads')
    op.drop_table('leads')
