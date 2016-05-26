"""add teams

Revision ID: 3f74c836ee
Revises: 55b0b89698b
Create Date: 2016-05-26 12:38:45.844345

"""

# revision identifiers, used by Alembic.
revision = '3f74c836ee'
down_revision = '55b0b89698b'
branch_labels = ()
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('team_permssions',
    sa.Column('team_id', sa.Integer(), nullable=True),
    sa.Column('need_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['need_id'], ['need.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['userteam.id'], ),
    sa.UniqueConstraint('team_id', 'need_id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('team_permssions')
    ### end Alembic commands ###
