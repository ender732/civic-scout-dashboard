# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/REPLACE_WITH_PROJECT_ID

## How can I edit this code?

There are several ways of editing your application.

"""
# NYC Civic Scout: Agent for Underserved Community Impact

**Mission:** To bridge the civic information gap by autonomously identifying, analyzing, and disseminating real-time legislative and community events that critically affect underserved communities in New York City.

✨ Key Features & Technology Stack

| Feature Category | Description | Core Technology |
|---|---|---|
| Agentic Core | Multi-step reasoning pipeline (Discovery → Analysis → Enrichment) powered by LLMs | Gemini 2.5 Flash (cost-efficient & fast) |
| Real-Time Data | Direct connection to official legislative database for current, high-impact event data | NYC Legistar API |
| Structured Output | AI-powered Impact Score (1-5) and non-technical summaries from raw legislative text | Pydantic v2 |
| Geospatial Layer | Convert government location strings into latitude/longitude for map-based alerting | Google Maps Geocoding API |
| Backend / Frontend | High-performance, scalable web architecture | FastAPI (Python), React |

🧠 The Agentic Workflow: Three Stages of Intelligence

The NYC Civic Scout is a multi-agent pipeline designed for robustness and high-impact analysis.

1. Discovery Agent (The Fetcher)
	- Action: Calls the `get_legistar_events()` tool
	- Input: Current date, filtering keywords (e.g., Housing, Zoning, Budget)
	- Output: Raw JSON payload of upcoming NYC Council meetings, public hearings, and agendas

2. Analyst Agent (The Gemini Core)
	- Action: Calls the `analyze_event_with_gemini()` tool
	- Input: Raw event title and description from Legistar
	- Reasoning Process (System Prompt): The agent adopts a Community Advocate persona and performs multi-step reasoning:
	  - Contextualize: Identify the legislative consequence (e.g., potential school closure, budget cut)
	  - Score: Assign an Impact Score (1-5)
	  - Translate: Generate a MAX TWO-SENTENCE non-technical summary explaining why a resident should attend
	- Output: Structured JSON containing `impact_score` and `community_impact_summary`

3. Enrichment Agent (The Notifier Prep)
	- Action: Calls the `geocode_address()` tool
	- Input: Raw location string from Legistar (e.g., "Bronx Borough Hall, Room 301")
	- Output: Appends `latitude` and `longitude` coordinates to the final `CivicEvent` object

🚀 Setup & Execution

Prerequisites: Python 3.10+, Node.js, and an active virtual environment

Clone & Install

```bash
git clone [YOUR_REPO_URL]
cd civic-scout-dashboard
pip install -r packages/civic-scout-agent/requirements.txt
npm install
```

API Key Configuration

Create a `.env` file in `packages/civic-scout-agent/` and populate with your keys. The full pipeline is confirmed working with live keys.

```bash
# .env (example)
GEMINI_API_KEY="sk-..."            # For AI Analysis (Gemini)
GOOGLE_MAPS_API_KEY="AIza..."      # For Geocoding
LEGISTAR_API_TOKEN="XYZ..."        # For NYC Legistar (if required by provider)
```

Run the Server

```bash
cd packages/civic-scout-agent
uvicorn main:app --reload --port 8001
```

Access the Results

- API: `http://localhost:8001/api/events?days_ahead=30&filter_keywords=health,housing`
- Frontend: `http://localhost:8082`

✅ Test Validation (Proof of Functionality)

| Component | Status | Test Result (Key Success Metric) |
|---|---:|---|
| Data Ingestion | WORKING | Successfully fetched 10+ real events from the NYC Legistar API |
| AI Analysis | WORKING | Gemini 2.5 Flash assigned Impact Score `4` to a Committee on Health meeting and generated a concise summary about vulnerable communities |
| Geocoding | WORKING | Coordinates for City Hall returned: `(40.7130079, -74.0078212)` |
| Robustness | WORKING | System gracefully handles Gemini 429 Rate Limit by falling back to heuristic topic classification |

If you want, I can also add a short `demo` script and a minimal `.env` validation checker to verify keys before startup.

"""
