"""
job.py — SQLAlchemy model for scraped Upwork jobs.
All columns match the scraper's output attributes exactly.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, Integer
from database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    # ── PitchCraft internal fields ────────────────────────────────────────────
    id         = Column(String, primary_key=True, default=_new_uuid, index=True)
    user_id    = Column(String, nullable=False, index=True)
    status     = Column(String, nullable=False, default="pending")   # "pending" or "applied"
    scraped_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Scraper output fields (match CSV columns exactly) ─────────────────────
    job_id                              = Column(String, unique=True, index=True, nullable=True)  # de-dup key
    title                               = Column(String, nullable=True)
    description                         = Column(Text,   nullable=True)
    url                                 = Column(String, nullable=True)
    client_country                      = Column(String, nullable=True)
    buyer_location_city                 = Column(String, nullable=True)
    buyer_location_localTime            = Column(String, nullable=True)
    buyer_hire_rate_pct                 = Column(Float,  nullable=True)
    client_total_spent                  = Column(Float,  nullable=True)
    client_hires                        = Column(Integer,nullable=True)
    buyer_avgHourlyJobsRate_amount      = Column(Float,  nullable=True)
    buyer_stats_hoursCount              = Column(Float,  nullable=True)
    buyer_company_contractDate          = Column(String, nullable=True)
    payment_verified                    = Column(Boolean,nullable=True)
    skills                              = Column(Text,   nullable=True)
    type                                = Column(String, nullable=True)   # "Fixed" / "Hourly"
    premium                             = Column(Boolean,nullable=True)
    enterpriseJob                       = Column(Boolean,nullable=True)
    fixed_budget_amount                 = Column(String, nullable=True)
    duration                            = Column(String, nullable=True)
    level                               = Column(String, nullable=True)
    ts_create                           = Column(String, nullable=True)
    ts_publish                          = Column(String, nullable=True)
    applicants                          = Column(Integer,nullable=True)
    numberOfPositionsToHire             = Column(Integer,nullable=True)
    connects_required                   = Column(Integer,nullable=True)
    client_rating                       = Column(Float,  nullable=True)
    client_reviews                      = Column(Integer,nullable=True)
    buyer_stats_activeAssignmentsCount  = Column(Integer,nullable=True)
    buyer_stats_totalJobsWithHires      = Column(Integer,nullable=True)
    clientActivity_invitationsSent      = Column(Integer,nullable=True)
    clientActivity_totalHired           = Column(Integer,nullable=True)
    clientActivity_totalInvitedToInterview = Column(Integer, nullable=True)
    clientActivity_unansweredInvites    = Column(Integer,nullable=True)
    buyer_jobs_openCount                = Column(Integer,nullable=True)
    buyer_jobs_postedCount              = Column(Integer,nullable=True)
    category_name                       = Column(String, nullable=True)
    buyer_location_offsetFromUtcMillis  = Column(Float,  nullable=True)
    client_industry                     = Column(String, nullable=True)
    phone_verified                      = Column(Boolean,nullable=True)
    isContractToHire                    = Column(Boolean,nullable=True)
    lastBuyerActivity                   = Column(String, nullable=True)
    contractorTier                      = Column(Integer,nullable=True)
    buyer_location_countryTimezone      = Column(String, nullable=True)
    client_company_size                 = Column(String, nullable=True)
    currency                            = Column(String, nullable=True)
    category                            = Column(String, nullable=True)
    category_urlSlug                    = Column(String, nullable=True)
    categoryGroup_name                  = Column(String, nullable=True)
    categoryGroup_urlSlug               = Column(String, nullable=True)
    hourly_max                          = Column(Float,  nullable=True)
    hourly_min                          = Column(Float,  nullable=True)
    qualifications                      = Column(Text,   nullable=True)
    questions                           = Column(Text,   nullable=True)
