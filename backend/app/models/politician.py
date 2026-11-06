from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class Politician(ProvenanceMixin, TimestampMixin, db.Model):
    __tablename__ = "politicians"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "source_external_id",
            name="uq_politicians_source",
        ),
        db.Index("ix_politicians_full_name", "full_name"),
        db.Index("ix_politicians_is_demo", "is_demo"),
        db.Index("ix_politicians_birth_state", "birth_state"),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    civil_name: Mapped[str | None] = mapped_column(db.String(255))
    birth_date = mapped_column(db.Date)
    birth_state: Mapped[str | None] = mapped_column(db.String(2))
    gender: Mapped[str | None] = mapped_column(db.String(16))
    photo_url: Mapped[str | None] = mapped_column(db.String(500))
    biography: Mapped[str | None] = mapped_column(db.Text)
    source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source = relationship("DataSource")
    political_terms = relationship(
        "PoliticalTerm",
        back_populates="politician",
        cascade="all, delete-orphan",
    )
    candidacies = relationship(
        "Candidacy",
        back_populates="politician",
        cascade="all, delete-orphan",
    )
    proposal_authorships = relationship(
        "ProposalAuthorship",
        back_populates="politician",
        cascade="all, delete-orphan",
    )
    votes = relationship(
        "Vote",
        back_populates="politician",
        cascade="all, delete-orphan",
    )
    public_compensations = relationship(
        "PublicCompensation",
        back_populates="politician",
        cascade="all, delete-orphan",
    )
    public_expenses = relationship(
        "PublicExpense",
        back_populates="politician",
        cascade="all, delete-orphan",
    )
    declared_assets = relationship(
        "DeclaredAsset",
        back_populates="politician",
        cascade="all, delete-orphan",
    )
    news_links = relationship(
        "NewsPoliticianLink",
        back_populates="politician",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_relations=False):
        from app.models.data_source import isoformat

        payload = {
            "id": self.id,
            "full_name": self.full_name,
            "civil_name": self.civil_name,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "birth_state": self.birth_state,
            "gender": self.gender,
            "photo_url": self.photo_url,
            "biography": self.biography,
            "is_demo": self.is_demo,
            "source": self.source.to_ref() if self.source else None,
            "source_external_id": self.source_external_id,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }
        if include_relations:
            payload["political_terms"] = [
                term.to_dict() for term in self.political_terms
            ]
            payload["candidacies"] = [
                candidacy.to_dict() for candidacy in self.candidacies
            ]
        return payload
