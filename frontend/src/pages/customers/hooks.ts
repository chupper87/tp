import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { CustomerMeasureOut } from "./types";

export function useCustomerMeasures(customerId: string) {
  return useQuery({
    queryKey: ["customers", customerId, "measures"],
    queryFn: () =>
      api.get<CustomerMeasureOut[]>(`/customers/${customerId}/measures`),
    enabled: !!customerId,
  });
}

export function useAddCustomerMeasure(customerId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      measure_id: string;
      frequency: string;
      days_of_week?: string[];
      occurrences_per_week?: number;
      customer_duration?: number;
      time_of_day?: string;
      time_flexibility?: string;
      customer_notes?: string;
    }) => api.post<CustomerMeasureOut>(`/customers/${customerId}/measures`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["customers", customerId, "measures"],
      });
    },
  });
}

export function useUpdateCustomerMeasure(customerId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      id: string;
      frequency?: string;
      days_of_week?: string[];
      occurrences_per_week?: number;
      customer_duration?: number;
      time_of_day?: string;
      time_flexibility?: string;
      customer_notes?: string;
    }) => {
      const { id, ...data } = payload;
      return api.patch<CustomerMeasureOut>(
        `/customers/${customerId}/measures/${id}`,
        data,
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["customers", customerId, "measures"],
      });
    },
  });
}

export function useRemoveCustomerMeasure(customerId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.delete(`/customers/${customerId}/measures/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["customers", customerId, "measures"],
      });
    },
  });
}
