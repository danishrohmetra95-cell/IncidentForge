"""Persist Phase 2 agent output validation telemetry.

Revision ID: 0002_phase2
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_phase2"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_runs",
        sa.Column("output_validation_status", sa.Text(), nullable=True),
    )
    op.create_table(
        "critiques",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("hypothesis_id", sa.Text(), nullable=False),
        sa.Column("objections", sa.JSON(), nullable=True),
        sa.Column("assumptions", sa.JSON(), nullable=True),
        sa.Column("evidence_weaknesses", sa.JSON(), nullable=True),
        sa.Column("contradictions", sa.JSON(), nullable=True),
        sa.Column("alternatives", sa.JSON(), nullable=True),
        sa.Column("falsification_criteria", sa.JSON(), nullable=True),
        sa.Column("recommended_experiment", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["hypotheses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_critiques_hypothesis_id", "critiques", ["hypothesis_id"])


def downgrade() -> None:
    op.drop_table("critiques")
    op.drop_column("agent_runs", "output_validation_status")
