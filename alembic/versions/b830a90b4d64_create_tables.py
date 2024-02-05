"""Create tables

Revision ID: b830a90b4d64
Revises: 
Create Date: 2023-01-18 14:33:35.189793

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b830a90b4d64"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "languages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "services",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("min_price", sa.Integer(), nullable=False),
        sa.Column("max_price", sa.Integer(), nullable=False),
        sa.Column("average_time_minutes", sa.Integer(), nullable=False),
        sa.Column("required_slots", sa.Integer(), nullable=False),
        sa.Column(
            "available", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("surname", sa.String(), nullable=False),
        sa.Column("gender", sa.String(), nullable=False),
        sa.Column(
            "permission_level",
            sa.ARRAY(sa.String()),
            server_default="{user}",
            nullable=False,
        ),
        sa.Column("verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("disabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "appointment_slots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("occupied", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "occupied_by_appointment", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("reserved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("reserved_reason", sa.String(), nullable=True),
        sa.Column("holiday", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sunday", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("break_time", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("holiday_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.DATE(), nullable=False),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["holiday_id"],
            ["holidays.id"],
        ),
        sa.ForeignKeyConstraint(
            ["occupied_by_appointment"], ["appointments.id"], use_alter=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("end_time"),
        sa.UniqueConstraint("start_time"),
    )
    op.create_table(
        "email_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_type", sa.String(), nullable=False),
        sa.Column("request_token", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "holiday_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("holiday_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["holiday_id"],
            ["holidays.id"],
        ),
        sa.ForeignKeyConstraint(
            ["language_id"],
            ["languages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "passwords",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "permission_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.Enum("user_ban", "user_unban", name="permission_event_type"),
            nullable=False,
        ),
        sa.Column(
            "performed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "performed_on_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "performed_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["performed_on_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "service_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column(
            "performed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "performed_on_service_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "performed_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["performed_on_service_id"],
            ["services.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "service_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["language_id"],
            ["languages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=False),
        sa.Column("sign_in_user_agent", sa.String(), nullable=False),
        sa.Column("sign_in_ip_address", sa.String(), nullable=False),
        sa.Column("last_user_agent", sa.String(), nullable=False),
        sa.Column("last_ip_address", sa.String(), nullable=False),
        sa.Column(
            "last_accessed",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.Column("sudo_mode_activated", sa.TIMESTAMP(), nullable=True),
        sa.Column("sudo_mode_expires", sa.TIMESTAMP(), nullable=True),
        sa.Column(
            "first_accessed",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("default_value", sa.String(), nullable=True),
        sa.Column("current_value", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "appointments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("end_slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canceled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["end_slot_id"],
            ["appointment_slots.id"],
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
        ),
        sa.ForeignKeyConstraint(
            ["start_slot_id"],
            ["appointment_slots.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "fcm_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "last_updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("(now() at time zone('utc'))"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
        sa.UniqueConstraint("token"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("fcm_tokens")
    op.drop_table("appointments")
    op.drop_table("settings")
    op.drop_table("sessions")
    op.drop_table("service_translations")
    op.drop_table("service_events")
    op.drop_table("permission_events")
    op.drop_table("passwords")
    op.drop_table("holiday_translations")
    op.drop_table("email_requests")
    op.drop_table("appointment_slots")
    op.drop_table("users")
    op.drop_table("services")
    op.drop_table("languages")
    op.drop_table("holidays")
    # ### end Alembic commands ###
