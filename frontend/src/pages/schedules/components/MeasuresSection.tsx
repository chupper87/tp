import { useState } from "react";
import { Trash2, Loader2, Pencil, Clock } from "lucide-react";
import { TIME_OF_DAY_LABELS } from "../constants";
import { useActiveMeasures, useRemoveMeasure } from "../hooks";
import type {
  ScheduleCustomerOut,
  ScheduleMeasureOut,
  MeasureBrief,
} from "../types";
import DroppableZone from "./DroppableZone";
import MeasureEditPopover from "./MeasureEditPopover";

interface MeasuresSectionProps {
  scheduleId: string;
  customers: ScheduleCustomerOut[];
  measures: ScheduleMeasureOut[];
}

export default function MeasuresSection({
  scheduleId,
  customers,
  measures,
}: MeasuresSectionProps) {
  const { data: allMeasures } = useActiveMeasures();

  // Group measures by customer
  const measuresByCustomer = new Map<string, ScheduleMeasureOut[]>();
  for (const m of measures) {
    const existing = measuresByCustomer.get(m.customer_id) ?? [];
    existing.push(m);
    measuresByCustomer.set(m.customer_id, existing);
  }

  // Build measure lookup
  const measureMap = new Map<string, MeasureBrief>();
  for (const m of allMeasures ?? []) {
    measureMap.set(m.id, m);
  }

  if (customers.length === 0) {
    return (
      <div className="card-glow rounded-xl bg-ocean/60 p-4">
        <h3 className="text-sm font-600 text-moon mb-3">Planerade insatser</h3>
        <p className="text-xs text-sediment">
          Tilldela kunder till schemat för att planera insatser
        </p>
      </div>
    );
  }

  return (
    <div className="card-glow rounded-xl bg-ocean/60 p-4">
      <h3 className="text-sm font-600 text-moon mb-4">Planerade insatser</h3>
      <div className="space-y-3">
        {customers.map((sc) => {
          const custMeasures = measuresByCustomer.get(sc.customer_id) ?? [];
          return (
            <CustomerMeasureBlock
              key={sc.customer_id}
              scheduleId={scheduleId}
              customer={sc}
              measures={custMeasures}
              measureMap={measureMap}
            />
          );
        })}
      </div>
    </div>
  );
}

// --- Per-customer block with drop zone ---

interface CustomerMeasureBlockProps {
  scheduleId: string;
  customer: ScheduleCustomerOut;
  measures: ScheduleMeasureOut[];
  measureMap: Map<string, MeasureBrief>;
}

function CustomerMeasureBlock({
  scheduleId,
  customer,
  measures,
  measureMap,
}: CustomerMeasureBlockProps) {
  return (
    <DroppableZone
      id={`measures-${customer.customer_id}`}
      zone="customer-measures"
      accepts={["measure"]}
      data={{ customerId: customer.customer_id }}
      className="rounded-lg bg-mid/20 p-3"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-600 text-mist/80">
          {customer.customer.first_name} {customer.customer.last_name}
        </span>
        <span className="text-[10px] text-sediment">
          {measures.length} {measures.length === 1 ? "insats" : "insatser"}
        </span>
      </div>

      <div className="space-y-1">
        {measures.map((m) => (
          <MeasureRow
            key={m.id}
            scheduleId={scheduleId}
            measure={m}
            measureInfo={measureMap.get(m.measure_id)}
          />
        ))}
        {measures.length === 0 && (
          <p className="text-xs text-sediment py-1">
            Dra insatser hit från panelen till höger
          </p>
        )}
      </div>
    </DroppableZone>
  );
}

// --- Single measure row ---

interface MeasureRowProps {
  scheduleId: string;
  measure: ScheduleMeasureOut;
  measureInfo?: MeasureBrief;
}

function MeasureRow({ scheduleId, measure, measureInfo }: MeasureRowProps) {
  const [editing, setEditing] = useState(false);
  const remove = useRemoveMeasure(scheduleId);

  const name = measureInfo?.name ?? "Okänd insats";
  const duration = measure.custom_duration ?? measureInfo?.default_duration ?? 0;
  const tod = measure.time_of_day;

  return (
    <div className="relative">
      <div className="flex items-center gap-2 h-8 px-2 rounded-md bg-deep/50 group">
        <span className="text-sm text-mist/80 flex-1 truncate">{name}</span>
        {measure.notes && (
          <span className="text-[10px] text-sediment truncate max-w-24" title={measure.notes}>
            {measure.notes}
          </span>
        )}
        <span className="flex items-center gap-1 text-[10px] text-sediment shrink-0">
          <Clock className="w-3 h-3" />
          {duration} min
        </span>
        {tod && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-mid/40 text-mist/50 shrink-0">
            {TIME_OF_DAY_LABELS[tod] ?? tod}
          </span>
        )}
        <button
          onClick={() => setEditing(true)}
          className="opacity-0 group-hover:opacity-100 text-sediment hover:text-moon transition-all cursor-pointer"
        >
          <Pencil className="w-3 h-3" />
        </button>
        <button
          onClick={() => remove.mutate({ id: measure.id })}
          disabled={remove.isPending}
          className="opacity-0 group-hover:opacity-100 text-sediment hover:text-coral transition-all cursor-pointer disabled:opacity-50"
        >
          {remove.isPending ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Trash2 className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {editing && (
        <MeasureEditPopover
          scheduleId={scheduleId}
          measure={measure}
          measureInfo={measureInfo}
          onClose={() => setEditing(false)}
        />
      )}
    </div>
  );
}
