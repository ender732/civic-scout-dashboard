import { useState, useMemo } from "react";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { MapPlaceholder } from "@/components/MapPlaceholder";
import { EventFilters } from "@/components/EventFilters";
import { EventCard } from "@/components/EventCard";
import { Footer } from "@/components/Footer";
import type { CivicEvent, Borough, EventTopic } from "@/types/event";

// Sample data - in production this would come from /api/events
const sampleEvents: CivicEvent[] = [
  {
    id: 12345,
    title: "Public Hearing: Zoning Change, CB4",
    impact_summary: "Crucial. This meeting will discuss a plan to eliminate 20 low-income housing units in the area. Your voice is needed to advocate for affordable housing.",
    date_time: "2025-12-20T18:00:00Z",
    location: "Bronx County Hall, Room 101",
    topic: "Zoning/Housing",
    link: "https://council.nyc.gov/calendar/",
  },
  {
    id: 12346,
    title: "School Budget Review Meeting",
    impact_summary: "Important. The Board of Education will review proposed cuts to after-school programs affecting 15 elementary schools in Queens.",
    date_time: "2025-12-18T17:30:00Z",
    location: "Queens Borough Hall, Conference Room A",
    topic: "Schools/Education",
    link: "https://council.nyc.gov/calendar/",
  },
  {
    id: 12347,
    title: "Transit Infrastructure Planning Session",
    impact_summary: "The MTA will present plans for new bus routes in Brooklyn. This could improve commute times for thousands of residents.",
    date_time: "2025-12-22T14:00:00Z",
    location: "Brooklyn Municipal Building, Room 305",
    topic: "Transit/Infrastructure",
    link: "https://council.nyc.gov/calendar/",
  },
  {
    id: 12348,
    title: "Community Safety Forum",
    impact_summary: "Urgent. Discussion on proposed changes to community policing strategies in Manhattan. Resident input will shape policy decisions.",
    date_time: "2025-12-19T19:00:00Z",
    location: "Manhattan Community Center, Main Hall",
    topic: "Public Safety",
    link: "https://council.nyc.gov/calendar/",
  },
  {
    id: 12349,
    title: "Annual Budget Hearing - Parks Department",
    impact_summary: "The Parks Department will present next year's budget. Critical decisions about playground maintenance and new green spaces will be discussed.",
    date_time: "2025-12-23T10:00:00Z",
    location: "City Hall, Council Chambers",
    topic: "Budget/Finance",
    link: "https://council.nyc.gov/calendar/",
  },
  {
    id: 12350,
    title: "Affordable Housing Development Review",
    impact_summary: "Crucial. Final review of a proposed 200-unit affordable housing complex in Staten Island. Community feedback will influence the final decision.",
    date_time: "2025-12-24T16:00:00Z",
    location: "Staten Island Borough Hall, Room 201",
    topic: "Zoning/Housing",
    link: "https://council.nyc.gov/calendar/",
  },
];

export default function Index() {
  const [selectedBoroughs, setSelectedBoroughs] = useState<Borough[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<EventTopic[]>([]);
  const [zipCode, setZipCode] = useState("");

  const handleBoroughChange = (borough: Borough) => {
    setSelectedBoroughs((prev) =>
      prev.includes(borough)
        ? prev.filter((b) => b !== borough)
        : [...prev, borough]
    );
  };

  const handleTopicChange = (topic: EventTopic) => {
    setSelectedTopics((prev) =>
      prev.includes(topic)
        ? prev.filter((t) => t !== topic)
        : [...prev, topic]
    );
  };

  const handleClearFilters = () => {
    setSelectedBoroughs([]);
    setSelectedTopics([]);
    setZipCode("");
  };

  const handleZipCodeSubmit = (zip: string) => {
    setZipCode(zip);
    // In production, this would trigger an API call with the ZIP code
    console.log("Filtering by ZIP code:", zip);
  };

  // Filter events based on selected criteria
  const filteredEvents = useMemo(() => {
    return sampleEvents.filter((event) => {
      if (selectedTopics.length > 0 && !selectedTopics.includes(event.topic)) {
        return false;
      }
      // Borough filtering would work with actual location data
      return true;
    });
  }, [selectedTopics]);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header />
      
      <main id="main-content" className="flex-1">
        <HeroSection onZipCodeSubmit={handleZipCodeSubmit} />

        {/* Map and Filters Section */}
        <section 
          id="map" 
          className="py-10 lg:py-14"
          aria-labelledby="map-section-heading"
        >
          <div className="civic-container">
            <h2 id="map-section-heading" className="sr-only">
              Event Map and Filters
            </h2>
            
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Map - Takes 2 columns on large screens */}
              <div className="lg:col-span-2">
                <MapPlaceholder />
              </div>
              
              {/* Filters Sidebar */}
              <div className="lg:col-span-1">
                <EventFilters
                  selectedBoroughs={selectedBoroughs}
                  selectedTopics={selectedTopics}
                  onBoroughChange={handleBoroughChange}
                  onTopicChange={handleTopicChange}
                  onClearFilters={handleClearFilters}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Events Grid Section */}
        <section 
          className="border-t border-border bg-secondary/20 py-10 lg:py-14"
          aria-labelledby="events-section-heading"
        >
          <div className="civic-container">
            <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 
                  id="events-section-heading"
                  className="font-display text-2xl font-bold text-foreground"
                >
                  Upcoming Meetings
                </h2>
                <p className="mt-1 text-muted-foreground">
                  {filteredEvents.length} events matching your criteria
                </p>
              </div>
              {zipCode && (
                <div className="inline-flex items-center gap-2 rounded-lg bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary">
                  Showing results near {zipCode}
                </div>
              )}
            </div>

            {/* Events Grid */}
            <div 
              className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
              role="list"
              aria-label="Civic events"
            >
              {filteredEvents.map((event, index) => (
                <EventCard key={event.id} event={event} index={index} />
              ))}
            </div>

            {filteredEvents.length === 0 && (
              <div className="rounded-xl border border-dashed border-border bg-card py-16 text-center">
                <p className="text-lg font-medium text-foreground">
                  No events match your filters
                </p>
                <p className="mt-2 text-muted-foreground">
                  Try adjusting your filter criteria to see more results.
                </p>
              </div>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
