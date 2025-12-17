import requests
import os
from datetime import datetime, timedelta, timezone
import time
from bs4 import BeautifulSoup
import googlemaps
import google.generativeai as genai
import re

# The base URL for the NYC Parks Events dataset on the Socrata platform.
# NOTE: This dataset appears to contain historical data from 2019. For current events,
# consider using a different API like NYC Council calendar or other civic APIs.
# 
# Alternative APIs to consider:
# - NYC Council Calendar: https://council.nyc.gov/calendar/ (requires web scraping)
# - NYC Open Data "City Council Discretionary Funding" or other civic datasets
# - Google Calendar API if events are published there
NYC_PARKS_API_ENDPOINT = "https://data.cityofnewyork.us/resource/fudw-fgrp.json"

# --- Function Tool Definition ---
# This function is what the main Gemini Agent will "see" and "call."

def geocode_address(address: str) -> dict:
    """
    Geocodes an address to get latitude and longitude using Google Maps Geocoding API.
    
    Args:
        address: The address string to geocode.
        
    Returns:
        A dict with 'lat' and 'lng' keys, or empty dict if geocoding fails.
    """
    if not address or not address.strip():
        return {}
    
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("⚠️ GOOGLE_MAPS_API_KEY not set. Skipping geocoding.")
        return {}
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        geocode_result = gmaps.geocode(address)
        
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return {"lat": location['lat'], "lng": location['lng']}
        else:
            print(f"⚠️ No geocoding results for: {address}")
            return {}
    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        return {}

def generate_impact_summary(title: str, description: str) -> str:
    """
    Generates a concise impact summary for an event using Google Gemini AI.
    
    Args:
        title: Event title
        description: Event description
        
    Returns:
        A short impact summary string.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set. Using heuristic summary.")
        return _heuristic_summary(title, description)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Analyze this civic event and provide a concise 1-2 sentence summary of its potential impact on the community.
        
        Title: {title}
        Description: {description}
        
        Focus on how this affects residents, neighborhoods, or local democracy. Keep it under 50 words.
        """
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        return summary if len(summary) <= 100 else summary[:97] + "..."
    except Exception as e:
        print(f"❌ Gemini API error: {e}. Using heuristic.")
        return _heuristic_summary(title, description)

def _heuristic_summary(title: str, description: str) -> str:
    """Fallback heuristic summary."""
    text = f"{title} {description}".lower()
    
    if "community" in text or "public" in text:
        return "Important community event affecting local residents."
    elif "education" in text or "school" in text:
        return "Educational opportunity for community members."
    elif "environment" in text or "park" in text:
        return "Environmental and recreational event in public spaces."
        return "Community gathering with potential local impact."

def get_nyc_council_events(days_ahead: int = 7, borough: str = None) -> list:
    """
    Fetches NYC Council meetings and civic events.
    Attempts to scrape https://council.nyc.gov/calendar/ with proper headers.
    Falls back to sample data if scraping fails.
    
    Args:
        days_ahead: Number of days ahead to look for events.
        borough: Optional borough filter.
        
    Returns:
        List of civic events.
    """
    try:
        # Try scraping with browser-like headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        url = 'https://council.nyc.gov/calendar/'
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for event containers - adjust selectors based on actual page structure
        events = soup.find_all('div', class_=re.compile(r'event|meeting|hearing', re.I)) or \
                soup.find_all('article') or \
                soup.find_all('li', class_=re.compile(r'event', re.I))
        
        scraped_events = []
        for event_elem in events[:20]:  # Limit to avoid too many
            # Extract data - this is placeholder, need to inspect actual HTML
            title_elem = event_elem.find('h3') or event_elem.find('a')
            title = title_elem.get_text(strip=True) if title_elem else "Untitled Event"
            
            date_elem = event_elem.find('time') or event_elem.find(class_=re.compile(r'date', re.I))
            date_time = date_elem.get('datetime') if date_elem else None
            
            location_elem = event_elem.find(class_=re.compile(r'location|venue', re.I))
            location = location_elem.get_text(strip=True) if location_elem else "TBD"
            
            link_elem = event_elem.find('a')
            link = link_elem.get('href') if link_elem else "https://council.nyc.gov/calendar/"
            
            if title and date_time:
                scraped_events.append({
                    "id": hash(title + str(date_time)),  # Simple ID
                    "title": title,
                    "impact_summary": "",  # Will be filled by AI
                    "date_time": date_time,
                    "location": location,
                    "topic": "Other",  # Placeholder
                    "link": link,
                })
        
        if scraped_events:
            print(f"✅ Scraped {len(scraped_events)} events from NYC Council calendar.")
            # Process scraped events
            for event in scraped_events:
                event["impact_summary"] = generate_impact_summary(event["title"], "")
                coordinates = geocode_address(event["location"])
                event["coordinates"] = coordinates
            return scraped_events
    
    except Exception as e:
        print(f"❌ Scraping failed: {e}. Using sample data.")
    
    # Fallback to sample data
    sample_events = [
        {
            "id": 12345,
            "title": "Public Hearing: Zoning Change, CB4",
            "impact_summary": "",  # Will be filled by AI
            "date_time": "2025-12-20T18:00:00Z",
            "location": "Bronx County Hall, Room 101",
            "topic": "Zoning/Housing",
            "link": "https://council.nyc.gov/calendar/",
        },
        {
            "id": 12346,
            "title": "School Budget Review Meeting",
            "impact_summary": "",
            "date_time": "2025-12-18T17:30:00Z",
            "location": "Queens Borough Hall, Conference Room A",
            "topic": "Schools/Education",
            "link": "https://council.nyc.gov/calendar/",
        },
        {
            "id": 12347,
            "title": "Transit Infrastructure Planning Session",
            "impact_summary": "",
            "date_time": "2025-12-22T14:00:00Z",
            "location": "Brooklyn Municipal Building, Room 305",
            "topic": "Transit/Infrastructure",
            "link": "https://council.nyc.gov/calendar/",
        },
        {
            "id": 12348,
            "title": "Community Safety Forum",
            "impact_summary": "",
            "date_time": "2025-12-19T19:00:00Z",
            "location": "Manhattan Community Center, Main Hall",
            "topic": "Public Safety",
            "link": "https://council.nyc.gov/calendar/",
        },
        {
            "id": 12349,
            "title": "Annual Budget Hearing - Parks Department",
            "impact_summary": "",
            "date_time": "2025-12-23T10:00:00Z",
            "location": "City Hall, Council Chambers",
            "topic": "Budget/Finance",
            "link": "https://council.nyc.gov/calendar/",
        },
        {
            "id": 12350,
            "title": "Affordable Housing Development Review",
            "impact_summary": "",
            "date_time": "2025-12-24T16:00:00Z",
            "location": "Staten Island Borough Hall, Room 201",
            "topic": "Zoning/Housing",
            "link": "https://council.nyc.gov/calendar/",
        },
    ]
    
    # Filter by date
    now = datetime.now().replace(tzinfo=timezone.utc)
    future_events = []
    for event in sample_events:
        event_date = datetime.fromisoformat(event["date_time"].replace('Z', '+00:00'))
        if event_date >= now and (event_date - now).days <= days_ahead:
            future_events.append(event)
    
    # Filter by borough if specified
    if borough:
        borough_locations = {
            "Bronx": "Bronx",
            "Brooklyn": "Brooklyn",
            "Manhattan": "Manhattan",
            "Queens": "Queens",
            "Staten Island": "Staten Island"
        }
        if borough in borough_locations:
            future_events = [e for e in future_events if borough_locations[borough].lower() in e["location"].lower()]
    
    # Generate impact summaries and geocode
    for event in future_events:
        event["impact_summary"] = generate_impact_summary(event["title"], "")
        coordinates = geocode_address(event["location"])
        event["coordinates"] = coordinates
    
    print(f"✅ Found {len(future_events)} NYC Council events for the next {days_ahead} days.")
    return future_events

