"""Remove placeholder laboratory records.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE laboratories "
            "SET is_active = false, verification_status = 'rejected' "
            "WHERE name IN ('HomeCare Verified Lab Demo', 'Metro Diagnostics Demo')"
        )
    )


def downgrade() -> None:
    pass
