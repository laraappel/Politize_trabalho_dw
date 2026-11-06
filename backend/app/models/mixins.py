from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class TimestampMixin:
    created_at: Mapped[object] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[object] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ProvenanceMixin:
    """Identificadores da fonte original para upsert e deduplicacao."""

    source_external_id: Mapped[str] = mapped_column(db.String(128), nullable=False)
    is_demo: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text("false"),
    )
