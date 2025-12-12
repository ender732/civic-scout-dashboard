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
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

import requests
import httpx
import googlemaps
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from models import LegistarEvent, GeminiAnalysisOutput, CivicEvent

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

def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    GEOLOCATION TOOL: Convert an address string to latitude/longitude coordinates.
    
    Uses Google Maps Geocoding API with proper error handling for:
    - Missing API key
    - Vague or invalid addresses
    - API errors
    
    Args:
        address: The address string to geocode
    
    Returns:
        Tuple of (latitude, longitude) or (None, None) if geocoding fails
    """
    if not address or not address.strip():
        logger.warning("Empty address provided for geocoding")
        return (None, None)
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set, skipping geocoding")
        return (None, None)
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        # Append NYC to improve geocoding accuracy
        full_address = f"{address}, New York City, NY" if "new york" not in address.lower() else address
        
        geocode_result = gmaps.geocode(full_address)
        
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            logger.debug(f"Geocoded '{address}' to ({lat}, {lng})")
            return (lat, lng)
        else:
            logger.warning(f"No geocoding results for address: {address}")
            return (None, None)
            
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Google Maps API error: {e}")
        return (None, None)
    except Exception as e:
        logger.error(f"Unexpected geocoding error: {e}")
        return (None, None)


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
    coordinates: Tuple[Optional[float], Optional[float]]
) -> CivicEvent:
    """
    Transform raw Legistar event data into a CivicEvent model.
    
    Args:
        raw_event: Raw event dictionary from Legistar API
        analysis: Gemini analysis output
        coordinates: Tuple of (latitude, longitude)
    
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
        longitude=coordinates[1]
    )
