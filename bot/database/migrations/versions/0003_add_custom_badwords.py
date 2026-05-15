"""add custom_badwords table with seed

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-15
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_SEED_WORDS = [
    # Spanish
    "mierda", "puta", "puto", "coño", "joder", "hostia", "cabron",
    "gilipollas", "imbecil", "estupido", "idiota", "pendejo", "verga",
    "polla", "culero", "maricon", "hijodeputa",
    # Italian
    "cazzo", "stronzo", "merda", "coglione", "vaffanculo", "minchia",
    "porco", "bastardo", "imbecille", "deficiente", "troia", "fanculo",
    # English
    "fuck", "shit", "asshole", "bitch", "cunt", "bastard", "dick",
    "pussy", "motherfucker", "cock", "whore", "prick", "twat",
    "bollocks", "wanker", "shithead", "arsehole",
]


def upgrade() -> None:
    op.create_table(
        "custom_badwords",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("word", sa.String(128), nullable=False),
        sa.Column("added_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word"),
    )
    op.create_index("ix_custom_badwords_word", "custom_badwords", ["word"])

    for word in _SEED_WORDS:
        op.execute(
            sa.text("INSERT INTO custom_badwords (word, added_by) VALUES (:word, NULL)").bindparams(word=word)
        )


def downgrade() -> None:
    op.drop_index("ix_custom_badwords_word", table_name="custom_badwords")
    op.drop_table("custom_badwords")
