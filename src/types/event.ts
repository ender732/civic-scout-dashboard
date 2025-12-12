export interface CivicEvent {
  id: number;
  title: string;
  impact_summary: string;
  date_time: string;
  location: string;
  topic: EventTopic;
  link: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
}

export type EventTopic = 
  | "Zoning/Housing" 
  | "Schools/Education" 
  | "Budget/Finance" 
  | "Transit/Infrastructure" 
  | "Public Safety"
  | "Other";

export type Borough = "Manhattan" | "Brooklyn" | "Queens" | "Bronx" | "Staten Island";
