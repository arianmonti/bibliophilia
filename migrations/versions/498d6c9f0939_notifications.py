"""notifications

Revision ID: 498d6c9f0939
Revises: ef5e8960875c
Create Date: 2020-08-23 17:45:04.457969

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '498d6c9f0939'
down_revision = 'ef5e8960875c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notification', sa.Column('timestamp', sa.Float(), nullable=True))
    op.create_index(op.f('ix_notification_timestamp'), 'notification', ['timestamp'], unique=False)
    op.drop_index('ix_notification_time', table_name='notification')
    op.drop_column('notification', 'time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notification', sa.Column('time', mysql.FLOAT(), nullable=True))
    op.create_index('ix_notification_time', 'notification', ['time'], unique=False)
    op.drop_index(op.f('ix_notification_timestamp'), table_name='notification')
    op.drop_column('notification', 'timestamp')
    # ### end Alembic commands ###
