"""Agregar columna fecha_hora a la tabla Problema

Revision ID: e2cfe2f5c3d9
Revises: afe54791e8ee
Create Date: 2024-07-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'e2cfe2f5c3d9'
down_revision = 'afe54791e8ee'
branch_labels = None
depends_on = None

def upgrade():
    # Set a default value for the new column
    op.add_column('problema', sa.Column('fecha_hora', sa.String(length=50), nullable=False, server_default=sa.text("'1970-01-01 00:00:00'")))

def downgrade():
    op.drop_column('problema', 'fecha_hora')


    op.create_table('_alembic_tmp_problema',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('estado', sa.VARCHAR(length=100), nullable=False),
    sa.Column('unidad_medica', sa.VARCHAR(length=100), nullable=False),
    sa.Column('categoria', sa.VARCHAR(length=100), nullable=False),
    sa.Column('subcategoria', sa.VARCHAR(length=100), nullable=True),
    sa.Column('descripcion', sa.VARCHAR(length=300), nullable=False),
    sa.Column('nivel_riesgo', sa.VARCHAR(length=50), nullable=False),
    sa.Column('lat', sa.FLOAT(), nullable=False),
    sa.Column('lon', sa.FLOAT(), nullable=False),
    sa.Column('ticket_id', sa.VARCHAR(length=10), nullable=False),
    sa.Column('reportado_por_operativo', sa.BOOLEAN(), nullable=True),
    sa.Column('actualizaciones', sa.TEXT(), nullable=True),
    sa.Column('estado_problema', sa.VARCHAR(length=50), nullable=True),
    sa.Column('fecha_hora', sa.VARCHAR(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ticket_id')
    )
    # ### end Alembic commands ###
