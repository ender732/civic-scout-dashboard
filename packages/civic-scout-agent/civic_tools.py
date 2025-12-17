"""
Core Function Tools for NYC Civic Scout Agent

These tools represent the agent's available actions:
1. get_legistar_events - DISCOVERY AGENT: Fetch events from NYC Legistar API
2. geocode_address - GEOLOCATION TOOL: Convert addresses to coordinates
3. analyze_event_with_gemini - ANALYST AGENT: AI analysis of event impact
4. analyze_pdf_agenda - PDF READING TOOL: Extract and analyze PDF agendas
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

import requests
import httpx
import googlemaps
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from models import LegistarEvent, GeminiAnalysisOutput, CivicEvent
from AsyncClient import CivicAsyncClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration and Constants
# =============================================================================

LEGISTAR_BASE_URL = "https://webapi.legistar.com/v1/nyc"
LEGISTAR_EVENTS_ENDPOINT = f"{LEGISTAR_BASE_URL}/Events"

# Keywords for filtering relevant civic events
CIVIC_KEYWORDS = [
    'Zoning', 'Budget', 'Housing', 'Education', 'Transportation',
    'Public Safety', 'Health', 'Environment', 'Social Services',
    'Community', 'Development', 'Land Use', 'Planning', 'Hearing',
    'Resolution', 'Appropriation', 'Tax', 'School', 'Police',
    'Sanitation', 'Parks', 'Affordable'
]

# =============================================================================
# Analyst Agent System Prompt
# =============================================================================

SYSTEM_INSTRUCTION = """You are the 'Civic Scout Analyst Agent,' an unbiased, expert-level community advocate for underserved New York City neighborhoods. Your sole function is to process raw government meeting and event data, analyze its direct human impact, and generate a concise, actionable summary for public awareness. Output strictly in the requested JSON format."""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following NYC government event and provide a structured assessment:

EVENT DATA:
- Event ID: {event_id}
- Title/Subject: {title}
- Body/Committee: {body}
- Date: {date}
- Location: {location}
- Additional Context: {context}

INSTRUCTIONS - Perform multi-step reasoning:

1. CONTEXTUAL ANALYSIS (THOUGHT STEP):
   - Identify the core subject matter of this event
   - Determine if it typically impacts underserved communities (housing, budget cuts, services, zoning changes)
   - Consider which NYC neighborhoods/demographics would be most affected

2. IMPACT DETERMINATION:
   - Assign an impact_score from 1 to 5:
     * 1 = Routine administrative matter, minimal public impact
     * 2 = Minor impact, affects specific groups
     * 3 = Moderate impact, notable community interest
     * 4 = Significant impact, affects many residents
     * 5 = Critical, immediate action required, major policy/budget decision

3. PLAIN LANGUAGE TRANSLATION:
   - Create a community_impact_summary (MAXIMUM TWO SENTENCES)
   - Explain in simple, non-technical language why a resident should care
   - Focus on concrete effects: rent, schools, safety, services, taxes
   - If relevant, mention which communities are most affected

4. TOPIC CLASSIFICATION:
   - Classify into one of these topics: "Legislation/Policy", "Zoning/Housing", "Budget/Finance", "Education", "Transportation", "Public Safety", "Health/Social Services", "Environment", "Other"

Respond with a JSON object containing:
- event_id: "{event_id}"
- impact_score: (integer 1-5)
- community_impact_summary: (your 2-sentence summary)
- topic: (one of the topic categories)
"""

