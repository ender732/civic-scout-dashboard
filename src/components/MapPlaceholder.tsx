import { MapPin, ZoomIn, ZoomOut, Locate } from "lucide-react";
import { Button } from "@/components/ui/button";

export function MapPlaceholder() {
  return (
    <div 
      className="relative h-full min-h-[400px] overflow-hidden rounded-xl border border-border bg-secondary/50"
      role="img"
      aria-label="Interactive map showing event locations across NYC boroughs. Map integration coming soon."
    >
      {/* Placeholder Map Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-secondary to-muted">
        {/* Grid lines to simulate map */}
        <svg 
          className="absolute inset-0 h-full w-full opacity-30" 
          aria-hidden="true"
        >
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path 
                d="M 40 0 L 0 0 0 40" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="0.5"
                className="text-muted-foreground"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        {/* Simulated borough shapes */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative h-64 w-72">
            {/* Manhattan */}
            <div className="absolute left-1/2 top-1/4 h-24 w-8 -translate-x-1/2 rounded-full bg-primary/20 border border-primary/30" />
            {/* Brooklyn */}
            <div className="absolute bottom-4 left-1/3 h-20 w-24 rounded-3xl bg-primary/15 border border-primary/25" />
            {/* Queens */}
            <div className="absolute right-0 top-1/4 h-28 w-28 rounded-[2rem] bg-primary/15 border border-primary/25" />
            {/* Bronx */}
            <div className="absolute left-1/3 top-0 h-16 w-20 rounded-2xl bg-primary/15 border border-primary/25" />
            {/* Staten Island */}
            <div className="absolute bottom-0 left-0 h-12 w-16 rounded-xl bg-primary/10 border border-primary/20" />
          </div>
        </div>

        {/* Event Markers */}
        <div className="absolute inset-0">
          {[
            { top: "25%", left: "48%", urgent: true },
            { top: "45%", left: "55%", urgent: false },
            { top: "60%", left: "40%", urgent: true },
            { top: "35%", left: "65%", urgent: false },
            { top: "20%", left: "42%", urgent: false },
          ].map((marker, i) => (
            <div
              key={i}
              className="absolute"
              style={{ top: marker.top, left: marker.left }}
            >
              <div className={`relative flex h-8 w-8 items-center justify-center rounded-full ${
                marker.urgent 
                  ? "bg-accent text-accent-foreground" 
                  : "bg-primary text-primary-foreground"
              } shadow-civic-md`}>
                <MapPin className="h-4 w-4" />
                {marker.urgent && (
                  <span className="absolute -right-1 -top-1 flex h-3 w-3">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-accent" />
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Map Controls */}
      <div className="absolute right-3 top-3 flex flex-col gap-2">
        <Button 
          variant="secondary" 
          size="icon" 
          className="h-9 w-9 shadow-civic-sm"
          aria-label="Zoom in"
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button 
          variant="secondary" 
          size="icon" 
          className="h-9 w-9 shadow-civic-sm"
          aria-label="Zoom out"
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button 
          variant="secondary" 
          size="icon" 
          className="h-9 w-9 shadow-civic-sm"
          aria-label="Use my location"
        >
          <Locate className="h-4 w-4" />
        </Button>
      </div>

      {/* Coming Soon Badge */}
      <div className="absolute bottom-3 left-3 rounded-lg bg-card/95 px-3 py-2 text-xs font-medium text-muted-foreground shadow-civic-sm backdrop-blur">
        🗺️ Interactive map integration coming soon
      </div>
    </div>
  );
}
