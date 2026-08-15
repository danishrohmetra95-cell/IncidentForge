"""initial

Revision ID: 0001
Revises: 
Create Date: 2026-08-15 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    op.create_table('incidents',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Text(), nullable=False),
        sa.Column('service', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scenario_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('evidence',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('observation', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('strength', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evidence_incident_id', 'evidence', ['incident_id'])

    op.create_table('hypotheses',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.Text(), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('predictions', sa.JSON(), nullable=True),
        sa.Column('alternatives', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_hypotheses_incident_id', 'hypotheses', ['incident_id'])

    op.create_table('hypothesis_evidence',
        sa.Column('hypothesis_id', sa.Text(), nullable=False),
        sa.Column('evidence_id', sa.Text(), nullable=False),
        sa.Column('relationship', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ),
        sa.ForeignKeyConstraint(['hypothesis_id'], ['hypotheses.id'], ),
        sa.PrimaryKeyConstraint('hypothesis_id', 'evidence_id')
    )

    op.create_table('experiments',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.Text(), nullable=False),
        sa.Column('target_hypothesis', sa.Text(), nullable=False),
        sa.Column('intervention', sa.JSON(), nullable=True),
        sa.Column('controls', sa.JSON(), nullable=True),
        sa.Column('baseline', sa.JSON(), nullable=True),
        sa.Column('expected_conditions', sa.JSON(), nullable=True),
        sa.Column('observation_window', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['target_hypothesis'], ['hypotheses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_experiments_incident_id', 'experiments', ['incident_id'])

    op.create_table('experiment_observations',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('experiment_id', sa.Text(), nullable=False),
        sa.Column('baseline', sa.JSON(), nullable=True),
        sa.Column('post_intervention', sa.JSON(), nullable=True),
        sa.Column('duration', sa.Text(), nullable=True),
        sa.Column('raw_snapshots', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('remediations',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.Text(), nullable=False),
        sa.Column('hypothesis_id', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('diff', sa.Text(), nullable=True),
        sa.Column('config_change', sa.JSON(), nullable=True),
        sa.Column('validation_status', sa.Text(), nullable=True),
        sa.Column('validation_detail', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['hypothesis_id'], ['hypotheses.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_remediations_incident_id', 'remediations', ['incident_id'])

    op.create_table('incident_memories',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.Text(), nullable=False),
        sa.Column('fingerprint', sa.JSON(), nullable=True),
        sa.Column('symptoms', sa.JSON(), nullable=True),
        sa.Column('evidence_summary', sa.JSON(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('experiment_summary', sa.Text(), nullable=True),
        sa.Column('verified_intervention', sa.Text(), nullable=True),
        sa.Column('remediation_summary', sa.Text(), nullable=True),
        sa.Column('post_fix_metrics', sa.JSON(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incident_memories_incident_id', 'incident_memories', ['incident_id'])
    op.execute('CREATE INDEX ix_incident_memories_embedding ON incident_memories USING hnsw (embedding vector_l2_ops);')

    op.create_table('agent_runs',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('agent', sa.Text(), nullable=False),
        sa.Column('model', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_runs_incident_id', 'agent_runs', ['incident_id'])

    op.create_table('timeline_events',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.Text(), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_timeline_events_incident_id', 'timeline_events', ['incident_id'])


def downgrade() -> None:
    op.drop_table('timeline_events')
    op.drop_table('agent_runs')
    op.drop_table('incident_memories')
    op.drop_table('remediations')
    op.drop_table('experiment_observations')
    op.drop_table('experiments')
    op.drop_table('hypothesis_evidence')
    op.drop_table('hypotheses')
    op.drop_table('evidence')
    op.drop_table('incidents')
