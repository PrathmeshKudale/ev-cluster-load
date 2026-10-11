"""Add authentication columns to clean.users and row-level security for cluster isolation.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add authentication & RBAC columns to clean.users
    op.add_column("users", sa.Column("username", sa.String(64), nullable=True), schema="clean")
    op.add_column("users", sa.Column("email", sa.String(128), nullable=True), schema="clean")
    op.add_column("users", sa.Column("hashed_password", sa.String(256), nullable=True), schema="clean")
    op.add_column(
        "users",
        sa.Column("role", sa.String(32), server_default="driver", nullable=False),
        schema="clean",
    )
    op.add_column("users", sa.Column("cluster_id", sa.String(64), nullable=True), schema="clean")
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        schema="clean",
    )

    # 2. Add foreign key from clean.users.cluster_id to clean.clusters.id
    op.create_foreign_key(
        "fk_clean_users_cluster_id",
        source_table="users",
        referent_table="clusters",
        local_cols=["cluster_id"],
        remote_cols=["id"],
        source_schema="clean",
        referent_schema="clean",
        ondelete="SET NULL",
    )

    # 3. Add unique indexes for username and email
    op.create_index("ix_clean_users_username", "users", ["username"], unique=True, schema="clean")
    op.create_index("ix_clean_users_email", "users", ["email"], unique=True, schema="clean")

    # 4. Enable Row-Level Security (RLS) on cluster-scoped tables
    op.execute("ALTER TABLE clean.stations ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY cluster_isolation_stations ON clean.stations
        FOR ALL
        USING (
            current_setting('app.cluster_id', true) IS NULL
            OR current_setting('app.cluster_id', true) = ''
            OR cluster_id = current_setting('app.cluster_id', true)
        );
    """)

    op.execute("ALTER TABLE clean.transformers ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY cluster_isolation_transformers ON clean.transformers
        FOR ALL
        USING (
            current_setting('app.cluster_id', true) IS NULL
            OR current_setting('app.cluster_id', true) = ''
            OR cluster_id = current_setting('app.cluster_id', true)
        );
    """)

    op.execute("ALTER TABLE clean.clusters ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY cluster_isolation_clusters ON clean.clusters
        FOR ALL
        USING (
            current_setting('app.cluster_id', true) IS NULL
            OR current_setting('app.cluster_id', true) = ''
            OR id = current_setting('app.cluster_id', true)
        );
    """)


def downgrade() -> None:
    # 1. Drop RLS policies and disable RLS
    op.execute("DROP POLICY IF EXISTS cluster_isolation_clusters ON clean.clusters;")
    op.execute("ALTER TABLE clean.clusters DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS cluster_isolation_transformers ON clean.transformers;")
    op.execute("ALTER TABLE clean.transformers DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS cluster_isolation_stations ON clean.stations;")
    op.execute("ALTER TABLE clean.stations DISABLE ROW LEVEL SECURITY;")

    # 2. Drop unique indexes
    op.drop_index("ix_clean_users_email", table_name="users", schema="clean")
    op.drop_index("ix_clean_users_username", table_name="users", schema="clean")

    # 3. Drop foreign key constraint
    op.drop_constraint("fk_clean_users_cluster_id", "users", schema="clean", type_="foreignkey")

    # 4. Drop added columns
    op.drop_column("users", "is_active", schema="clean")
    op.drop_column("users", "cluster_id", schema="clean")
    op.drop_column("users", "role", schema="clean")
    op.drop_column("users", "hashed_password", schema="clean")
    op.drop_column("users", "email", schema="clean")
    op.drop_column("users", "username", schema="clean")
