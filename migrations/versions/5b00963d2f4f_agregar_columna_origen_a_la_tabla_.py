"""Agregar columna origen a la tabla Problema

Revision ID: 5b00963d2f4f
Revises: ddc87436a608
Create Date: 2024-08-07 14:06:53.457610

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b00963d2f4f'
down_revision = 'ddc87436a608'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('problema', schema=None) as batch_op:
        batch_op.add_column(sa.Column('origen', sa.String(length=50), nullable=True))
        batch_op.alter_column('archivo',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=300),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('problema', schema=None) as batch_op:
        batch_op.alter_column('archivo',
               existing_type=sa.String(length=300),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
        batch_op.drop_column('origen')

    # ### end Alembic commands ###
