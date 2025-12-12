"""
NYC Civic Scout Agent - FastAPI Backend

This is the main orchestrator that coordinates the agentic pipeline:
1. Fetch events from Legistar API (Discovery Agent)
2. Analyze each event with Gemini AI (Analyst Agent)
3. Geocode event locations (Geolocation Tool)
4. Return structured CivicEvent data

Endpoints:
- GET /api/events - Fetch and process civic events
- GET /health - Health check endpoint
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import CivicEvent, EventsResponse, HealthResponse
from civic_tools import (
    get_legistar_events,
    geocode_address,
    analyze_event_with_gemini,
    analyze_pdf_agenda,
    transform_legistar_to_civic_event,
    CIVIC_KEYWORDS
)

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Application Configuration
# =============================================================================

APP_VERSION = "1.0.0"
APP_TITLE = "NYC Civic Scout Agent API"
APP_DESCRIPTION = """
The NYC Civic Scout Agent API provides processed civic event data with AI-powered
impact analysis. It aggregates events from official NYC government sources,
analyzes their community impact using Google Gemini, and enriches them with
geolocation data.

## Features
- **Discovery Agent**: Fetches events from NYC Legistar API
- **Analyst Agent**: AI-powered impact analysis using Gemini
- **Geolocation Tool**: Google Maps geocoding for event locations
- **Structured Output**: Pydantic-validated response models

## Authentication
API keys are required for full functionality:
- `GEMINI_API_KEY` - Google Gemini AI
- `LEGISTAR_API_TOKEN` - NYC Legistar API
- `GOOGLE_MAPS_API_KEY` - Google Maps Geocoding
"""

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")
    
    # Validate environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    legistar_token = os.getenv("LEGISTAR_API_TOKEN")
    
    if not gemini_key:
        logger.warning("GEMINI_API_KEY not set - AI analysis will use fallback mode")
    if not maps_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set - geocoding will be disabled")
    if not legistar_token:
        logger.warning("LEGISTAR_API_TOKEN not set - API rate limits may apply")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NYC Civic Scout Agent")

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access - allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# The Agentic Orchestrator Pipeline
# =============================================================================

async def run_civic_scout_pipeline(
    days_ahead: int = 30,
    filter_keywords: bool = True,
    include_pdf_analysis: bool = False
) -> List[CivicEvent]:
    """
    AGENTIC ORCHESTRATOR: Coordinate the full civic event processing pipeline.
    
    This function orchestrates multiple agents/tools:
    1. Discovery Agent (get_legistar_events) - Fetch raw event data
    2. Analyst Agent (analyze_event_with_gemini) - AI impact analysis
    3. Geolocation Tool (geocode_address) - Add coordinates
    4. Optional: PDF Tool (analyze_pdf_agenda) - Extract agenda details
    
    Args:
        days_ahead: Number of days to look ahead for events
        filter_keywords: Whether to filter events by civic keywords
        include_pdf_analysis: Whether to download and analyze PDF agendas
    
    Returns:
        List of fully processed CivicEvent objects
    """
    logger.info(f"Starting Civic Scout pipeline: {days_ahead} days ahead, filter={filter_keywords}")
    
    # Step 1: DISCOVERY - Fetch raw events from Legistar
    try:
        raw_events = get_legistar_events(
            days_ahead=days_ahead,
            filter_keywords=filter_keywords
        )
    except Exception as e:
        logger.error(f"Discovery agent failed: {e}")
        raw_events = []
    
    if not raw_events:
        logger.warning("No events retrieved from Legistar, using sample data")
        raw_events = _get_sample_events()
    
    logger.info(f"Processing {len(raw_events)} events through analysis pipeline")
    
    # Step 2-4: Process each event through analysis and geocoding
    processed_events: List[CivicEvent] = []
    
    for i, raw_event in enumerate(raw_events):
        event_id = str(raw_event.get("EventId", i))
        logger.debug(f"Processing event {event_id} ({i+1}/{len(raw_events)})")
        
        try:
            # Extract event details for analysis
            title = raw_event.get("EventBodyName", "City Council Meeting")
            body = raw_event.get("EventBodyName", "")
            date = raw_event.get("EventDate", "")
            location = raw_event.get("EventLocation", "City Hall, New York, NY")
            
            # Optional: Analyze PDF agenda for additional context
            context = ""
            if include_pdf_analysis:
                agenda_url = raw_event.get("EventAgendaFile")
                if agenda_url:
                    context = await analyze_pdf_agenda(agenda_url, event_id) or ""
            
            # Step 2: ANALYST AGENT - AI analysis
            analysis = analyze_event_with_gemini(
                event_id=event_id,
                title=title,
                body=body,
                date=date,
                location=location,
                context=context
            )
            
            # Step 3: GEOLOCATION - Geocode the address
            coordinates = geocode_address(location)
            
            # Step 4: TRANSFORM - Create final CivicEvent
            civic_event = transform_legistar_to_civic_event(
                raw_event=raw_event,
                analysis=analysis,
                coordinates=coordinates
            )
            
            processed_events.append(civic_event)
            
        except Exception as e:
            logger.error(f"Failed to process event {event_id}: {e}")
            continue
    
    logger.info(f"Pipeline complete: {len(processed_events)} events processed")
    return processed_events


def _get_sample_events() -> List[dict]:
    """
    Fallback sample events when Legistar API is unavailable.
    These represent typical NYC civic events for demonstration.
    """
    base_date = datetime.now()
    
    return [
        {
            "EventId": 10001,
            "EventBodyName": "Committee on Housing and Buildings - Zoning Amendment Hearing",
            "EventDate": (base_date.replace(day=base_date.day + 3)).isoformat(),
            "EventTime": "10:00 AM",
            "EventLocation": "City Hall, Committee Room, New York, NY 10007",
            "EventInSiteURL": "https://legistar.council.nyc.gov/Calendar.aspx",
            "EventAgendaFile": None,
            "EventComment": "Public hearing on proposed zoning changes in Brooklyn"
        },
        {
            "EventId": 10002,
            "EventBodyName": "Committee on Education - School Budget Review",
            "EventDate": (base_date.replace(day=base_date.day + 5)).isoformat(),
            "EventTime": "2:00 PM",
            "EventLocation": "250 Broadway, 14th Floor, New York, NY 10007",
            "EventInSiteURL": "https://legistar.council.nyc.gov/Calendar.aspx",
            "EventAgendaFile": None,
            "EventComment": "Review of proposed budget cuts to after-school programs"
        },
        {
            "EventId": 10003,
            "EventBodyName": "Committee on Transportation - Transit Access Hearing",
            "EventDate": (base_date.replace(day=base_date.day + 7)).isoformat(),
            "EventTime": "11:00 AM",
            "EventLocation": "City Hall, Council Chambers, New York, NY 10007",
            "EventInSiteURL": "https://legistar.council.nyc.gov/Calendar.aspx",
            "EventAgendaFile": None,
            "EventComment": "Discussion on improving transit access in underserved areas"
        },
        {
            "EventId": 10004,
            "EventBodyName": "Committee on Public Safety - Community Policing Review",
            "EventDate": (base_date.replace(day=base_date.day + 8)).isoformat(),
            "EventTime": "3:00 PM",
            "EventLocation": "Bronx Borough Hall, 851 Grand Concourse, Bronx, NY 10451",
            "EventInSiteURL": "https://legistar.council.nyc.gov/Calendar.aspx",
            "EventAgendaFile": None,
            "EventComment": "Review of community policing initiatives"
        },
        {
            "EventId": 10005,
            "EventBodyName": "Committee on Finance - Budget Appropriations Hearing",
            "EventDate": (base_date.replace(day=base_date.day + 10)).isoformat(),
            "EventTime": "10:00 AM",
            "EventLocation": "City Hall, Council Chambers, New York, NY 10007",
            "EventInSiteURL": "https://legistar.council.nyc.gov/Calendar.aspx",
            "EventAgendaFile": None,
            "EventComment": "Final hearing on FY2026 budget appropriations"
        },
        {
            "EventId": 10006,
            "EventBodyName": "Committee on Land Use - Affordable Housing Development",
            "EventDate": (base_date.replace(day=base_date.day + 12)).isoformat(),
            "EventTime": "1:00 PM",
            "EventLocation": "Queens Borough Hall, 120-55 Queens Blvd, Kew Gardens, NY 11424",
            "EventInSiteURL": "https://legistar.council.nyc.gov/Calendar.aspx",
            "EventAgendaFile": None,
            "EventComment": "Review of proposed affordable housing development in Queens"
        }
    ]


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/events", response_model=EventsResponse, tags=["Events"])
async def get_events(
    days_ahead: int = Query(
        default=30,
        ge=1,
        le=90,
        description="Number of days ahead to search for events"
    ),
    filter_keywords: bool = Query(
        default=True,
        description="Filter events by civic keywords"
    ),
    include_pdf: bool = Query(
        default=False,
        description="Include PDF agenda analysis (slower)"
    )
) -> EventsResponse:
    """
    Fetch and process NYC civic events.
    
    This endpoint runs the full agentic pipeline:
    1. Fetches events from NYC Legistar API
    2. Analyzes each event with Gemini AI for impact assessment
    3. Geocodes event locations
    4. Returns structured CivicEvent data
    
    **Parameters:**
    - `days_ahead`: How many days ahead to look for events (1-90)
    - `filter_keywords`: Filter events by civic keywords like 'Zoning', 'Budget', etc.
    - `include_pdf`: Enable PDF agenda analysis (adds latency)
    
    **Returns:**
    - List of processed civic events with AI-generated impact summaries
    """
    try:
        events = await run_civic_scout_pipeline(
            days_ahead=days_ahead,
            filter_keywords=filter_keywords,
            include_pdf_analysis=include_pdf
        )
        
        return EventsResponse(
            events=events,
            count=len(events),
            source="legistar",
            generated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process events: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring.
    
    Returns the status of the API and connected services.
    """
    # Check service availability
    services = {
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
        "legistar": True  # Public API, always "available"
    }
    
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        services=services
    )


@app.get("/api/topics", tags=["Reference"])
async def get_topics() -> dict:
    """Get the list of available topic categories."""
    return {
        "topics": [
            "Legislation/Policy",
            "Zoning/Housing",
            "Budget/Finance",
            "Education",
            "Transportation",
            "Public Safety",
            "Health/Social Services",
            "Environment",
            "Other"
        ]
    }


@app.get("/api/keywords", tags=["Reference"])
async def get_keywords() -> dict:
    """Get the list of civic keywords used for filtering."""
    return {"keywords": CIVIC_KEYWORDS}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8001))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
