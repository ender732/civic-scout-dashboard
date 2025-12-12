"""
Pydantic Data Models for NYC Civic Scout

These models define the structured output schema for the entire pipeline,
ensuring type safety and consistent API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class EventTopic(str, Enum):
    """Enumeration of civic event topics for classification."""
    LEGISLATION_POLICY = "Legislation/Policy"
    ZONING_HOUSING = "Zoning/Housing"
    BUDGET_FINANCE = "Budget/Finance"
    EDUCATION = "Education"
    TRANSPORTATION = "Transportation"
    PUBLIC_SAFETY = "Public Safety"
    HEALTH_SOCIAL_SERVICES = "Health/Social Services"
    ENVIRONMENT = "Environment"
    OTHER = "Other"


class GeminiAnalysisOutput(BaseModel):
    """
    Schema for Gemini's structured output response.
    Used to enforce JSON schema in the Gemini API call.
    """
    event_id: str = Field(description="The unique identifier of the event")
    impact_score: int = Field(
        ge=1, le=5,
        description="Impact score from 1-5, where 5 is 'Critical, immediate action required'"
    )
    community_impact_summary: str = Field(
        description="A 2-sentence non-technical summary explaining why a resident should care"
    )
    topic: str = Field(
        description="The classified topic category of the event"
    )


class CivicEvent(BaseModel):
    """
    The primary output model for a processed civic event.
    This dictates the structured output of the entire pipeline.
    """
    id: str = Field(description="Unique identifier for the event")
    title: str = Field(description="The title/subject of the event")
    date_time: str = Field(description="ISO 8601 formatted date and time of the event")
    location: str = Field(description="Physical location/address of the event")
    link: str = Field(description="URL to the official event page or agenda")
    topic: str = Field(
        default="Other",
        description="Classified topic (e.g., 'Legislation/Policy', 'Education')"
    )
    impact_score: int = Field(
        default=1,
        ge=1, le=5,
        description="Impact score from 1-5, where 5 is 'Critical, immediate action required'"
    )
    community_impact_summary: str = Field(
        default="",
        description="A 2-sentence non-technical summary from Gemini analysis"
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude coordinate from geocoding"
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude coordinate from geocoding"
    )
    borough: Optional[str] = Field(
        default=None,
        description="NYC Borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island)"
    )


class LegistarEvent(BaseModel):
    """
    Raw event data structure from the Legistar API.
    Used for parsing incoming API responses.
    """
    EventId: int
    EventGuid: Optional[str] = None
    EventLastModifiedUtc: Optional[str] = None
    EventRowVersion: Optional[str] = None
    EventBodyId: Optional[int] = None
    EventBodyName: Optional[str] = None
    EventDate: str
    EventTime: Optional[str] = None
    EventVideoStatus: Optional[str] = None
    EventAgendaStatusId: Optional[int] = None
    EventAgendaStatusName: Optional[str] = None
    EventMinutesStatusId: Optional[int] = None
    EventMinutesStatusName: Optional[str] = None
    EventLocation: Optional[str] = None
    EventAgendaFile: Optional[str] = None
    EventMinutesFile: Optional[str] = None
    EventAgendaLastPublishedUTC: Optional[str] = None
    EventMinutesLastPublishedUTC: Optional[str] = None
    EventComment: Optional[str] = None
    EventVideoPath: Optional[str] = None
    EventInSiteURL: Optional[str] = None
    EventItems: Optional[List[dict]] = None


class EventsResponse(BaseModel):
    """API response model for the /api/events endpoint."""
    events: List[CivicEvent]
    count: int
    source: str = Field(default="legistar", description="Data source identifier")
    generated_at: str = Field(description="Timestamp when the response was generated")


class HealthResponse(BaseModel):
    """API response model for the /health endpoint."""
    status: str
    version: str
    services: dict
