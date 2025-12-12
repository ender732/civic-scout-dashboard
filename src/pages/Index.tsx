import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { MapPlaceholder } from "@/components/MapPlaceholder";
import { EventFilters } from "@/components/EventFilters";
import { EventCard } from "@/components/EventCard";
import { Footer } from "@/components/Footer";
import type { CivicEvent, Borough, EventTopic } from "@/types/event";

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

  // Fetch events from API
  const { data: eventsData, isLoading, error } = useQuery({
    queryKey: ['events'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8001/api/events');
      if (!response.ok) {
        throw new Error('Failed to fetch events');
      }
      return response.json();
    },
  });

  const events = eventsData?.events || [];

  // Filter events based on selected criteria
  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      // Topic filtering
      if (selectedTopics.length > 0 && !selectedTopics.includes(event.topic)) {
        return false;
      }
      // Borough filtering
      if (selectedBoroughs.length > 0 && event.borough && !selectedBoroughs.includes(event.borough)) {
        return false;
      }
      return true;
    });
  }, [selectedTopics, selectedBoroughs, events]);

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
            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-muted-foreground">Loading events...</p>
                </div>
              </div>
            ) : error ? (
              <div className="rounded-xl border border-destructive/50 bg-destructive/5 py-16 text-center">
                <p className="text-lg font-medium text-destructive">
                  Failed to load events
                </p>
                <p className="mt-2 text-muted-foreground">
                  Please check your connection and try again.
                </p>
              </div>
            ) : (
              <div 
                className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
                role="list"
                aria-label="Civic events"
              >
                {filteredEvents.map((event, index) => (
                  <EventCard key={event.id} event={event} index={index} />
                ))}
              </div>
            )}

            {filteredEvents.length === 0 && !isLoading && !error && (
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
