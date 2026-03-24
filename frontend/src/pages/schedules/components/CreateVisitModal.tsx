import { useState, useMemo } from "react";
import { X, Clock, Check } from "lucide-react";
import { useCreateCareVisit } from "../hooks";
import type {
  ScheduleEmployeeOut,
  ScheduleCustomerOut,
  ScheduleMeasureOut,
} from "../types";

interface CreateVisitModalProps {
  scheduleId: string;
  employees: ScheduleEmployeeOut[];
  customers: ScheduleCustomerOut[];
  measures: ScheduleMeasureOut[];
  onClose: () => void;
}

export default function CreateVisitModal({
  scheduleId,
  employees,
  customers,
  measures,
  onClose,
}: CreateVisitModalProps) {
  const createVisit = useCreateCareVisit(scheduleId);

  const [customerId, setCustomerId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [startTime, setStartTime] = useState("08:00");
  const [selectedMeasureIds, setSelectedMeasureIds] = useState<Set<string>>(
    new Set(),
  );
  const [durationOverride, setDurationOverride] = useState<string>("");

  // Measures for selected customer that aren't linked to a visit
  const availableMeasures = useMemo(() => {
    if (!customerId) return [];
    return measures.filter((m) => m.customer_id === customerId);
  }, [measures, customerId]);

  // Auto-computed duration from selected measures
  const computedDuration = useMemo(() => {
    let total = 0;
    for (const m of availableMeasures) {
      if (selectedMeasureIds.has(m.id)) {
        total += m.custom_duration ?? 0;
      }
    }
    return total;
  }, [availableMeasures, selectedMeasureIds]);

  const finalDuration = durationOverride
    ? parseInt(durationOverride, 10)
    : computedDuration;

  function toggleMeasure(id: string) {
    setSelectedMeasureIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function selectAllMeasures() {
    setSelectedMeasureIds(new Set(availableMeasures.map((m) => m.id)));
  }

  async function handleSubmit() {
    if (!customerId || !employeeId || finalDuration <= 0) return;

    createVisit.mutate(
      {
        schedule_id: scheduleId,
        customer_id: customerId,
        planned_start_time: startTime + ":00",
        duration: finalDuration,
        employees: [{ employee_id: employeeId, is_primary: true }],
        schedule_measure_ids: Array.from(selectedMeasureIds),
      },
      {
        onSuccess: () => onClose(),
      },
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-abyss/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md rounded-2xl bg-deep border border-reef/50 shadow-[0_16px_64px_rgba(0,0,0,0.6)] animate-fade-up">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-reef/20">
          <h2 className="font-display text-base font-700 text-moon">
            Nytt besök
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-mid/30 text-sediment hover:text-moon transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-4">
          {/* Customer */}
          <div>
            <label className="block text-[10px] text-sediment uppercase tracking-wider font-600 mb-1.5">
              Kund
            </label>
            <select
              value={customerId}
              onChange={(e) => {
                setCustomerId(e.target.value);
                setSelectedMeasureIds(new Set());
              }}
              className="w-full px-3 py-2 rounded-lg bg-ocean/60 border border-reef/30 text-sm text-moon
                focus:outline-none focus:border-glow/50 transition-colors"
            >
              <option value="">Välj kund...</option>
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.customer.first_name} {c.customer.last_name}
                </option>
              ))}
            </select>
          </div>

          {/* Employee */}
          <div>
            <label className="block text-[10px] text-sediment uppercase tracking-wider font-600 mb-1.5">
              Anställd
            </label>
            <select
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-ocean/60 border border-reef/30 text-sm text-moon
                focus:outline-none focus:border-glow/50 transition-colors"
            >
              <option value="">Välj anställd...</option>
              {employees.map((emp) => (
                <option key={emp.employee_id} value={emp.employee_id}>
                  {emp.employee.first_name} {emp.employee.last_name}
                </option>
              ))}
            </select>
          </div>

          {/* Start time */}
          <div>
            <label className="block text-[10px] text-sediment uppercase tracking-wider font-600 mb-1.5">
              Starttid
            </label>
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              step={900}
              className="w-full px-3 py-2 rounded-lg bg-ocean/60 border border-reef/30 text-sm text-moon font-data
                focus:outline-none focus:border-glow/50 transition-colors"
            />
          </div>

          {/* Measures */}
          {customerId && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[10px] text-sediment uppercase tracking-wider font-600">
                  Insatser
                </label>
                {availableMeasures.length > 0 && (
                  <button
                    onClick={selectAllMeasures}
                    className="text-[10px] text-glow/60 hover:text-glow transition-colors cursor-pointer"
                  >
                    Välj alla
                  </button>
                )}
              </div>
              {availableMeasures.length === 0 ? (
                <p className="text-xs text-sediment py-1">
                  Inga insatser för denna kund
                </p>
              ) : (
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {availableMeasures.map((m) => {
                    const selected = selectedMeasureIds.has(m.id);
                    return (
                      <button
                        key={m.id}
                        onClick={() => toggleMeasure(m.id)}
                        className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left transition-colors cursor-pointer ${
                          selected
                            ? "bg-glow/10 border border-glow/30"
                            : "bg-ocean/40 border border-reef/20 hover:border-reef/40"
                        }`}
                      >
                        <div
                          className={`w-4 h-4 rounded flex items-center justify-center shrink-0 ${
                            selected
                              ? "bg-glow text-abyss"
                              : "bg-mid/40 border border-reef/30"
                          }`}
                        >
                          {selected && <Check className="w-2.5 h-2.5" />}
                        </div>
                        <span className="text-xs text-mist/80 flex-1 truncate">
                          {m.notes || `Insats`}
                        </span>
                        <span className="font-data text-[10px] text-sediment flex items-center gap-0.5">
                          <Clock className="w-2.5 h-2.5" />
                          {m.custom_duration ?? "?"}m
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Duration */}
          <div>
            <label className="block text-[10px] text-sediment uppercase tracking-wider font-600 mb-1.5">
              Längd (minuter)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={durationOverride || ""}
                onChange={(e) => setDurationOverride(e.target.value)}
                placeholder={String(computedDuration || 30)}
                min={1}
                className="w-24 px-3 py-2 rounded-lg bg-ocean/60 border border-reef/30 text-sm text-moon font-data
                  focus:outline-none focus:border-glow/50 transition-colors"
              />
              {computedDuration > 0 && !durationOverride && (
                <span className="text-[10px] text-mist/40">
                  {computedDuration}m från insatser
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-reef/20">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-600 text-mist/60
              hover:bg-mid/30 transition-colors cursor-pointer"
          >
            Avbryt
          </button>
          <button
            onClick={handleSubmit}
            disabled={
              !customerId ||
              !employeeId ||
              finalDuration <= 0 ||
              createVisit.isPending
            }
            className="px-4 py-2 rounded-lg bg-glow/15 text-glow text-xs font-600
              hover:bg-glow/25 border border-glow/20 transition-colors
              disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            {createVisit.isPending ? "Skapar..." : "Skapa besök"}
          </button>
        </div>

        {/* Error */}
        {createVisit.isError && (
          <div className="px-5 py-2 text-xs text-coral border-t border-reef/15">
            {(createVisit.error as Error)?.message ?? "Något gick fel"}
          </div>
        )}
      </div>
    </div>
  );
}
