"""init

Revision ID: 78db1f820ded
Revises:
Create Date: 2019-02-14 10:14:38.289690

"""

# revision identifiers, used by Alembic.
revision = "aaaaaaaaaaaa"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op

    op.create_table(
        "upgraded",
    )


def downgrade() -> None:
    from alembic import op

    op.drop_table("upgraded")
