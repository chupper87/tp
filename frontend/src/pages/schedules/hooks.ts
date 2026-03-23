import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import type {
  ScheduleOut,
  ScheduleDetailOut,
  EmployeeBrief,
  CustomerBrief,
  MeasureBrief,
} from "./types";

// --- Queries ---

export function useScheduleList(dateFrom: string, dateTo: string) {
  return useQuery({
    queryKey: ["schedules", { dateFrom, dateTo }],
    queryFn: () =>
      api.get<ScheduleOut[]>(
        `/schedules/?date_from=${dateFrom}&date_to=${dateTo}`,
      ),
  });
}

export function useScheduleDetail(id: string) {
  return useQuery({
    queryKey: ["schedules", id],
    queryFn: () => api.get<ScheduleDetailOut>(`/schedules/${id}`),
    enabled: !!id,
  });
}

export function useActiveEmployees() {
  return useQuery({
    queryKey: ["employees", { active: true }],
    queryFn: () => api.get<EmployeeBrief[]>("/employees/?is_active=true"),
    staleTime: 60_000,
  });
}

export function useActiveCustomers() {
  return useQuery({
    queryKey: ["customers", { active: true }],
    queryFn: () => api.get<CustomerBrief[]>("/customers/?is_active=true"),
    staleTime: 60_000,
  });
}

export function useActiveMeasures() {
  return useQuery({
    queryKey: ["measures", { active: true }],
    queryFn: () => api.get<MeasureBrief[]>("/measures/?is_active=true"),
    staleTime: 60_000,
  });
}

// --- Mutations ---

function useScheduleMutation<TPayload>(
  method: "post" | "patch" | "delete",
  pathFn: (payload: TPayload) => string,
  scheduleId?: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TPayload) => {
      const path = pathFn(payload);
      if (method === "delete") return api.delete(path);
      if (method === "patch") return api.patch(path, payload);
      return api.post(path, payload);
    },
    onSuccess: () => {
      if (scheduleId) {
        queryClient.invalidateQueries({ queryKey: ["schedules", scheduleId] });
      }
      queryClient.invalidateQueries({
        queryKey: ["schedules"],
        exact: false,
      });
    },
  });
}

export function useCreateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { date: string; shift_type?: string; custom_shift?: string }) =>
      api.post<ScheduleDetailOut>("/schedules/", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["schedules"],
        exact: false,
      });
    },
  });
}

export function useAssignEmployee(scheduleId: string) {
  return useScheduleMutation<{ employee_id: string }>(
    "post",
    () => `/schedules/${scheduleId}/employees`,
    scheduleId,
  );
}

export function useRemoveEmployee(scheduleId: string) {
  return useScheduleMutation<{ employee_id: string }>(
    "delete",
    (p) => `/schedules/${scheduleId}/employees/${p.employee_id}`,
    scheduleId,
  );
}

export function useAssignCustomer(scheduleId: string) {
  return useScheduleMutation<{ customer_id: string }>(
    "post",
    () => `/schedules/${scheduleId}/customers`,
    scheduleId,
  );
}

export function useRemoveCustomer(scheduleId: string) {
  return useScheduleMutation<{ customer_id: string }>(
    "delete",
    (p) => `/schedules/${scheduleId}/customers/${p.customer_id}`,
    scheduleId,
  );
}

export function useAddMeasure(scheduleId: string) {
  return useScheduleMutation<{
    customer_id: string;
    measure_id: string;
    time_of_day?: string;
    custom_duration?: number;
    notes?: string;
  }>("post", () => `/schedules/${scheduleId}/measures`, scheduleId);
}

export function useUpdateMeasure(scheduleId: string) {
  return useScheduleMutation<{
    id: string;
    time_of_day?: string;
    custom_duration?: number;
    notes?: string;
  }>("patch", (p) => `/schedules/${scheduleId}/measures/${p.id}`, scheduleId);
}

export function useRemoveMeasure(scheduleId: string) {
  return useScheduleMutation<{ id: string }>(
    "delete",
    (p) => `/schedules/${scheduleId}/measures/${p.id}`,
    scheduleId,
  );
}
