from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class PoliticalTerm(ProvenanceMixin, TimestampMixin, db.Model):
    __tablename__ = "political_terms"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "source_external_id",
            name="uq_political_terms_source",
        ),
        db.Index("ix_political_terms_politician", "politician_id"),
        db.Index("ix_political_terms_party", "party_id"),
        db.Index("ix_political_terms_office_state", "office", "state"),
        db.Index("ix_political_terms_status", "status"),
        db.Index("ix_political_terms_is_demo", "is_demo"),
        db.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_political_terms_dates",
        ),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    politician_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("politicians.id", ondelete="CASCADE"),
        nullable=False,
    )
    party_id: Mapped[int | None] = mapped_column(
        db.Integer,
        db.ForeignKey("parties.id", ondelete="RESTRICT"),
    )
    office: Mapped[str] = mapped_column(db.String(64), nullable=False)
    house: Mapped[str | None] = mapped_column(db.String(32))
    state: Mapped[str | None] = mapped_column(db.String(2))
    municipality: Mapped[str | None] = mapped_column(db.String(128))
    legislature: Mapped[str | None] = mapped_column(db.String(32))
    start_date = mapped_column(db.Date)
    end_date = mapped_column(db.Date)
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="ativo")
    source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    politician = relationship("Politician", back_populates="political_terms")
    party = relationship("Party", back_populates="political_terms")
    source = relationship("DataSource")

    def to_dict(self):
        from app.models.data_source import isoformat

        return {
            "id": self.id,
            "politician_id": self.politician_id,
            "party": self.party.to_dict() if self.party else None,
            "office": self.office,
            "house": self.house,
            "state": self.state,
            "municipality": self.municipality,
            "legislature": self.legislature,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "is_demo": self.is_demo,
            "source": self.source.to_ref() if self.source else None,
            "source_external_id": self.source_external_id,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }
