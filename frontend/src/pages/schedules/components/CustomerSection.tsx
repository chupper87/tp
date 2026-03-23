import { X, Loader2, AlertCircle } from "lucide-react";
import { useRemoveCustomer } from "../hooks";
import type { ScheduleCustomerOut } from "../types";
import type { ApiError } from "../../../api/client";
import DroppableZone from "./DroppableZone";

interface CustomerSectionProps {
  scheduleId: string;
  customers: ScheduleCustomerOut[];
  assignError: ApiError | null;
}

export default function CustomerSection({
  scheduleId,
  customers,
  assignError,
}: CustomerSectionProps) {
  const remove = useRemoveCustomer(scheduleId);

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
        {customers.map((sc) => (
          <div
            key={sc.customer_id}
            className="flex items-center justify-between h-8 px-3 rounded-lg bg-mid/20"
          >
            <span className="text-sm text-mist/80">
              {sc.customer.first_name} {sc.customer.last_name}
            </span>
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
        ))}
        {customers.length === 0 && (
          <p className="text-xs text-sediment py-1">
            Dra kunder hit eller sök nedan
          </p>
        )}
      </div>
    </DroppableZone>
  );
}
