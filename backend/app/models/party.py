from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class Party(ProvenanceMixin, TimestampMixin, db.Model):
    __tablename__ = "parties"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "source_external_id",
            name="uq_parties_source",
        ),
        db.Index("ix_parties_acronym", "acronym"),
        db.Index("ix_parties_is_demo", "is_demo"),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    acronym: Mapped[str] = mapped_column(db.String(32), nullable=False)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    number: Mapped[int | None] = mapped_column(db.Integer)
    source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source = relationship("DataSource")
    political_terms = relationship("PoliticalTerm", back_populates="party")
    candidacies = relationship("Candidacy", back_populates="party")

    def to_dict(self):
        from app.models.data_source import isoformat

        return {
            "id": self.id,
            "acronym": self.acronym,
            "name": self.name,
            "number": self.number,
            "is_demo": self.is_demo,
            "source": self.source.to_ref() if self.source else None,
            "source_external_id": self.source_external_id,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }
