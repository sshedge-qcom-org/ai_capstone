"""procurement dashboard data model"""

import sqlalchemy as sa
from alembic import op

revision = "5090c7b233ca"
down_revision = "29f5ef8b01ec"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "categories",
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("rating", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("average_price_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("average_delivery_days", sa.Integer(), nullable=False),
        sa.Column("reliability_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("contact_person", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.CheckConstraint("average_delivery_days >= 1 AND average_delivery_days <= 365"),
        sa.CheckConstraint("average_price_score >= 0 AND average_price_score <= 100"),
        sa.CheckConstraint("rating >= 0 AND rating <= 5"),
        sa.CheckConstraint("reliability_score >= 0 AND reliability_score <= 100"),
        sa.ForeignKeyConstraint(
            ["category"],
            ["categories.name"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suppliers_category"), "suppliers", ["category"], unique=False)
    op.create_table(
        "purchase_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("estimated_budget", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("target_delivery_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('pending','approved','rejected','revision','ordered')"),
        sa.CheckConstraint("estimated_budget > 0 AND estimated_budget <= 9999999999.99"),
        sa.CheckConstraint("quantity > 0"),
        sa.ForeignKeyConstraint(
            ["category"],
            ["categories.name"],
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_purchase_requests_created_at"), "purchase_requests", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_purchase_requests_requested_by"),
        "purchase_requests",
        ["requested_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_purchase_requests_status"), "purchase_requests", ["status"], unique=False
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("order_date", sa.DateTime(), nullable=False),
        sa.Column("delivery_date", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('created','processing','shipped','delivered')"),
        sa.CheckConstraint("amount > 0"),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["purchase_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index(op.f("ix_orders_delivery_date"), "orders", ["delivery_date"], unique=False)
    op.create_index(op.f("ix_orders_order_date"), "orders", ["order_date"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index(op.f("ix_orders_supplier_id"), "orders", ["supplier_id"], unique=False)
    op.execute("ALTER TABLE users ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id)")


def downgrade():
    op.drop_column("users", "supplier_id")
    op.drop_index(op.f("ix_orders_supplier_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_date"), table_name="orders")
    op.drop_index(op.f("ix_orders_delivery_date"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_purchase_requests_status"), table_name="purchase_requests")
    op.drop_index(op.f("ix_purchase_requests_requested_by"), table_name="purchase_requests")
    op.drop_index(op.f("ix_purchase_requests_created_at"), table_name="purchase_requests")
    op.drop_table("purchase_requests")
    op.drop_index(op.f("ix_suppliers_category"), table_name="suppliers")
    op.drop_table("suppliers")
    op.drop_table("categories")
