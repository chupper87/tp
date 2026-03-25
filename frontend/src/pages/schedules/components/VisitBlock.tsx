import { useState } from "react";
import { Clock, Trash2, X, Loader2 } from "lucide-react";
import { timeToMinutes, minutesToTime } from "../constants";
import type { TimelineVisit } from "../types";

interface VisitBlockProps {
  visit: TimelineVisit;
  leftPct: number;
  widthPct: number;
  onDelete?: (careVisitId: string) => void;
  onUpdateTime?: (careVisitId: string, newStartTime: string) => void;
  isUpdating?: boolean;
}

const STATUS_STYLES: Record<string, string> = {
  planned: "bg-glow/8 border-glow/30 hover:bg-glow/14 border-l-glow",
  completed: "bg-kelp/8 border-kelp/30 hover:bg-kelp/14 border-l-kelp",
  canceled: "bg-coral/8 border-coral/30 hover:bg-coral/14 border-l-coral opacity-60",
};

export default function VisitBlock({
  visit,
  leftPct,
  widthPct,
  onDelete,
  onUpdateTime,
  isUpdating,
}: VisitBlockProps) {
  const [expanded, setExpanded] = useState(false);
  const startStr = minutesToTime(timeToMinutes(visit.planned_start_time));
  const endStr = minutesToTime(timeToMinutes(visit.planned_end_time));

  const [editingTime, setEditingTime] = useState(false);
  const [timeValue, setTimeValue] = useState(startStr);

  const style = STATUS_STYLES[visit.status] ?? STATUS_STYLES.planned;
  const totalMeasureDuration = visit.measures.reduce(
    (acc, m) => acc + m.duration,
    0,
  );

  function handleTimeSave() {
    if (timeValue !== startStr && onUpdateTime) {
      onUpdateTime(visit.care_visit_id, timeValue + ":00");
    }
    setEditingTime(false);
  }

  return (
    <>
      <div
        className={`absolute top-1 bottom-1 rounded-lg border border-l-[3px] cursor-pointer
          transition-all duration-200 group overflow-hidden ${style}`}
        style={{
          left: `${leftPct}%`,
          width: `${Math.max(widthPct, 2)}%`,
        }}
        onClick={() => setExpanded(!expanded)}
        title={`${visit.customer_name} ${startStr}–${endStr}`}
      >
        <div className="px-2 py-1 h-full flex flex-col justify-center min-w-0">
          {/* Customer name */}
          <div className="flex items-center gap-1 min-w-0">
            <span className="text-[11px] font-600 text-moon truncate">
              {visit.customer_name}
            </span>
          </div>
          {/* Time + measures summary */}
          <div className="flex items-center gap-1.5 min-w-0">
            <span className="font-data text-[9px] text-mist/60 shrink-0">
              {startStr}
            </span>
            {widthPct > 8 && (
              <span className="text-[9px] text-sediment truncate">
                {visit.measures
                  .map((m) => m.measure_name)
                  .join(", ")}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Expanded detail popover */}
      {expanded && (
        <div
          className="absolute z-30 top-full mt-1 rounded-xl bg-deep border border-reef/60
            shadow-[0_8px_32px_rgba(0,0,0,0.6)] min-w-[240px] max-w-[320px]"
          style={{ left: `${leftPct}%` }}
        >
          <div className="px-3.5 py-2.5 border-b border-reef/20 flex items-center justify-between">
            <div>
              <p className="text-sm font-600 text-moon">
                {visit.customer_name}
              </p>
              {/* Editable time row */}
              {editingTime ? (
                <div className="flex items-center gap-1.5 mt-1">
                  <input
                    type="time"
                    value={timeValue}
                    onChange={(e) => setTimeValue(e.target.value)}
                    step={900}
                    autoFocus
                    className="w-[90px] px-1.5 py-0.5 rounded-md bg-ocean/60 border border-reef/40 text-xs text-moon font-data
                      focus:outline-none focus:border-glow/50 transition-colors"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleTimeSave();
                      if (e.key === "Escape") {
                        setTimeValue(startStr);
                        setEditingTime(false);
                      }
                    }}
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTimeSave();
                    }}
                    disabled={isUpdating}
                    className="px-2 py-0.5 rounded-md bg-glow/15 text-glow text-[10px] font-600
                      hover:bg-glow/25 border border-glow/20 transition-colors cursor-pointer
                      disabled:opacity-50"
                  >
                    {isUpdating ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      "Spara"
                    )}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setTimeValue(startStr);
                      setEditingTime(false);
                    }}
                    className="text-sediment hover:text-moon text-[10px] transition-colors cursor-pointer"
                  >
                    Avbryt
                  </button>
                </div>
              ) : (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setTimeValue(startStr);
                    setEditingTime(true);
                  }}
                  className="font-data text-xs text-mist/60 hover:text-glow transition-colors cursor-pointer mt-0.5"
                  title="Klicka för att ändra tid"
                >
                  {startStr} – {endStr} · {visit.duration} min
                </button>
              )}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(false);
                setEditingTime(false);
              }}
              className="p-1 rounded-md hover:bg-mid/30 text-sediment hover:text-moon transition-colors cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="px-3.5 py-2 space-y-1">
            {visit.measures.map((m) => (
              <div
                key={m.schedule_measure_id}
                className="flex items-center justify-between text-xs"
              >
                <span className="text-mist/70">{m.measure_name}</span>
                <span className="font-data text-sediment">
                  {m.duration}m
                </span>
              </div>
            ))}
            {visit.measures.length > 0 && (
              <div className="flex items-center justify-between text-xs pt-1 border-t border-reef/15">
                <span className="text-mist/50 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Totalt
                </span>
                <span className="font-data text-moon font-600">
                  {totalMeasureDuration}m
                </span>
              </div>
            )}
          </div>

          {onDelete && (
            <div className="px-3.5 py-2 border-t border-reef/15">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(visit.care_visit_id);
                  setExpanded(false);
                }}
                className="flex items-center gap-1.5 text-[11px] text-coral/70 hover:text-coral transition-colors cursor-pointer"
              >
                <Trash2 className="w-3 h-3" />
                Ta bort besök
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
