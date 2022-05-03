"""Unique language code and name constraints

Revision ID: 40b74283a084
Revises: 6454d7d69156
Create Date: 2022-05-03 13:42:13.480913

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "40b74283a084"
down_revision = "6454d7d69156"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(
        None,
        "appointment_slots",
        "appointments",
        ["occupied_by_appointment"],
        ["id"],
        use_alter=True,
    )
    op.create_unique_constraint(None, "languages", ["name"])
    op.create_unique_constraint(None, "languages", ["code"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "languages", type_="unique")
    op.drop_constraint(None, "languages", type_="unique")
    op.drop_constraint(None, "appointment_slots", type_="foreignkey")
    # ### end Alembic commands ###