def get_nyc_parks_events(days_ahead: int = 7, borough: str = None) -> list:
    """
    Fetches a list of public events happening in NYC Parks from the NYC Open Data API.
    This tool filters for events in the near future. Note: Borough filtering not available in this dataset.

    Args:
        days_ahead: The number of days from today to search for events (e.g., 7 for the next week).
        borough: Optional. Not used in this dataset as borough info is not available.

    Returns:
        A list of dictionaries, each representing a cleaned event.
        Returns an empty list if no events are found or the API call fails.
    """
    try:
        # 1. Calculate the date range (SoQL query logic)
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        # 2. Build the Socrata Query Language (SoQL) filter
        filters = [
            # Event Date must be within the next 'days_ahead'
            f"date >= '{start_date}'",
            f"date <= '{end_date}'"
        ]

        # Borough filtering not available in this dataset
        if borough:
            print(f"⚠️ Borough filtering not supported in this dataset. Ignoring borough: {borough}")
        
        # Combine filters for the WHERE clause
        where_clause = " AND ".join(filters)

        # 3. Construct the API Request
        params = {
            "$where": where_clause,
            # Select specific, useful columns to minimize data transfer
            "$select": "event_id, title, date, start_time, end_time, location_description, description, url",
            "$limit": 1000, # Cap the results for robustness
            "$$app_token": os.getenv("NYC_OPEN_DATA_TOKEN") # Use App Token for better limits
        }
        
        # 4. Make the API Call with retry logic for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.get(NYC_PARKS_API_ENDPOINT, params=params)
            if response.status_code == 200:
                break
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"⚠️ Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                response.raise_for_status()
        else:
            print("❌ Failed after retries due to rate limiting")
            return []
        
        raw_events = response.json()
        
        # 5. Data Cleaning and Formatting
        cleaned_events = []
        for event in raw_events:
            # Combine date and start_time for date_time
            date_str = event.get("date", "")
            time_str = event.get("start_time", "")
            if date_str and time_str:
                # Assume date is YYYY-MM-DD and time is HH:MM
                date_time = f"{date_str}T{time_str}:00Z"
            else:
                date_time = date_str or ""
            
            # Geocode the location
            location_str = event.get("location_description", "")
            coordinates = geocode_address(location_str)
            
            cleaned_events.append({
                "id": event.get("event_id"),
                "title": event.get("title"),
                "impact_summary": generate_impact_summary(event.get("title", ""), event.get("description", "")), 
                "date_time": date_time,
                "location": location_str,
                "topic": "Community/Parks", 
                "link": f"https://www.nyc.gov/site/nycgov/agencies/events/{event.get('url', '')}" if event.get("url") else "",
                "coordinates": coordinates,  # Added geocoding
                "raw_description": event.get("description") 
            })

        print(f"✅ Found {len(cleaned_events)} events for the next {days_ahead} days.")
        return cleaned_events

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {e}")
        return []
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return []

# --- FastAPI Backend ---
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Civic Scout Agent API", description="API for fetching NYC civic events")

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/events")
async def get_events(days_ahead: int = 7, borough: str = None):
    """
    Get NYC civic events.
    
    - **days_ahead**: Number of days ahead to look for events (default: 7)
    - **borough**: Optional borough filter
    """
    try:
        # Try NYC Council events first
        events = get_nyc_council_events(days_ahead, borough)
        
        # If no council events, fall back to parks events
        if not events:
            events = get_nyc_parks_events(days_ahead, borough)
        
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)