# =============================================================================
# Tool 1: DISCOVERY AGENT - Legistar Events Fetcher
# =============================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
)
def get_legistar_events(days_ahead: int = 30, filter_keywords: bool = True) -> List[Dict[str, Any]]:
    """
    DISCOVERY AGENT: Fetch current/future City Council Events from NYC Legistar API.
    
    Args:
        days_ahead: Number of days ahead to search for events (default: 30)
        filter_keywords: Whether to filter by civic keywords (default: True)
    
    Returns:
        List of raw event dictionaries from Legistar API
    
    Raises:
        requests.exceptions.RequestException: If API call fails after retries
    """
    api_token = os.getenv("LEGISTAR_API_TOKEN", "")
    
    # Calculate date range
    today = datetime.now()
    future_date = today + timedelta(days=days_ahead)
    
    # Format dates for OData filter
    today_str = today.strftime("%Y-%m-%dT00:00:00")
    future_str = future_date.strftime("%Y-%m-%dT23:59:59")
    
    # Build OData filter query
    odata_filter = f"EventDate ge datetime'{today_str}' and EventDate le datetime'{future_str}'"
    
    params = {
        "$filter": odata_filter,
        "$orderby": "EventDate asc",
        "$top": 100  # Limit results
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    
    logger.info(f"Fetching Legistar events from {today_str} to {future_str}")
    
    try:
        response = requests.get(
            LEGISTAR_EVENTS_ENDPOINT,
            params=params,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        events = response.json()
        logger.info(f"Retrieved {len(events)} raw events from Legistar")
        
        # Filter by keywords if enabled
        if filter_keywords and events:
            filtered_events = []
            for event in events:
                event_text = " ".join([
                    str(event.get("EventBodyName", "")),
                    str(event.get("EventComment", "")),
                    str(event.get("EventLocation", ""))
                ]).lower()
                
                if any(keyword.lower() in event_text for keyword in CIVIC_KEYWORDS):
                    filtered_events.append(event)
            
            logger.info(f"Filtered to {len(filtered_events)} relevant civic events")
            return filtered_events
        
        return events
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning("Legistar API endpoint not found, returning empty list")
            return []
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Legistar events: {e}")
        raise


# =============================================================================
# Tool 2: GEOLOCATION TOOL - Google Maps Geocoding
# =============================================================================

def get_borough_from_coordinates(lat: float, lng: float) -> Optional[str]:
    """
    Determine NYC borough from latitude/longitude coordinates.
    Uses approximate bounding boxes for each borough.
    
    Returns:
        Borough name or None if outside NYC
    """
    # Approximate bounding boxes for NYC boroughs
    # These are rough estimates and may have edge case inaccuracies
    boroughs = {
        "Manhattan": {"lat_min": 40.700, "lat_max": 40.882, "lng_min": -74.020, "lng_max": -73.907},
        "Brooklyn": {"lat_min": 40.570, "lat_max": 40.739, "lng_min": -74.042, "lng_max": -73.833},
        "Queens": {"lat_min": 40.541, "lat_max": 40.812, "lng_min": -73.962, "lng_max": -73.700},
        "Bronx": {"lat_min": 40.785, "lat_max": 40.917, "lng_min": -73.933, "lng_max": -73.765},
        "Staten Island": {"lat_min": 40.496, "lat_max": 40.651, "lng_min": -74.259, "lng_max": -74.052},
    }
    
    for borough, bounds in boroughs.items():
        if (bounds["lat_min"] <= lat <= bounds["lat_max"] and
            bounds["lng_min"] <= lng <= bounds["lng_max"]):
            return borough
    
    # Default to Manhattan for City Hall area addresses
    if 40.71 <= lat <= 40.72 and -74.01 <= lng <= -74.00:
        return "Manhattan"
    
    return None


def get_borough_from_address(address: str) -> Optional[str]:
    """
    Try to extract borough from address string.
    """
    address_lower = address.lower()
    
    # Check for explicit borough mentions
    if "manhattan" in address_lower or "new york, ny 100" in address_lower:
        return "Manhattan"
    if "brooklyn" in address_lower or "new york, ny 112" in address_lower:
        return "Brooklyn"
    if "queens" in address_lower or "new york, ny 11" in address_lower:
        return "Queens"
    if "bronx" in address_lower or "new york, ny 104" in address_lower:
        return "Bronx"
    if "staten island" in address_lower or "new york, ny 103" in address_lower:
        return "Staten Island"
    
    # City Hall and 250 Broadway are in Manhattan
    if "city hall" in address_lower or "250 broadway" in address_lower:
        return "Manhattan"
    
    return None


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    GEOLOCATION TOOL: Convert an address string to latitude/longitude coordinates.
    
    Uses Google Maps Geocoding API with proper error handling for:
    - Missing API key
    - Vague or invalid addresses
    - API errors
    
    Args:
        address: The address string to geocode
    
    Returns:
        Tuple of (latitude, longitude, borough) or (None, None, None) if geocoding fails
    """
    if not address or not address.strip():
        logger.warning("Empty address provided for geocoding")
        return (None, None, None)
    
    # Try to get borough from address text first
    borough_from_text = get_borough_from_address(address)
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set, skipping geocoding")
        return (None, None, borough_from_text)
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        # Append NYC to improve geocoding accuracy
        full_address = f"{address}, New York City, NY" if "new york" not in address.lower() else address
        
        geocode_result = gmaps.geocode(full_address)
        
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            logger.debug(f"Geocoded '{address}' to ({lat}, {lng})")
            
            # Determine borough from coordinates or fall back to address text
            borough = get_borough_from_coordinates(lat, lng) or borough_from_text
            
            return (lat, lng, borough)
        else:
            logger.warning(f"No geocoding results for address: {address}")
            return (None, None, borough_from_text)
            
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Google Maps API error: {e}")
        return (None, None, borough_from_text)
    except Exception as e:
        logger.error(f"Unexpected geocoding error: {e}")
        return (None, None, borough_from_text)


# =============================================================================
# Tool 3: ANALYST AGENT - Gemini Event Analysis
# =============================================================================

def analyze_event_with_gemini(
    event_id: str,
    title: str,
    body: str,
    date: str,
    location: str,
    context: str = ""
) -> GeminiAnalysisOutput:
    """
    ANALYST AGENT: Use Gemini to analyze event impact and generate summary.
    
    Performs multi-step reasoning to:
    1. Analyze contextual impact on underserved communities
    2. Assign impact score (1-5)
    3. Generate plain-language community summary
    4. Classify topic category
    
    Args:
        event_id: Unique identifier for the event
        title: Event title/subject
        body: Committee/body name
        date: Event date
        location: Event location
        context: Additional context (agenda items, etc.)
    
    Returns:
        GeminiAnalysisOutput with impact_score, community_impact_summary, and topic
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set, using default analysis")
        return _default_analysis(event_id, title)
    
    try:
        genai.configure(api_key=api_key)
        
        # Use gemini-2.5-flash for best performance and quota availability
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Format the analysis prompt
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            event_id=event_id,
            title=title,
            body=body,
            date=date,
            location=location,
            context=context or "No additional context available"
        )
        
        # Configure for JSON output
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Parse JSON response
        result_text = response.text.strip()
        result_data = json.loads(result_text)
        
        return GeminiAnalysisOutput(
            event_id=str(result_data.get("event_id", event_id)),
            impact_score=int(result_data.get("impact_score", 1)),
            community_impact_summary=result_data.get("community_impact_summary", ""),
            topic=result_data.get("topic", "Other")
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}")
        return _default_analysis(event_id, title)
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return _default_analysis(event_id, title)


def _default_analysis(event_id: str, title: str) -> GeminiAnalysisOutput:
    """
    Enhanced fallback analysis when Gemini is unavailable.
    Provides contextual summaries based on committee type.
    """
    title_lower = title.lower()
    
    # Enhanced keyword-based classification with contextual summaries
    if any(word in title_lower for word in ['zoning', 'housing', 'land use', 'development', 'affordable']):
        topic = "Zoning/Housing"
        score = 4
        summary = "This hearing will discuss zoning changes and housing development that could affect rent prices, building permits, and neighborhood character in your community."
    elif any(word in title_lower for word in ['budget', 'appropriation', 'tax', 'finance']):
        topic = "Budget/Finance"
        score = 4
        summary = "Budget decisions made here directly impact funding for schools, parks, sanitation, and other essential services in your neighborhood."
    elif any(word in title_lower for word in ['school', 'education', 'student']):
        topic = "Education"
        score = 4
        summary = "This meeting addresses school policies, funding, and programs that affect students and families throughout NYC public schools."
    elif any(word in title_lower for word in ['police', 'safety', 'fire', 'emergency']):
        topic = "Public Safety"
        score = 3
        summary = "Public safety policies discussed here may change how police and emergency services operate in your neighborhood."
    elif any(word in title_lower for word in ['transit', 'transportation', 'mta', 'traffic']):
        topic = "Transportation"
        score = 3
        summary = "Transportation decisions here could affect subway service, bus routes, bike lanes, and street safety in your area."
    elif any(word in title_lower for word in ['health', 'hospital', 'social service', 'mental health', 'disabilities', 'addiction']):
        topic = "Health/Social Services"
        score = 4
        summary = "This committee discusses healthcare access, mental health services, and social programs that support vulnerable New Yorkers."
    elif any(word in title_lower for word in ['immigration', 'immigrant']):
        topic = "Legislation/Policy"
        score = 4
        summary = "Immigration policy decisions here affect services, protections, and resources available to immigrant communities across NYC."
    elif any(word in title_lower for word in ['parks', 'recreation']):
        topic = "Legislation/Policy"
        score = 3
        summary = "Parks committee decisions impact green space maintenance, recreation programs, and public facilities in your neighborhood."
    elif any(word in title_lower for word in ['veterans']):
        topic = "Legislation/Policy"
        score = 3
        summary = "This meeting addresses services, benefits, and support programs specifically for NYC's veteran community."
    else:
        topic = "Legislation/Policy"
        score = 2
        summary = "This council meeting will discuss citywide policies and legislation that may have broad impacts on NYC residents."
    
    return GeminiAnalysisOutput(
        event_id=event_id,
        impact_score=score,
        community_impact_summary=summary,
        topic=topic
    )


# =============================================================================
# Tool 4: PDF READING TOOL - Agenda Analysis
# =============================================================================

async def analyze_pdf_agenda(pdf_url: str, event_id: str) -> Optional[str]:
    """
    PDF READING TOOL: Download and analyze PDF agenda using Gemini.
    
    Uses Gemini's File API to upload PDF and extract key information
    relevant to community impact.
    
    Args:
        pdf_url: URL to the PDF agenda file
        event_id: Event ID for reference
    
    Returns:
        Extracted context string from the PDF, or None if analysis fails
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set, skipping PDF analysis")
        return None
    
    if not pdf_url:
        return None
    
    try:
        # Download PDF content
        async with httpx.AsyncClient() as client:
            response = await client.get(pdf_url, timeout=30.0)
            response.raise_for_status()
            pdf_content = response.content
        
        genai.configure(api_key=api_key)
        
        # Upload PDF to Gemini File API
        # Note: For production, you'd use the actual File API upload
        # Here we'll use inline data for PDFs under 20MB
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create a file-like part for the PDF
        pdf_part = {
            "mime_type": "application/pdf",
            "data": pdf_content
        }
        
        prompt = """Extract the key agenda items from this PDF document.
        Focus on items that would affect residents:
        - Budget allocations or cuts
        - Zoning changes
        - New policies or regulations
        - Service changes
        - Community programs
        
        Provide a brief summary (2-3 sentences) of the most impactful items."""
        
        response = model.generate_content([prompt, pdf_part])
        
        return response.text.strip()
        
    except httpx.HTTPError as e:
        logger.error(f"Failed to download PDF from {pdf_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"PDF analysis failed: {e}")
        return None


# =============================================================================
# Utility Functions
# =============================================================================

def transform_legistar_to_civic_event(
    raw_event: Dict[str, Any],
    analysis: GeminiAnalysisOutput,
    coordinates: Tuple[Optional[float], Optional[float], Optional[str]]
) -> CivicEvent:
    """
    Transform raw Legistar event data into a CivicEvent model.
    
    Args:
        raw_event: Raw event dictionary from Legistar API
        analysis: Gemini analysis output
        coordinates: Tuple of (latitude, longitude, borough)
    
    Returns:
        Fully populated CivicEvent model
    """
    # Parse and format date/time
    event_date = raw_event.get("EventDate", "")
    event_time = raw_event.get("EventTime", "")
    
    if event_date:
        try:
            # Parse ISO date format
            dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            if event_time:
                # Combine with time if available
                date_time = f"{dt.strftime('%Y-%m-%d')}T{event_time}"
            else:
                date_time = dt.isoformat()
        except ValueError:
            date_time = event_date
    else:
        date_time = datetime.now().isoformat()
    
    # Build event link
    event_link = raw_event.get("EventInSiteURL") or \
                 f"https://legistar.council.nyc.gov/Calendar.aspx?ID={raw_event.get('EventId', '')}"
    
    return CivicEvent(
        id=str(raw_event.get("EventId", "")),
        title=raw_event.get("EventBodyName", "City Council Meeting"),
        date_time=date_time,
        location=raw_event.get("EventLocation", "City Hall, New York, NY"),
        link=event_link,
        topic=analysis.topic,
        impact_score=analysis.impact_score,
        community_impact_summary=analysis.community_impact_summary,
        latitude=coordinates[0],
        longitude=coordinates[1],
        borough=coordinates[2]
    )


# =============================================================================
# Tool 5: Socrata Parks Events Fetcher (Async with SoQL support)
# =============================================================================

async def get_socrata_dataset_async(
    dataset_id: str,
    soql: Optional[str] = None,
    app_token: Optional[str] = None,
    limit: int = 1000,
    max_pages: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Async fetch for a Socrata dataset using CivicAsyncClient.
    
    Args:
        dataset_id: Socrata resource ID (e.g., "ebds-hqr2")
        soql: Optional SoQL query for server-side filtering
        app_token: Optional app token (uses NYC_OPEN_DATA_TOKEN env var if not provided)
        limit: Page size for pagination (default: 1000)
        max_pages: Max pages to fetch (prevents runaway requests)
    
    Returns:
        List of raw records from the dataset
    """
    base_url = os.getenv("SOCRATA_BASE_URL", "https://data.cityofnewyork.us/resource/")
    async with CivicAsyncClient(base_url=base_url) as client:
        results = await client.fetch_socrata_paginated(
            resource=dataset_id,
            soql=soql,
            app_token=app_token or os.getenv("NYC_OPEN_DATA_TOKEN"),
            limit=limit,
            max_pages=max_pages
        )
        return results or []


async def transform_socrata_to_civic_event(raw: Dict[str, Any]) -> CivicEvent:
    """
    Convert a Socrata record to CivicEvent.
    
    Uses heuristic field mapping for common Socrata schemas.
    Performs geocoding and AI analysis using existing tools.
    
    Args:
        raw: Raw Socrata record dictionary
    
    Returns:
        Transformed CivicEvent object
    """
    # Extract fields with fallbacks for common Socrata schemas
    event_id_raw = (
        raw.get("objectid") or 
        raw.get("id") or 
        raw.get("unique_id") or 
        raw.get("event_id") or 
        raw.get("permitnumber") or
        ""
    )
    
    title = (
        raw.get("event_name") or 
        raw.get("eventname") or
        raw.get("park_name") or 
        raw.get("title") or 
        raw.get("name") or 
        "Community Event"
    )
    
    # Try common date/time fields
    date_time = (
        raw.get("start_date") or 
        raw.get("startdatetime") or 
        raw.get("start_date_time") or
        raw.get("date") or 
        raw.get("event_date") or 
        datetime.now().isoformat()
    )
    
    location = (
        raw.get("location_name") or 
        raw.get("location") or 
        raw.get("address") or 
        raw.get("park_address") or
        raw.get("eventlocation") or
        "New York, NY"
    )
    
    link = raw.get("url") or raw.get("link") or raw.get("eventurl") or ""
    
    description = (
        raw.get("description") or 
        raw.get("details") or 
        raw.get("eventdescription") or 
        ""
    )
    
    # Generate stable ID using hash if no explicit ID
    if not event_id_raw:
        uid_source = f"{title}|{date_time}|{location}"
        event_id = f"socrata-{hashlib.sha256(uid_source.encode('utf-8')).hexdigest()[:12]}"
    else:
        event_id = f"socrata-{event_id_raw}"
    
    # Perform analysis using existing Gemini tool
    analysis = analyze_event_with_gemini(
        event_id=event_id,
        title=title,
        body=description[:200],  # Truncate for context
        date=str(date_time),
        location=location,
        context=description
    )
    
    # Geocode address using existing tool
    coords = geocode_address(location)
    
    return CivicEvent(
        id=event_id,
        title=title,
        date_time=str(date_time),
        location=location,
        link=link,
        topic=analysis.topic,
        impact_score=analysis.impact_score,
        community_impact_summary=analysis.community_impact_summary,
        latitude=coords[0],
        longitude=coords[1],
        borough=coords[2]
    )


async def get_socrata_parks_events(
    days_ahead: int = 30, 
    limit: int = 200,
    borough: Optional[str] = None
) -> List[CivicEvent]:
    """
    Fetch parks-related events from NYC Parks Socrata dataset.
    
    Uses dataset 'fudw-fgrp' (NYC Parks Public Events).
    Supports optional borough filtering via SoQL.
    
    Args:
        days_ahead: Number of days ahead to fetch events for
        limit: Maximum number of records to fetch per page
        borough: Optional borough filter (e.g., "Manhattan", "Brooklyn")
    
    Returns:
        List of transformed CivicEvent objects
    """
    dataset_id = "fudw-fgrp"  # NYC Parks Public Events
    
    # Build SoQL query for date filtering
    today = datetime.now()
    future_date = today + timedelta(days=days_ahead)
    
    # Format dates for SoQL (Socrata uses ISO format)
    today_str = today.strftime("%Y-%m-%d")
    future_str = future_date.strftime("%Y-%m-%d")
    
    # Build SoQL WHERE clause
    where_clauses = [f"date >= '{today_str}'", f"date <= '{future_str}'"]
    
    if borough:
        # Add borough filter if specified
        where_clauses.append(f"borough = '{borough}'")
    
    soql = f"SELECT * WHERE {' AND '.join(where_clauses)}"
    
    logger.info(f"Fetching Socrata parks events with SoQL: {soql}")
    
    try:
        raw_records = await get_socrata_dataset_async(
            dataset_id=dataset_id, 
            soql=soql, 
            limit=limit
        )
        
        logger.info(f"Retrieved {len(raw_records)} raw records from Socrata parks dataset")
        
        civic_events: List[CivicEvent] = []
        for raw in raw_records:
            try:
                civic = await transform_socrata_to_civic_event(raw)
                civic_events.append(civic)
            except Exception as e:
                logger.debug(f"Failed to transform Socrata record: {e}")
                continue
        
        logger.info(f"Transformed {len(civic_events)} Socrata parks events")
        return civic_events
        
    except Exception as e:
        logger.error(f"Failed to fetch Socrata parks events: {e}")
        return []

