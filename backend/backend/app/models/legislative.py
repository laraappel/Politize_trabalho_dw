from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class LegislativeProposal(ProvenanceMixin, TimestampMixin, db.Model):
    __tablename__ = "legislative_proposals"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "source_external_id",
            name="uq_legislative_proposals_source",
        ),
        db.Index("ix_legislative_proposals_year_kind", "year", "kind"),
        db.Index("ix_legislative_proposals_house_status", "house", "status"),
        db.Index("ix_legislative_proposals_is_demo", "is_demo"),
        db.CheckConstraint("year >= 1823", name="ck_legislative_proposals_year"),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(db.String(16), nullable=False)
    number: Mapped[int | None] = mapped_column(db.Integer)
    year: Mapped[int] = mapped_column(db.Integer, nullable=False)
    house: Mapped[str | None] = mapped_column(db.String(32))
    title: Mapped[str] = mapped_column(db.String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(db.Text)
    status: Mapped[str | None] = mapped_column(db.String(64))
    presentation_date = mapped_column(db.Date)
    source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source = relationship("DataSource")
    authorships = relationship(
        "ProposalAuthorship",
        back_populates="legislative_proposal",
        cascade="all, delete-orphan",
    )
    votes = relationship(
        "Vote",
        back_populates="legislative_proposal",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_authors=False):
        from app.models.data_source import isoformat

        payload = {
            "id": self.id,
            "kind": self.kind,
            "number": self.number,
            "year": self.year,
            "house": self.house,
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "presentation_date": (
                self.presentation_date.isoformat() if self.presentation_date else None
            ),
            "is_demo": self.is_demo,
            "source": self.source.to_ref() if self.source else None,
            "source_external_id": self.source_external_id,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }
        if include_authors:
            payload["authorships"] = [item.to_dict() for item in self.authorships]
        return payload


class ProposalAuthorship(TimestampMixin, db.Model):
    __tablename__ = "proposal_authorships"
    __table_args__ = (
        db.UniqueConstraint(
            "legislative_proposal_id",
            "politician_id",
            name="uq_proposal_authorships_pair",
        ),
        db.Index("ix_proposal_authorships_politician", "politician_id"),
        db.CheckConstraint(
            "role IN ('autor', 'coautor', 'relator')",
            name="ck_proposal_authorships_role",
        ),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    legislative_proposal_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("legislative_proposals.id", ondelete="CASCADE"),
        nullable=False,
    )
    politician_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("politicians.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(db.String(16), nullable=False, default="autor")

    legislative_proposal = relationship(
        "LegislativeProposal", back_populates="authorships"
    )
    politician = relationship("Politician", back_populates="proposal_authorships")

    def to_dict(self):
        return {
            "id": self.id,
            "legislative_proposal_id": self.legislative_proposal_id,
            "politician_id": self.politician_id,
            "politician_name": self.politician.full_name if self.politician else None,
            "role": self.role,
        }


class Vote(ProvenanceMixin, TimestampMixin, db.Model):
    __tablename__ = "votes"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "source_external_id",
            name="uq_votes_source",
        ),
        db.Index("ix_votes_politician", "politician_id"),
        db.Index("ix_votes_proposal", "legislative_proposal_id"),
        db.Index("ix_votes_session_date", "session_date"),
        db.Index("ix_votes_choice", "vote_choice"),
        db.Index("ix_votes_is_demo", "is_demo"),
        db.CheckConstraint(
            "vote_choice IN ('sim', 'nao', 'abstencao', 'ausente', 'obstrucao')",
            name="ck_votes_choice",
        ),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    legislative_proposal_id: Mapped[int | None] = mapped_column(
        db.Integer,
        db.ForeignKey("legislative_proposals.id", ondelete="SET NULL"),
    )
    politician_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("politicians.id", ondelete="CASCADE"),
        nullable=False,
    )
    political_term_id: Mapped[int | None] = mapped_column(
        db.Integer,
        db.ForeignKey("political_terms.id", ondelete="SET NULL"),
    )
    session_date = mapped_column(db.Date, nullable=False)
    vote_choice: Mapped[str] = mapped_column(db.String(16), nullable=False)
    roll_call_code: Mapped[str | None] = mapped_column(db.String(64))
    source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    legislative_proposal = relationship("LegislativeProposal", back_populates="votes")
    politician = relationship("Politician", back_populates="votes")
    political_term = relationship("PoliticalTerm")
    source = relationship("DataSource")

    def to_dict(self):
        from app.models.data_source import isoformat

        return {
            "id": self.id,
            "legislative_proposal_id": self.legislative_proposal_id,
            "legislative_proposal_title": (
                self.legislative_proposal.title if self.legislative_proposal else None
            ),
            "politician_id": self.politician_id,
            "politician_name": self.politician.full_name if self.politician else None,
            "political_term_id": self.political_term_id,
            "session_date": self.session_date.isoformat() if self.session_date else None,
            "vote_choice": self.vote_choice,
            "roll_call_code": self.roll_call_code,
            "is_demo": self.is_demo,
            "source": self.source.to_ref() if self.source else None,
            "source_external_id": self.source_external_id,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }
