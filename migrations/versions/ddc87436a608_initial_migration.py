"""Initial migration

Revision ID: ddc87436a608
Revises: 
Create Date: 2024-08-07 10:40:02.783031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddc87436a608'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('problema',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('estado', sa.String(length=100), nullable=False),
    sa.Column('unidad_medica', sa.String(length=100), nullable=False),
    sa.Column('categoria', sa.String(length=100), nullable=False),
    sa.Column('subcategoria', sa.String(length=100), nullable=True),
    sa.Column('descripcion', sa.String(length=300), nullable=False),
    sa.Column('nivel_riesgo', sa.String(length=50), nullable=False),
    sa.Column('lat', sa.Float(), nullable=False),
    sa.Column('lon', sa.Float(), nullable=False),
    sa.Column('ticket_id', sa.String(length=10), nullable=False),
    sa.Column('reportado_por_operativo', sa.Boolean(), nullable=True),
    sa.Column('actualizaciones', sa.Text(), nullable=True),
    sa.Column('estado_problema', sa.String(length=50), nullable=True),
    sa.Column('fecha_hora', sa.String(length=50), nullable=False),
    sa.Column('aceptado', sa.String(length=50), nullable=True),
    sa.Column('nombre_reportante', sa.String(length=100), nullable=False),
    sa.Column('responsable_problema', sa.String(length=100), nullable=False),
    sa.Column('correo_electronico', sa.String(length=100), nullable=False),
    sa.Column('archivo', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ticket_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('problema')
    # ### end Alembic commands ###
