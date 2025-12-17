#!/usr/bin/env python3
"""
NYC Civic Scout - Demo Script

This script demonstrates the full agentic pipeline:
1. Discovery Agent: Fetch events from Legistar
2. Analyst Agent: AI-powered impact analysis
3. Enrichment Agent: Geocoding
"""

import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

def demo():
    """Run the Civic Scout demo."""
    
    # Header
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]NYC Civic Scout Agent Demo[/bold cyan]\n"
        "[dim]Bridging the civic information gap for underserved communities[/dim]",
        border_style="cyan"
    ))
    console.print("\n")
    
    # Fetch events
    console.print("📡 [bold]Discovery Agent:[/bold] Fetching events from NYC Legistar API...", style="yellow")
    
    try:
        response = requests.get("http://localhost:8001/api/events?days_ahead=7")
        response.raise_for_status()
        data = response.json()
        
        events = data.get("events", [])
        console.print(f"✅ Retrieved {len(events)} upcoming civic events\n", style="green")
        
        # Create table
        table = Table(
            title="🗽 Upcoming NYC Council Meetings",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )
        
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Event", style="white", width=40)
        table.add_column("Topic", style="yellow", width=20)
        table.add_column("Impact", style="red", justify="center", width=8)
        table.add_column("Location", style="green", width=15)
        
        # Display top 5 events
        for event in events[:5]:
            date = event.get("date_time", "").split("T")[0]
            title = event.get("title", "")[:38] + "..." if len(event.get("title", "")) > 38 else event.get("title", "")
            topic = event.get("topic", "N/A")
            impact = f"{event.get('impact_score', 0)}/5 {'⭐' * event.get('impact_score', 0)}"
            
            lat = event.get("latitude")
            lng = event.get("longitude")
            location = f"({lat:.4f}, {lng:.4f})" if lat and lng else "N/A"
            
            table.add_row(date, title, topic, impact, location)
        
        console.print(table)
        console.print("\n")
        
        # Highlight a high-impact event
        high_impact = [e for e in events if e.get("impact_score", 0) >= 4]
        if high_impact:
            event = high_impact[0]
            console.print(Panel(
                f"[bold]{event.get('title')}[/bold]\n\n"
                f"📅 {event.get('date_time')}\n"
                f"📍 {event.get('location')}\n"
                f"🎯 Impact Score: {event.get('impact_score')}/5\n\n"
                f"[italic]{event.get('community_impact_summary')}[/italic]",
                title="🔥 High-Impact Event Alert",
                border_style="red",
                expand=False
            ))
        
        console.print("\n")
        
        # System info
        console.print("🧠 [bold]Agentic Pipeline Status:[/bold]", style="blue")
        console.print("  ✅ Discovery Agent: Legistar API", style="green")
        console.print("  ✅ Analyst Agent: Enhanced AI summaries", style="green")
        console.print("  ✅ Enrichment Agent: Google Maps geocoding", style="green")
        
        console.print("\n")
        console.print("🌐 [bold]Access the dashboard:[/bold] http://localhost:8080", style="cyan")
        console.print("📊 [bold]API endpoint:[/bold] http://localhost:8001/api/events", style="cyan")
        console.print("\n")
        
    except requests.exceptions.ConnectionError:
        console.print("❌ [bold red]Error:[/bold red] Backend server not running!", style="red")
        console.print("   Start with: [cyan]python3 main.py[/cyan]")
    except Exception as e:
        console.print(f"❌ [bold red]Error:[/bold red] {str(e)}", style="red")

if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        console.print("\n\n👋 Demo interrupted. Thanks for watching!", style="yellow")
