from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class Candidacy(ProvenanceMixin, TimestampMixin, db.Model):
    __tablename__ = "candidacies"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "source_external_id",
            name="uq_candidacies_source",
        ),
        db.Index("ix_candidacies_politician", "politician_id"),
        db.Index("ix_candidacies_party", "party_id"),
        db.Index("ix_candidacies_election_year", "election_year"),
        db.Index("ix_candidacies_office_state", "office", "state"),
        db.Index("ix_candidacies_result", "result"),
        db.Index("ix_candidacies_is_demo", "is_demo"),
        db.CheckConstraint("election_year >= 1890", name="ck_candidacies_year"),
        db.CheckConstraint(
            "votes_received IS NULL OR votes_received >= 0",
            name="ck_candidacies_votes",
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
    election_year: Mapped[int] = mapped_column(db.Integer, nullable=False)
    office: Mapped[str] = mapped_column(db.String(64), nullable=False)
    state: Mapped[str | None] = mapped_column(db.String(2))
    municipality: Mapped[str | None] = mapped_column(db.String(128))
    ballot_name: Mapped[str | None] = mapped_column(db.String(255))
    ballot_number: Mapped[str | None] = mapped_column(db.String(16))
    result: Mapped[str | None] = mapped_column(db.String(32))
    votes_received: Mapped[int | None] = mapped_column(db.Integer)
    source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    politician = relationship("Politician", back_populates="candidacies")
    party = relationship("Party", back_populates="candidacies")
    source = relationship("DataSource")
    campaign_proposals = relationship(
        "CampaignProposal",
        back_populates="candidacy",
        cascade="all, delete-orphan",
    )
    declared_assets = relationship("DeclaredAsset", back_populates="candidacy")

    def to_dict(self, include_proposals=False):
        from app.models.data_source import isoformat

        payload = {
            "id": self.id,
            "politician_id": self.politician_id,
            "politician_name": self.politician.full_name if self.politician else None,
            "party": self.party.to_dict() if self.party else None,
            "election_year": self.election_year,
            "office": self.office,
            "state": self.state,
            "municipality": self.municipality,
            "ballot_name": self.ballot_name,
            "ballot_number": self.ballot_number,
            "result": self.result,
            "votes_received": self.votes_received,
            "is_demo": self.is_demo,
            "source": self.source.to_ref() if self.source else None,
            "source_external_id": self.source_external_id,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }
        if include_proposals:
            payload["campaign_proposals"] = [
                item.to_dict() for item in self.campaign_proposals
            ]
        return payload


class CampaignProposal(ProvenanceMixin, TimestampMixin, db.Model):
    __tablename__ = "campaign_proposals"
    __table_args__ = (
        db.UniqueConstraint(
            "source_id",
            "source_external_id",
            name="uq_campaign_proposals_source",
        ),
        db.Index("ix_campaign_proposals_candidacy", "candidacy_id"),
        db.Index("ix_campaign_proposals_theme", "theme"),
        db.Index("ix_campaign_proposals_is_demo", "is_demo"),
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    candidacy_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("candidacies.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text)
    theme: Mapped[str | None] = mapped_column(db.String(64))
    source_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    candidacy = relationship("Candidacy", back_populates="campaign_proposals")
    source = relationship("DataSource")

    def to_dict(self):
        from app.models.data_source import isoformat

        return {
            "id": self.id,
            "candidacy_id": self.candidacy_id,
            "title": self.title,
            "description": self.description,
            "theme": self.theme,
            "is_demo": self.is_demo,
            "source": self.source.to_ref() if self.source else None,
            "source_external_id": self.source_external_id,
            "created_at": isoformat(self.created_at),
            "updated_at": isoformat(self.updated_at),
        }
