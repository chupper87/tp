import { useState } from "react";
import {
  Check,
  Plus,
  Minus,
  Loader2,
  Pencil,
  Trash2,
  Clock,
} from "lucide-react";
import { TIME_OF_DAY_LABELS } from "../constants";
import { useAddMeasure, useRemoveMeasure } from "../hooks";
import type {
  RequiredMeasure,
  CustomerFulfillment,
  ScheduleMeasureOut,
} from "../types";
import DroppableZone from "./DroppableZone";
import MeasureEditPopover from "./MeasureEditPopover";
import type { MeasureBrief } from "../types";

const CARE_LEVEL_COLORS: Record<string, string> = {
  low: "bg-kelp/20 text-kelp",
  medium: "bg-sun/20 text-sun",
  high: "bg-coral/20 text-coral",
};

const CARE_LEVEL_LABELS: Record<string, string> = {
  low: "Låg",
  medium: "Medel",
  high: "Hög",
};

const FREQUENCY_LABELS: Record<string, string> = {
  daily: "Daglig",
  weekly: "Veckovis",
  biweekly: "Varannan vecka",
  monthly: "Månadsvis",
};

interface FulfillmentCardProps {
  scheduleId: string;
  customer: CustomerFulfillment;
  scheduleMeasures: ScheduleMeasureOut[];
  measureMap: Map<string, MeasureBrief>;
}

function statusBorder(fulfilled: number, required: number): string {
  if (required === 0) return "border-l-reef";
  if (fulfilled >= required) return "border-l-kelp";
  if (fulfilled > 0) return "border-l-sun";
  return "border-l-coral";
}

function statusBadge(
  fulfilled: number,
  required: number,
): { bg: string; text: string } {
  if (required === 0) return { bg: "bg-reef/20", text: "text-mist/50" };
  if (fulfilled >= required)
    return { bg: "bg-kelp/15", text: "text-kelp" };
  if (fulfilled > 0) return { bg: "bg-sun/15", text: "text-sun" };
  return { bg: "bg-coral/15", text: "text-coral" };
}

