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
