"""
Alembic migration: add_agent_evaluation_table
=============================================
Adds the agent_evaluations table for persisting
per-run evaluation scores from the Reflection/Evaluation pipeline.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f1a2b3c4d5e6"
down_revision = "605e80810f09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        # Per-dimension scores
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("cost_score", sa.Float(), nullable=True),
        sa.Column("latency_score", sa.Float(), nullable=True),
        sa.Column("reasoning_score", sa.Float(), nullable=True),
        sa.Column("tool_usage_score", sa.Float(), nullable=True),
        sa.Column("knowledge_usage_score", sa.Float(), nullable=True),
        sa.Column("brand_alignment_score", sa.Float(), nullable=True),
        sa.Column("safety_score", sa.Float(), nullable=True),
        # Reflection sub-scores
        sa.Column("hallucination_score", sa.Float(), nullable=True),
        sa.Column("grammar_score", sa.Float(), nullable=True),
        sa.Column("tone_score", sa.Float(), nullable=True),
        sa.Column("completeness_score", sa.Float(), nullable=True),
        # Aggregate
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        # Reflection text
        sa.Column("critique", sa.Text(), nullable=True),
        sa.Column("suggested_edits", sa.Text(), nullable=True),
        sa.Column("is_satisfactory", sa.Boolean(), nullable=False, server_default="true"),
        # Metadata
        sa.Column("meta_data", sa.JSON(), nullable=True),
        # Audit
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True, server_default="1"),
    )
    op.create_index("ix_agent_evaluations_run_id", "agent_evaluations", ["run_id"])
    op.create_index("ix_agent_evaluations_org_id", "agent_evaluations", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_evaluations_org_id", table_name="agent_evaluations")
    op.drop_index("ix_agent_evaluations_run_id", table_name="agent_evaluations")
    op.drop_table("agent_evaluations")
