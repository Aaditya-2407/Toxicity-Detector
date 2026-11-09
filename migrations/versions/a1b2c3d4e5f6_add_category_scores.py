"""Add per-category toxicity score columns

Revision ID: a1b2c3d4e5f6
Revises: 76fb0790722b
Create Date: 2026-11-09 16:46:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '76fb0790722b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('score_toxic', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('score_severe_toxic', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('score_obscene', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('score_threat', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('score_insult', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('score_identity_hate', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.drop_column('score_identity_hate')
        batch_op.drop_column('score_insult')
        batch_op.drop_column('score_threat')
        batch_op.drop_column('score_obscene')
        batch_op.drop_column('score_severe_toxic')
        batch_op.drop_column('score_toxic')
