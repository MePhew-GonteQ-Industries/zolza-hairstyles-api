"""add temporary_closure column to appointment_slots table

Revision ID: be60e4b8c659
Revises: 58620602b811
Create Date: 2025-05-17 01:20:23.969446

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "be60e4b8c659"
down_revision = "58620602b811"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "appointment_slots",
        sa.Column(
            "temporary_closure", sa.Boolean(), server_default="false", nullable=False
        ),
    )


def downgrade():
    op.drop_column("appointment_slots", "temporary_closure")
