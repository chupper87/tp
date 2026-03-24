export interface ScheduleOut {
  id: string;
  date: string;
  shift_type: string | null;
  custom_shift: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduleEmployeeOut {
  employee_id: string;
  employee: { id: string; first_name: string; last_name: string };
}

export interface ScheduleCustomerOut {
  customer_id: string;
  customer: { id: string; first_name: string; last_name: string };
}

export interface ScheduleMeasureOut {
  id: string;
  schedule_id: string;
  customer_id: string;
  measure_id: string;
  time_of_day: string | null;
  custom_duration: number | null;
  notes: string | null;
  created_at: string;
}

export interface ScheduleDetailOut extends ScheduleOut {
  employees: ScheduleEmployeeOut[];
  customers: ScheduleCustomerOut[];
  measures: ScheduleMeasureOut[];
}

export interface EmployeeBrief {
  id: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
}

export interface CustomerBrief {
  id: string;
  first_name: string;
  last_name: string;
  care_level: string | null;
  is_active: boolean;
}

export interface MeasureBrief {
  id: string;
  name: string;
  default_duration: number;
  time_of_day: string | null;
  is_active: boolean;
}

// --- Planning intelligence types ---

export interface RequiredMeasure {
  customer_measure_id: string;
  measure_id: string;
  measure_name: string;
  frequency: string;
  time_of_day: string | null;
  expected_duration: number;
  is_required: boolean;
  is_fulfilled: boolean;
  schedule_measure_id: string | null;
}

export interface CustomerFulfillment {
  customer_id: string;
  customer_name: string;
  care_level: string | null;
  required_measures: RequiredMeasure[];
  total_required: number;
  total_fulfilled: number;
  total_duration_minutes: number;
}

export interface ScheduleFulfillment {
  schedule_id: string;
  customers: CustomerFulfillment[];
}

export interface ScheduleUtilization {
  schedule_id: string;
  shift_type: string | null;
  total_planned_minutes: number;
  total_capacity_minutes: number;
  employee_count: number;
  utilization_pct: number;
  per_employee_avg_minutes: number;
  per_employee_capacity_minutes: number;
}

export interface EmployeeCustomerFamiliarity {
  employee_id: string;
  employee_name: string;
  customer_id: string;
  customer_name: string;
  shared_schedules_last_60_days: number;
  familiarity_score: number;
}

export interface ContinuityPreview {
  schedule_id: string;
  average_familiarity: number;
  entries: EmployeeCustomerFamiliarity[];
}
