export interface CustomerMeasureOut {
  id: string;
  customer_id: string;
  measure_id: string;
  frequency: string;
  days_of_week: string[] | null;
  occurrences_per_week: number | null;
  customer_duration: number | null;
  customer_notes: string | null;
  time_of_day: string | null;
  time_flexibility: string | null;
  created_at: string;
  updated_at: string;
  measure_name: string;
  measure_default_duration: number;
}
