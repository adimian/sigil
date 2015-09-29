"""pre-release

Revision ID: 436332d8734
Revises: 
Create Date: 2015-09-29 14:22:52.272240

"""

# revision identifiers, used by Alembic.
revision = '436332d8734'
down_revision = None
branch_labels = ('default',)
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('appcontext',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('validated_at', sa.DateTime(), nullable=True),
    sa.Column('totp_secret', sa.String(length=256), nullable=True),
    sa.Column('totp_configured', sa.Boolean(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('username', sa.String(length=256), nullable=False),
    sa.Column('_password', sa.String(length=256), nullable=True),
    sa.Column('email', sa.String(length=256), nullable=False),
    sa.Column('api_key', sa.String(length=256), nullable=True),
    sa.Column('jpeg_photo', sa.LargeBinary(), nullable=True),
    sa.Column('firstname', sa.String(length=256), nullable=True),
    sa.Column('surname', sa.String(length=256), nullable=True),
    sa.Column('display', sa.String(length=256), nullable=True),
    sa.Column('phone_number', sa.String(length=256), nullable=True),
    sa.Column('mobile_number', sa.String(length=256), nullable=True),
    sa.Column('home_number', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('api_key'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('userteam',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('virtualgroup',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('group_member',
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('member_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['virtualgroup.id'], ),
    sa.ForeignKeyConstraint(['member_id'], ['user.id'], ),
    sa.UniqueConstraint('group_id', 'member_id')
    )
    op.create_table('need',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('app_id', sa.Integer(), nullable=True),
    sa.Column('method', sa.String(length=256), nullable=True),
    sa.Column('value', sa.String(length=256), nullable=True),
    sa.Column('resource', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['app_id'], ['appcontext.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('app_id', 'method', 'value', 'resource')
    )
    op.create_table('team_member',
    sa.Column('team_id', sa.Integer(), nullable=True),
    sa.Column('member_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['member_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['userteam.id'], ),
    sa.UniqueConstraint('team_id', 'member_id')
    )
    op.create_table('permssions',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('need_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['need_id'], ['need.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.UniqueConstraint('user_id', 'need_id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('permssions')
    op.drop_table('team_member')
    op.drop_table('need')
    op.drop_table('group_member')
    op.drop_table('virtualgroup')
    op.drop_table('userteam')
    op.drop_table('user')
    op.drop_table('appcontext')
    ### end Alembic commands ###
