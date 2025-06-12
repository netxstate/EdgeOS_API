from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base
from app.core.utils import current_time


class WorldBuilder(Base):
    __tablename__ = 'world_builders'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    world_address = Column(String, nullable=False)
    phone = Column(String)
    location = Column(String)
    personal_links = Column(String)
    x_handle = Column(String)
    project_description = Column(String)
    project_stage = Column(String)
    funding_status = Column(String)
    team_description = Column(String)
    tech_stack = Column(String)
    edge_nexus_benefit = Column(String)
    edge_nexus_cohort = Column(String)
    financial_situation = Column(String)
    financial_support_reason = Column(String)
    extra_info = Column(String)
    integration_potential = Column(String)
    send_proposal = Column(Boolean, default=False)
    accepted = Column(String)
    notes = Column(String)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)
