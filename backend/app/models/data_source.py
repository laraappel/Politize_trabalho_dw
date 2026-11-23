from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class DataSource(TimestampMixin, db.Model):
    __tablename__ = "data_sources"
    __table_args__ = (
        db.Index("ix_data_sources_is_official", "is_official"),
        db.Index("ix_data_sources_is_demo", "is_demo"),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    code: Mapped[str] = mapped_column(db.String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(db.String(500))
    description: Mapped[str | None] = mapped_column(db.Text)
    is_official: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text("false"),
    )
    is_demo: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text("false"),
    )

    sync_logs = relationship("DataSourceSyncLog", back_populates="data_source")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "is_official": self.is_official,
            "is_demo": self.is_demo,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }

    def to_ref(self):
        return {"id": self.id, "code": self.code, "name": self.name}


class DataSourceSyncLog(db.Model):
    __tablename__ = "data_source_sync_logs"
    __table_args__ = (
        db.Index("ix_data_source_sync_logs_source_started", "data_source_id", "started_at"),
        db.Index("ix_data_source_sync_logs_status", "status"),
        db.CheckConstraint(
            "status IN ('running', 'success', 'failed')",
            name="ck_data_source_sync_logs_status",
        ),
        db.CheckConstraint(
            "records_read >= 0 AND records_upserted >= 0 AND records_failed >= 0",
            name="ck_data_source_sync_logs_counts",
        ),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    data_source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entity_name: Mapped[str] = mapped_column(db.String(64), nullable=False)
    started_at: Mapped[object] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[object | None] = mapped_column(db.DateTime(timezone=True))
    status: Mapped[str] = mapped_column(db.String(16), nullable=False)
    records_read: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    records_upserted: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    records_failed: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    message: Mapped[str | None] = mapped_column(db.Text)

    data_source = relationship("DataSource", back_populates="sync_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "data_source": self.data_source.to_ref() if self.data_source else None,
            "entity_name": self.entity_name,
            "started_at": isoformat(self.started_at),
            "finished_at": isoformat(self.finished_at),
            "status": self.status,
            "records_read": self.records_read,
            "records_upserted": self.records_upserted,
            "records_failed": self.records_failed,
            "message": self.message,
        }


def isoformat(value):
    if value is None:
        return None
    return value.isoformat()