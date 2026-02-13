from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision = 'add_vector_column'
# down_revision = 'previous_revision_id' (handle manually or auto-detect)
# ... standard headers ...

def upgrade() -> None:
    # Enable vector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Add embedding column
    op.add_column('skills', sa.Column('embedding', Vector(384), nullable=True))
    
    # Create index (HNSW for speed)
    op.create_index('ix_skills_embedding', 'skills', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_l2_ops'})


def downgrade() -> None:
    op.drop_index('ix_skills_embedding', table_name='skills', postgresql_using='hnsw')
    op.drop_column('skills', 'embedding')
    # op.execute("DROP EXTENSION vector") # Optional, usually safe to keep
