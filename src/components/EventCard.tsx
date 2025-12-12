import { Calendar, MapPin, ExternalLink, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { CivicEvent, EventTopic } from "@/types/event";

interface EventCardProps {
  event: CivicEvent;
  index: number;
}

const topicStyles: Record<EventTopic, { bg: string; text: string }> = {
  "Zoning/Housing": { bg: "bg-topic-zoning/15", text: "text-topic-zoning" },
  "Schools/Education": { bg: "bg-topic-schools/15", text: "text-topic-schools" },
  "Budget/Finance": { bg: "bg-topic-budget/15", text: "text-topic-budget" },
  "Transit/Infrastructure": { bg: "bg-topic-transit/15", text: "text-topic-transit" },
  "Public Safety": { bg: "bg-topic-safety/15", text: "text-topic-safety" },
  "Other": { bg: "bg-topic-default/15", text: "text-topic-default" },
};

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  }) + ", " + date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function isUrgent(impactSummary: string): boolean {
  const urgentKeywords = ["crucial", "urgent", "critical", "eliminate", "cut"];
  return urgentKeywords.some(keyword => 
    impactSummary.toLowerCase().includes(keyword)
  );
}

export function EventCard({ event, index }: EventCardProps) {
  const urgent = isUrgent(event.impact_summary);
  const topicStyle = topicStyles[event.topic] || topicStyles["Other"];

  return (
    <article
      className={`group relative flex flex-col overflow-hidden rounded-xl border bg-card shadow-civic-sm transition-all duration-300 hover:shadow-civic-md animate-fade-in ${
        urgent ? "border-accent/50" : "border-border"
      }`}
      style={{ animationDelay: `${index * 75}ms` }}
      aria-labelledby={`event-title-${event.id}`}
    >
      {/* Urgent Indicator */}
      {urgent && (
        <div className="flex items-center gap-2 bg-accent/10 px-4 py-2 text-sm font-medium text-accent">
          <AlertTriangle className="h-4 w-4" aria-hidden="true" />
          <span>High Impact Meeting</span>
        </div>
      )}

      <div className="flex flex-1 flex-col p-5">
        {/* Topic Badge */}
        <div className="mb-3">
          <Badge 
            variant="secondary"
            className={`${topicStyle.bg} ${topicStyle.text} border-0 font-medium`}
          >
            {event.topic}
          </Badge>
        </div>

        {/* Title */}
        <h3 
          id={`event-title-${event.id}`}
          className="mb-3 font-display text-lg font-semibold leading-snug text-foreground group-hover:text-primary transition-colors"
        >
          {event.title}
        </h3>

        {/* Impact Summary */}
        <p className="mb-4 flex-1 text-sm leading-relaxed text-muted-foreground">
          <strong className="font-semibold text-foreground">
            {event.impact_summary.split(".")[0]}.
          </strong>{" "}
          {event.impact_summary.split(".").slice(1).join(".").trim()}
        </p>

        {/* Meta Info */}
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-start gap-2">
            <Calendar className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <time dateTime={event.date_time}>
              {formatDateTime(event.date_time)}
            </time>
          </div>
          <div className="flex items-start gap-2">
            <MapPin className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{event.location}</span>
          </div>
        </div>

        {/* CTA Button */}
        <div className="mt-5 pt-4 border-t border-border">
          <Button
            variant="outline"
            className="w-full justify-center"
            asChild
          >
            <a 
              href={event.link} 
              target="_blank" 
              rel="noopener noreferrer"
              aria-label={`View full agenda for ${event.title} (opens in new tab)`}
            >
              View Full Agenda
              <ExternalLink className="ml-2 h-4 w-4" aria-hidden="true" />
            </a>
          </Button>
        </div>
      </div>
    </article>
  );
}