export default function FulfillmentCard({
  scheduleId,
  customer,
  scheduleMeasures,
  measureMap,
}: FulfillmentCardProps) {
  const addMeasure = useAddMeasure(scheduleId);
  const border = statusBorder(customer.total_fulfilled, customer.total_required);
  const badge = statusBadge(customer.total_fulfilled, customer.total_required);

  // Build a lookup for schedule measures by measure_id for this customer
  const smByMeasureId = new Map<string, ScheduleMeasureOut>();
  for (const sm of scheduleMeasures) {
    if (sm.customer_id === customer.customer_id) {
      smByMeasureId.set(sm.measure_id, sm);
    }
  }

  // Separate into required (hard), soft, and manually-added
  const hardMeasures = customer.required_measures.filter((m) => m.is_required);
  const softMeasures = customer.required_measures.filter(
    (m) => !m.is_required,
  );

  // Find manually-added measures (on schedule but not in care plan)
  const carePlanMeasureIds = new Set(
    customer.required_measures.map((m) => m.measure_id),
  );
  const manualMeasures = scheduleMeasures.filter(
    (sm) =>
      sm.customer_id === customer.customer_id &&
      !carePlanMeasureIds.has(sm.measure_id),
  );

  return (
    <DroppableZone
      id={`measures-${customer.customer_id}`}
      zone="customer-measures"
      accepts={["measure"]}
      data={{ customerId: customer.customer_id }}
      className={`rounded-xl bg-ocean/60 border border-reef/40 border-l-[3px] ${border} overflow-hidden`}
    >
      {/* Header */}
      <div className="px-3.5 py-2.5 border-b border-reef/20 flex items-center gap-2">
        <span className="text-sm font-600 text-moon flex-1">
          {customer.customer_name}
        </span>
        {customer.care_level && (
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded font-600 ${CARE_LEVEL_COLORS[customer.care_level] ?? "bg-mid/40 text-mist/50"}`}
          >
            {CARE_LEVEL_LABELS[customer.care_level] ?? customer.care_level}
          </span>
        )}
        <span
          className={`font-data text-xs font-600 px-2 py-0.5 rounded ${badge.bg} ${badge.text}`}
        >
          {customer.total_fulfilled}/{customer.total_required}
        </span>
      </div>

      {/* Measure rows */}
      <div className="px-2 py-1.5 space-y-0.5">
        {/* Hard requirements */}
        {hardMeasures.map((rm) => (
          <RequiredMeasureRow
            key={rm.customer_measure_id}
            rm={rm}
            scheduleId={scheduleId}
            customerId={customer.customer_id}
            scheduleMeasure={smByMeasureId.get(rm.measure_id)}
            measureInfo={measureMap.get(rm.measure_id)}
            onAutoAdd={() =>
              addMeasure.mutate({
                customer_id: customer.customer_id,
                measure_id: rm.measure_id,
                time_of_day: rm.time_of_day ?? undefined,
              })
            }
            isAdding={addMeasure.isPending}
          />
        ))}

        {/* Soft requirements */}
        {softMeasures.map((rm) => (
          <SoftMeasureRow
            key={rm.customer_measure_id}
            rm={rm}
            scheduleMeasure={smByMeasureId.get(rm.measure_id)}
            scheduleId={scheduleId}
            customerId={customer.customer_id}
            measureInfo={measureMap.get(rm.measure_id)}
            onAutoAdd={() =>
              addMeasure.mutate({
                customer_id: customer.customer_id,
                measure_id: rm.measure_id,
                time_of_day: rm.time_of_day ?? undefined,
              })
            }
            isAdding={addMeasure.isPending}
          />
        ))}

        {/* Manually added (not from care plan) */}
        {manualMeasures.map((sm) => (
          <ManualMeasureRow
            key={sm.id}
            scheduleId={scheduleId}
            measure={sm}
            measureInfo={measureMap.get(sm.measure_id)}
          />
        ))}

        {/* Empty state */}
        {hardMeasures.length === 0 &&
          softMeasures.length === 0 &&
          manualMeasures.length === 0 && (
            <p className="text-xs text-sediment py-2 px-1.5">
              Ingen vårdplan — dra insatser hit
            </p>
          )}
      </div>
    </DroppableZone>
  );
}

// --- Fulfilled / Missing measure row ---

interface RequiredMeasureRowProps {
  rm: RequiredMeasure;
  scheduleId: string;
  customerId: string;
  scheduleMeasure?: ScheduleMeasureOut;
  measureInfo?: MeasureBrief;
  onAutoAdd: () => void;
  isAdding: boolean;
}

function RequiredMeasureRow({
  rm,
  scheduleId,
  scheduleMeasure,
  measureInfo,
  onAutoAdd,
  isAdding,
}: RequiredMeasureRowProps) {
  const [editing, setEditing] = useState(false);
  const removeMeasure = useRemoveMeasure(scheduleId);

  if (rm.is_fulfilled && scheduleMeasure) {
    // Fulfilled row
    const duration =
      scheduleMeasure.custom_duration ?? rm.expected_duration;
    return (
      <div className="relative">
        <div className="flex items-center gap-2 h-8 px-2 rounded-md group hover:bg-deep/30 transition-colors">
          <div className="w-5 h-5 rounded-full bg-kelp/20 flex items-center justify-center shrink-0">
            <Check className="w-3 h-3 text-kelp" />
          </div>
          <span className="text-sm text-mist/70 flex-1 truncate">
            {rm.measure_name}
          </span>
          <span className="flex items-center gap-0.5 font-data text-[11px] text-sediment shrink-0">
            <Clock className="w-3 h-3" />
            {duration}m
          </span>
          {rm.time_of_day && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-mid/40 text-mist/50 shrink-0">
              {TIME_OF_DAY_LABELS[rm.time_of_day] ?? rm.time_of_day}
            </span>
          )}
          <button
            onClick={() => setEditing(true)}
            className="opacity-0 group-hover:opacity-100 text-sediment hover:text-moon transition-all cursor-pointer"
          >
            <Pencil className="w-3 h-3" />
          </button>
          <button
            onClick={() =>
              removeMeasure.mutate({ id: scheduleMeasure.id })
            }
            disabled={removeMeasure.isPending}
            className="opacity-0 group-hover:opacity-100 text-sediment hover:text-coral transition-all cursor-pointer disabled:opacity-50"
          >
            {removeMeasure.isPending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Trash2 className="w-3 h-3" />
            )}
          </button>
        </div>
        {editing && scheduleMeasure && (
          <MeasureEditPopover
            scheduleId={scheduleId}
            measure={scheduleMeasure}
            measureInfo={measureInfo}
            onClose={() => setEditing(false)}
          />
        )}
      </div>
    );
  }

  // Missing row — clickable to auto-add
  return (
    <button
      onClick={onAutoAdd}
      disabled={isAdding}
      className="w-full flex items-center gap-2 h-8 px-2 rounded-md bg-coral/[0.04] hover:bg-coral/[0.08] transition-colors group cursor-pointer disabled:opacity-50"
    >
      <div className="w-5 h-5 rounded-full bg-coral/15 flex items-center justify-center shrink-0 group-hover:bg-coral/25 transition-colors">
        {isAdding ? (
          <Loader2 className="w-3 h-3 text-coral animate-spin" />
        ) : (
          <Plus className="w-3 h-3 text-coral" />
        )}
      </div>
      <span className="text-sm text-coral/80 flex-1 truncate text-left">
        {rm.measure_name}
      </span>
      <span className="flex items-center gap-0.5 font-data text-[11px] text-coral/50 shrink-0">
        <Clock className="w-3 h-3" />
        {rm.expected_duration}m
      </span>
      {rm.time_of_day && (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-coral/10 text-coral/60 shrink-0">
          {TIME_OF_DAY_LABELS[rm.time_of_day] ?? rm.time_of_day}
        </span>
      )}
      <span className="text-[10px] text-coral/50 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
        Lägg till
      </span>
    </button>
  );
}

// --- Soft requirement row ---

interface SoftMeasureRowProps {
  rm: RequiredMeasure;
  scheduleMeasure?: ScheduleMeasureOut;
  scheduleId: string;
  customerId: string;
  measureInfo?: MeasureBrief;
  onAutoAdd: () => void;
  isAdding: boolean;
}

function SoftMeasureRow({
  rm,
  scheduleMeasure,
  scheduleId,
  measureInfo,
  onAutoAdd,
  isAdding,
}: SoftMeasureRowProps) {
  const [editing, setEditing] = useState(false);
  const removeMeasure = useRemoveMeasure(scheduleId);

  if (rm.is_fulfilled && scheduleMeasure) {
    // Fulfilled soft requirement — same as hard but with a subtle indicator
    const duration =
      scheduleMeasure.custom_duration ?? rm.expected_duration;
    return (
      <div className="relative">
        <div className="flex items-center gap-2 h-8 px-2 rounded-md group hover:bg-deep/30 transition-colors">
          <div className="w-5 h-5 rounded-full bg-kelp/20 flex items-center justify-center shrink-0">
            <Check className="w-3 h-3 text-kelp" />
          </div>
          <span className="text-sm text-mist/70 flex-1 truncate">
            {rm.measure_name}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-mid/20 text-mist/30 shrink-0 italic">
            {FREQUENCY_LABELS[rm.frequency] ?? rm.frequency}
          </span>
          <span className="flex items-center gap-0.5 font-data text-[11px] text-sediment shrink-0">
            <Clock className="w-3 h-3" />
            {duration}m
          </span>
          <button
            onClick={() => setEditing(true)}
            className="opacity-0 group-hover:opacity-100 text-sediment hover:text-moon transition-all cursor-pointer"
          >
            <Pencil className="w-3 h-3" />
          </button>
          <button
            onClick={() =>
              removeMeasure.mutate({ id: scheduleMeasure.id })
            }
            disabled={removeMeasure.isPending}
            className="opacity-0 group-hover:opacity-100 text-sediment hover:text-coral transition-all cursor-pointer disabled:opacity-50"
          >
            {removeMeasure.isPending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Trash2 className="w-3 h-3" />
            )}
          </button>
        </div>
        {editing && (
          <MeasureEditPopover
            scheduleId={scheduleId}
            measure={scheduleMeasure}
            measureInfo={measureInfo}
            onClose={() => setEditing(false)}
          />
        )}
      </div>
    );
  }

  // Unfulfilled soft — quietest: amber tilde, italic frequency label
  return (
    <button
      onClick={onAutoAdd}
      disabled={isAdding}
      className="w-full flex items-center gap-2 h-8 px-2 rounded-md hover:bg-sun/[0.04] transition-colors group cursor-pointer disabled:opacity-50"
    >
      <div className="w-5 h-5 rounded-full bg-sun/10 flex items-center justify-center shrink-0">
        {isAdding ? (
          <Loader2 className="w-3 h-3 text-sun/60 animate-spin" />
        ) : (
          <Minus className="w-3 h-3 text-sun/50" />
        )}
      </div>
      <span className="text-sm text-mist/40 flex-1 truncate text-left italic">
        {rm.measure_name}
      </span>
      <span className="text-[10px] px-1.5 py-0.5 rounded bg-mid/20 text-mist/30 shrink-0 italic">
        {FREQUENCY_LABELS[rm.frequency] ?? rm.frequency}
      </span>
      <span className="flex items-center gap-0.5 font-data text-[11px] text-mist/30 shrink-0">
        <Clock className="w-3 h-3" />
        {rm.expected_duration}m
      </span>
    </button>
  );
}

// --- Manually added measure (not from care plan) ---

interface ManualMeasureRowProps {
  scheduleId: string;
  measure: ScheduleMeasureOut;
  measureInfo?: MeasureBrief;
}

function ManualMeasureRow({
  scheduleId,
  measure,
  measureInfo,
}: ManualMeasureRowProps) {
  const [editing, setEditing] = useState(false);
  const removeMeasure = useRemoveMeasure(scheduleId);
  const name = measureInfo?.name ?? "Okänd insats";
  const duration =
    measure.custom_duration ?? measureInfo?.default_duration ?? 0;

  return (
    <div className="relative">
      <div className="flex items-center gap-2 h-8 px-2 rounded-md group hover:bg-deep/30 transition-colors">
        <div className="w-5 h-5 rounded-full bg-current/20 flex items-center justify-center shrink-0">
          <Check className="w-3 h-3 text-current" />
        </div>
        <span className="text-sm text-mist/70 flex-1 truncate">{name}</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-current/10 text-current/60 shrink-0">
          Manuell
        </span>
        <span className="flex items-center gap-0.5 font-data text-[11px] text-sediment shrink-0">
          <Clock className="w-3 h-3" />
          {duration}m
        </span>
        {measure.time_of_day && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-mid/40 text-mist/50 shrink-0">
            {TIME_OF_DAY_LABELS[measure.time_of_day] ?? measure.time_of_day}
          </span>
        )}
        <button
          onClick={() => setEditing(true)}
          className="opacity-0 group-hover:opacity-100 text-sediment hover:text-moon transition-all cursor-pointer"
        >
          <Pencil className="w-3 h-3" />
        </button>
        <button
          onClick={() => removeMeasure.mutate({ id: measure.id })}
          disabled={removeMeasure.isPending}
          className="opacity-0 group-hover:opacity-100 text-sediment hover:text-coral transition-all cursor-pointer disabled:opacity-50"
        >
          {removeMeasure.isPending ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Trash2 className="w-3 h-3" />
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
