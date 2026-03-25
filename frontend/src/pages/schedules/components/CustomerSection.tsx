import { X, Loader2, AlertCircle } from "lucide-react";
import ScoreRing from "../../../components/ScoreRing";
import { useRemoveCustomer } from "../hooks";
import type { ScheduleCustomerOut, EmployeeCustomerFamiliarity } from "../types";
import type { ApiError } from "../../../api/client";
import DroppableZone from "./DroppableZone";

interface CustomerSectionProps {
  scheduleId: string;
  customers: ScheduleCustomerOut[];
  assignError: ApiError | null;
  familiarityEntries: EmployeeCustomerFamiliarity[];
}

export default function CustomerSection({
  scheduleId,
  customers,
  assignError,
  familiarityEntries,
}: CustomerSectionProps) {
  const remove = useRemoveCustomer(scheduleId);

  // Compute average familiarity per customer
  const customerFamiliarity = new Map<string, number>();
  for (const cust of customers) {
    const entries = familiarityEntries.filter(
      (e) => e.customer_id === cust.customer_id,
    );
    if (entries.length > 0) {
      const avg =
        entries.reduce((sum, e) => sum + e.familiarity_score, 0) /
        entries.length;
      customerFamiliarity.set(cust.customer_id, avg);
    }
  }

  return (
    <DroppableZone
      id="customer-drop"
      zone="customers"
      accepts={["customer"]}
      className="card-glow bg-ocean/60 p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-600 text-moon">
          Kunder ({customers.length})
        </h3>
      </div>

      {assignError && (
        <div className="flex items-start gap-2 p-2 rounded-lg bg-coral/10 border border-coral/20 mb-3">
          <AlertCircle className="w-3.5 h-3.5 text-coral mt-0.5 shrink-0" />
          <p className="text-xs text-coral">{assignError.detail}</p>
        </div>
      )}

      <div className="space-y-1.5">
        {customers.map((sc) => {
          const famScore = customerFamiliarity.get(sc.customer_id);
          return (
            <div
              key={sc.customer_id}
              className="flex items-center gap-2 h-8 px-3 rounded-lg bg-mid/20"
            >
              <span className="text-sm text-mist/80 flex-1 truncate">
                {sc.customer.first_name} {sc.customer.last_name}
              </span>
              {famScore !== undefined && (
                <ScoreRing
                  score={famScore}
                  size={24}
                  strokeWidth={2}
                  label={`${Math.round(famScore * 100)}% kontinuitet`}
                />
              )}
              <button
                onClick={() => remove.mutate({ customer_id: sc.customer_id })}
                disabled={remove.isPending}
                className="text-sediment hover:text-coral transition-colors cursor-pointer disabled:opacity-50"
              >
                {remove.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <X className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          );
        })}
        {customers.length === 0 && (
          <p className="text-xs text-sediment py-1">
            Dra kunder hit eller sök nedan
          </p>
        )}
      </div>
    </DroppableZone>
  );
}
