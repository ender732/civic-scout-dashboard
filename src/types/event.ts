export interface CivicEvent {
  id: string;
  title: string;
  community_impact_summary: string;
  date_time: string;
  location: string;
  topic: EventTopic;
  link: string;
  impact_score: number;
  latitude?: number | null;
  longitude?: number | null;
  borough?: Borough | null;
}

export type EventTopic = 
  | "Zoning/Housing" 
  | "Education" 
  | "Budget/Finance" 
  | "Transportation" 
  | "Public Safety"
  | "Health/Social Services"
  | "Legislation/Policy"
  | "Environment"
  | "Other";

export type Borough = "Manhattan" | "Brooklyn" | "Queens" | "Bronx" | "Staten Island";
