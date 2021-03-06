"""adtaoke

Revision ID: e4f721e0d2a
Revises: 2f9fd087ac21
Create Date: 2014-09-17 21:06:54.919453

"""

# revision identifiers, used by Alembic.
revision = 'e4f721e0d2a'
down_revision = '2f9fd087ac21'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('taokes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('taoke_title', sa.String(length=256), nullable=True),
    sa.Column('taoke_image', sa.String(length=512), nullable=True),
    sa.Column('taoke_discount', sa.String(length=512), nullable=True),
    sa.Column('taoke_price', sa.Float(), nullable=True),
    sa.Column('taoke_link', sa.String(length=4000), nullable=True),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'topics', sa.Column('topic_desc', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'topics', 'topic_desc')
    op.drop_table('taokes')
    ### end Alembic commands ###
