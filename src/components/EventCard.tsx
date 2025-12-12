import { Calendar, MapPin, ExternalLink, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { CivicEvent, EventTopic } from "@/types/event";

interface EventCardProps {
  event: CivicEvent;
  index: number;
}

const topicStyles: Record<string, { bg: string; text: string }> = {
  "Zoning/Housing": { bg: "bg-orange-500/15", text: "text-orange-600" },
  "Education": { bg: "bg-blue-500/15", text: "text-blue-600" },
  "Budget/Finance": { bg: "bg-green-500/15", text: "text-green-600" },
  "Transportation": { bg: "bg-purple-500/15", text: "text-purple-600" },
  "Public Safety": { bg: "bg-red-500/15", text: "text-red-600" },
  "Health/Social Services": { bg: "bg-pink-500/15", text: "text-pink-600" },
  "Legislation/Policy": { bg: "bg-slate-500/15", text: "text-slate-600" },
  "Environment": { bg: "bg-emerald-500/15", text: "text-emerald-600" },
  "Other": { bg: "bg-gray-500/15", text: "text-gray-600" },
};

function formatDateTime(dateString: string): string {
  // Handle format like "2025-12-12T10:00 AM"
  try {
    // Split the date and time parts
    const [datePart, timePart] = dateString.split('T');
    if (!datePart) return dateString;
    
    const [year, month, day] = datePart.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    const dateObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    const dayName = dayNames[dateObj.getDay()];
    const monthName = monthNames[parseInt(month) - 1];
    
    const timeStr = timePart || '';
    return `${dayName}, ${monthName} ${parseInt(day)}, ${timeStr}`;
  } catch {
    return dateString;
  }
}

function isHighImpact(impactScore: number, summary: string): boolean {
  if (impactScore >= 4) return true;
  const urgentKeywords = ["crucial", "urgent", "critical", "vulnerable", "underserved"];
  return urgentKeywords.some(keyword => 
    summary.toLowerCase().includes(keyword)
  );
}

export function EventCard({ event, index }: EventCardProps) {
  const urgent = isHighImpact(event.impact_score, event.community_impact_summary);
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
            {event.community_impact_summary.split(".")[0]}.
          </strong>{" "}
          {event.community_impact_summary.split(".").slice(1).join(".").trim()}
        </p>

        {/* Impact Score */}
        <div className="mb-3 flex items-center gap-1">
          <span className="text-xs text-muted-foreground">Impact:</span>
          {[1, 2, 3, 4, 5].map((star) => (
            <span key={star} className={star <= event.impact_score ? "text-yellow-500" : "text-gray-300"}>★</span>
          ))}
        </div>

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
