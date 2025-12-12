import { useState } from "react";
import { Search, MapPin, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface HeroSectionProps {
  onZipCodeSubmit: (zipCode: string) => void;
}

export function HeroSection({ onZipCodeSubmit }: HeroSectionProps) {
  const [zipCode, setZipCode] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (zipCode.trim()) {
      onZipCodeSubmit(zipCode.trim());
    }
  };

  return (
    <section 
      id="home"
      className="relative overflow-hidden bg-primary py-16 sm:py-20 lg:py-24"
      aria-labelledby="hero-heading"
    >
      {/* Background Pattern */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}
        aria-hidden="true"
      />

      <div className="civic-container relative">
        <div className="mx-auto max-w-3xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-accent/20 px-4 py-1.5 text-sm font-medium text-accent-foreground">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
            <span>Track decisions that affect your neighborhood</span>
          </div>

          {/* Heading */}
          <h1 
            id="hero-heading"
            className="font-display text-3xl font-bold tracking-tight text-primary-foreground sm:text-4xl lg:text-5xl"
          >
            Crucial Meetings in{" "}
            <span className="text-accent">Your Community</span>
          </h1>

          {/* Subheading */}
          <p className="mt-4 text-lg text-primary-foreground/80 sm:text-xl">
            Stay informed about zoning changes, school board meetings, and budget decisions 
            happening near you. Your voice matters.
          </p>

          {/* ZIP Code Search */}
          <form 
            onSubmit={handleSubmit}
            className="mx-auto mt-8 flex max-w-md flex-col gap-3 sm:flex-row"
            role="search"
            aria-label="Filter events by ZIP code"
          >
            <div className="relative flex-1">
              <MapPin 
                className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" 
                aria-hidden="true" 
              />
              <Input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={5}
                placeholder="Enter your ZIP code"
                value={zipCode}
                onChange={(e) => setZipCode(e.target.value.replace(/\D/g, ""))}
                className="h-12 bg-card pl-11 text-base shadow-civic-md placeholder:text-muted-foreground"
                aria-label="ZIP code"
              />
            </div>
            <Button 
              type="submit" 
              variant="hero" 
              size="lg"
              className="h-12 shadow-civic-lg"
            >
              <Search className="mr-2 h-5 w-5" aria-hidden="true" />
              Filter Events
            </Button>
          </form>

          {/* Stats */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-8 text-primary-foreground/90">
            <div className="text-center">
              <div className="font-display text-2xl font-bold">150+</div>
              <div className="text-sm text-primary-foreground/70">Upcoming Meetings</div>
            </div>
            <div className="hidden h-8 w-px bg-primary-foreground/20 sm:block" aria-hidden="true" />
            <div className="text-center">
              <div className="font-display text-2xl font-bold">5</div>
              <div className="text-sm text-primary-foreground/70">Boroughs Covered</div>
            </div>
            <div className="hidden h-8 w-px bg-primary-foreground/20 sm:block" aria-hidden="true" />
            <div className="text-center">
              <div className="font-display text-2xl font-bold">12K+</div>
              <div className="text-sm text-primary-foreground/70">Active Citizens</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
