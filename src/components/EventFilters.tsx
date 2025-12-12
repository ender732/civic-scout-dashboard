import { Filter, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import type { Borough, EventTopic } from "@/types/event";

interface EventFiltersProps {
  selectedBoroughs: Borough[];
  selectedTopics: EventTopic[];
  onBoroughChange: (borough: Borough) => void;
  onTopicChange: (topic: EventTopic) => void;
  onClearFilters: () => void;
}

const boroughs: Borough[] = [
  "Manhattan",
  "Brooklyn",
  "Queens",
  "Bronx",
  "Staten Island",
];

const topics: { value: EventTopic; label: string; colorClass: string }[] = [
  { value: "Zoning/Housing", label: "Zoning/Housing", colorClass: "bg-orange-500" },
  { value: "Education", label: "Education", colorClass: "bg-blue-500" },
  { value: "Budget/Finance", label: "Budget/Finance", colorClass: "bg-green-500" },
  { value: "Transportation", label: "Transportation", colorClass: "bg-purple-500" },
  { value: "Public Safety", label: "Public Safety", colorClass: "bg-red-500" },
  { value: "Health/Social Services", label: "Health/Social Services", colorClass: "bg-pink-500" },
  { value: "Legislation/Policy", label: "Legislation/Policy", colorClass: "bg-slate-500" },
];

export function EventFilters({
  selectedBoroughs,
  selectedTopics,
  onBoroughChange,
  onTopicChange,
  onClearFilters,
}: EventFiltersProps) {
  const hasActiveFilters = selectedBoroughs.length > 0 || selectedTopics.length > 0;

  return (
    <aside 
      className="rounded-xl border border-border bg-card p-5 shadow-civic-sm"
      aria-label="Event filters"
    >
      {/* Header */}
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-foreground">
          <Filter className="h-5 w-5" aria-hidden="true" />
          <h2 className="font-display text-lg font-semibold">Filters</h2>
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="h-8 text-xs text-muted-foreground hover:text-foreground"
          >
            <X className="mr-1 h-3 w-3" aria-hidden="true" />
            Clear all
          </Button>
        )}
      </div>

      {/* Borough Filter */}
      <fieldset className="mb-6">
        <legend className="mb-3 text-sm font-semibold text-foreground">
          Borough
        </legend>
        <div className="space-y-2.5">
          {boroughs.map((borough) => (
            <div key={borough} className="flex items-center gap-3">
              <Checkbox
                id={`borough-${borough}`}
                checked={selectedBoroughs.includes(borough)}
                onCheckedChange={() => onBoroughChange(borough)}
                aria-describedby={`borough-${borough}-label`}
              />
              <Label
                id={`borough-${borough}-label`}
                htmlFor={`borough-${borough}`}
                className="cursor-pointer text-sm font-normal text-muted-foreground hover:text-foreground"
              >
                {borough}
              </Label>
            </div>
          ))}
        </div>
      </fieldset>

      {/* Topic Filter */}
      <fieldset>
        <legend className="mb-3 text-sm font-semibold text-foreground">
          Topic
        </legend>
        <div className="space-y-2.5">
          {topics.map((topic) => (
            <div key={topic.value} className="flex items-center gap-3">
              <Checkbox
                id={`topic-${topic.value}`}
                checked={selectedTopics.includes(topic.value)}
                onCheckedChange={() => onTopicChange(topic.value)}
                aria-describedby={`topic-${topic.value}-label`}
              />
              <Label
                id={`topic-${topic.value}-label`}
                htmlFor={`topic-${topic.value}`}
                className="flex cursor-pointer items-center gap-2 text-sm font-normal text-muted-foreground hover:text-foreground"
              >
                <span 
                  className={`h-2.5 w-2.5 rounded-full ${topic.colorClass}`} 
                  aria-hidden="true" 
                />
                {topic.label}
              </Label>
            </div>
          ))}
        </div>
      </fieldset>

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="mt-6 rounded-lg bg-secondary/50 p-3">
          <p className="text-xs text-muted-foreground">
            Showing events in{" "}
            <span className="font-medium text-foreground">
              {selectedBoroughs.length > 0 
                ? selectedBoroughs.join(", ") 
                : "all boroughs"}
            </span>
            {selectedTopics.length > 0 && (
              <>
                {" "}about{" "}
                <span className="font-medium text-foreground">
                  {selectedTopics.join(", ")}
                </span>
              </>
            )}
          </p>
        </div>
      )}
    </aside>
  );
}
