import { useState, useRef, useEffect } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { TIME_OF_DAY_LABELS } from "../constants";
import { useUpdateMeasure } from "../hooks";
import type { ScheduleMeasureOut, MeasureBrief } from "../types";
import type { ApiError } from "../../../api/client";

const TIME_OF_DAY_OPTIONS = ["morning", "midday", "afternoon", "evening", "night"] as const;

interface MeasureEditPopoverProps {
  scheduleId: string;
  measure: ScheduleMeasureOut;
  measureInfo?: MeasureBrief;
  onClose: () => void;
}

export default function MeasureEditPopover({
  scheduleId,
  measure,
  measureInfo,
  onClose,
}: MeasureEditPopoverProps) {
  const [timeOfDay, setTimeOfDay] = useState(measure.time_of_day ?? "");
  const [customDuration, setCustomDuration] = useState(
    measure.custom_duration ? String(measure.custom_duration) : "",
  );
  const [notes, setNotes] = useState(measure.notes ?? "");
  const popoverRef = useRef<HTMLDivElement>(null);

  const update = useUpdateMeasure(scheduleId);
  const error = update.error as ApiError | null;

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  function handleSave() {
    update.mutate(
      {
        id: measure.id,
        ...(timeOfDay ? { time_of_day: timeOfDay } : {}),
        ...(customDuration ? { custom_duration: parseInt(customDuration, 10) } : {}),
        ...(notes ? { notes } : {}),
      },
      { onSuccess: () => onClose() },
    );
  }

  return (
    <div
      ref={popoverRef}
      className="absolute z-20 top-full left-0 right-0 mt-1 p-3 rounded-lg bg-deep border border-reef shadow-xl space-y-2"
    >
      {error && (
        <div className="flex items-start gap-2 p-2 rounded-lg bg-coral/10 border border-coral/20">
          <AlertCircle className="w-3.5 h-3.5 text-coral mt-0.5 shrink-0" />
          <p className="text-xs text-coral">{error.detail}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1">
            Tid på dygnet
          </label>
          <select
            value={timeOfDay}
            onChange={(e) => setTimeOfDay(e.target.value)}
            className="w-full h-7 px-2 rounded-md bg-deep border border-reef text-xs text-moon focus:border-glow/50 focus:outline-none transition-colors"
          >
            <option value="">
              {measureInfo?.time_of_day
                ? TIME_OF_DAY_LABELS[measureInfo.time_of_day]
                : "Standard"}
            </option>
            {TIME_OF_DAY_OPTIONS.map((tod) => (
              <option key={tod} value={tod}>
                {TIME_OF_DAY_LABELS[tod]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1">
            Tid (min)
          </label>
          <input
            type="number"
            value={customDuration}
            onChange={(e) => setCustomDuration(e.target.value)}
            placeholder={measureInfo ? String(measureInfo.default_duration) : "—"}
            min={1}
            max={480}
            className="w-full h-7 px-2 rounded-md bg-deep border border-reef text-xs text-moon placeholder:text-sediment focus:border-glow/50 focus:outline-none transition-colors"
          />
        </div>
      </div>

      <div>
        <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1">
          Anteckningar
        </label>
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Valfritt"
          maxLength={200}
          className="w-full h-7 px-2 rounded-md bg-deep border border-reef text-xs text-moon placeholder:text-sediment focus:border-glow/50 focus:outline-none transition-colors"
        />
      </div>

      <div className="flex gap-2 pt-1">
        <button
          onClick={onClose}
          className="h-6 px-2.5 rounded-md border border-reef text-[10px] text-mist/60 hover:text-moon hover:border-reef-light transition-colors cursor-pointer"
        >
          Avbryt
        </button>
        <button
          onClick={handleSave}
          disabled={update.isPending}
          className="h-6 px-2.5 rounded-md bg-glow/90 hover:bg-glow text-abyss text-[10px] font-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 cursor-pointer"
        >
          {update.isPending ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            "Spara"
          )}
        </button>
      </div>
    </div>
  );
}
