"""Initial database schema with all tables.

Revision ID: 001_initial
Revises: None
Create Date: 2025-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Covered delivery areas
    op.create_table(
        "covered_areas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name_ar", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=True),
        sa.Column("city", sa.String(50), server_default="Riyadh", nullable=False),
        sa.Column("aliases_ar", postgresql.ARRAY(sa.String(100)), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_covered_areas_name_ar", "covered_areas", ["name_ar"])
    op.create_index(
        "idx_covered_areas_active",
        "covered_areas",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # Menu items
    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=True),
        sa.Column("description_ar", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("category_ar", sa.String(100), nullable=False),
        sa.Column("category_en", sa.String(100), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("is_combo", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("preparation_time_mins", sa.Integer(), server_default="15", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_menu_items_category", "menu_items", ["category_ar"])
    op.create_index(
        "idx_menu_items_available",
        "menu_items",
        ["is_available"],
        postgresql_where=sa.text("is_available = true"),
    )

    # Modifier groups (e.g., "Size", "Spice Level")
    op.create_table(
        "modifier_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name_ar", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=True),
        sa.Column(
            "selection_type",
            sa.String(20),
            server_default="single",
            nullable=False,
        ),
        sa.Column("min_selections", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_selections", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Individual modifiers
    op.create_table(
        "modifiers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("name_ar", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=True),
        sa.Column(
            "price_adjustment",
            sa.Numeric(10, 2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("is_available", sa.Boolean(), server_default="true", nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["modifier_groups.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_modifiers_group", "modifiers", ["group_id"])

    # Link menu items to modifier groups
    op.create_table(
        "item_modifier_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("modifier_group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["menu_item_id"],
            ["menu_items.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["modifier_group_id"],
            ["modifier_groups.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("menu_item_id", "modifier_group_id"),
    )
    op.create_index("idx_item_modifiers_item", "item_modifier_groups", ["menu_item_id"])

    # Promo codes
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "min_order_amount",
            sa.Numeric(10, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("max_discount", sa.Numeric(10, 2), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_promo_codes_code", "promo_codes", ["code"])

    # Orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("customer_name", sa.String(200), nullable=False),
        sa.Column("customer_phone", sa.String(20), nullable=False),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("delivery_area_id", sa.Integer(), nullable=True),
        sa.Column(
            "order_type",
            sa.String(20),
            server_default="delivery",
            nullable=False,
        ),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "delivery_fee",
            sa.Numeric(10, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "discount_amount",
            sa.Numeric(10, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("promo_code_id", sa.Integer(), nullable=True),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["delivery_area_id"], ["covered_areas.id"]),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_orders_session", "orders", ["session_id"])
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_phone", "orders", ["customer_phone"])

    # Order line items
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("item_name_ar", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("special_instructions", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_order_items_order", "order_items", ["order_id"])

    # Order item modifiers
    op.create_table(
        "order_item_modifiers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column("modifier_id", sa.Integer(), nullable=False),
        sa.Column("modifier_name_ar", sa.String(100), nullable=False),
        sa.Column("price_adjustment", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["modifier_id"], ["modifiers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_order_item_modifiers_item",
        "order_item_modifiers",
        ["order_item_id"],
    )

    # Chat sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(100), nullable=False),
        sa.Column("state", sa.String(30), server_default="S0_INIT", nullable=False),
        sa.Column("customer_name", sa.String(200), nullable=True),
        sa.Column("customer_phone", sa.String(20), nullable=True),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("delivery_area_id", sa.Integer(), nullable=True),
        sa.Column("order_type", sa.String(20), nullable=True),
        sa.Column(
            "cart",
            postgresql.JSONB(),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("applied_promo_code", sa.String(50), nullable=True),
        sa.Column(
            "conversation_history",
            postgresql.JSONB(),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "conversation_summary_ar",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now() + interval '2 hours'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["delivery_area_id"], ["covered_areas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_sessions_state", "sessions", ["state"])
    op.create_index("idx_sessions_expires", "sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("order_item_modifiers")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("promo_codes")
    op.drop_table("item_modifier_groups")
    op.drop_table("modifiers")
    op.drop_table("modifier_groups")
    op.drop_table("menu_items")
    op.drop_table("covered_areas")
