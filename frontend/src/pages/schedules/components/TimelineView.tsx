import { AlertTriangle, Loader2 } from "lucide-react";
import { useScheduleTimeline, useDeleteCareVisit, useUpdateCareVisit } from "../hooks";
import TimelineAxis from "./TimelineAxis";
import EmployeeTimelineRow from "./EmployeeTimelineRow";

interface TimelineViewProps {
  scheduleId: string;
  scheduleDate: string;
  onCreateVisit: () => void;
}

export default function TimelineView({
  scheduleId,
  scheduleDate,
  onCreateVisit,
}: TimelineViewProps) {
  const { data: timeline, isLoading } = useScheduleTimeline(scheduleId);
  const deleteVisit = useDeleteCareVisit(scheduleId);
  const updateVisit = useUpdateCareVisit(scheduleId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 text-glow animate-spin" />
      </div>
    );
  }

  if (!timeline) return null;

  const shiftStart = timeline.shift_start.slice(0, 5);
  const shiftEnd = timeline.shift_end.slice(0, 5);

  const hasVisits = timeline.employees.some((e) => e.visits.length > 0);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-600 text-moon">Tidslinje</h3>
          {timeline.unassigned_measures_count > 0 && (
            <span className="flex items-center gap-1 text-[10px] text-sun px-2 py-0.5 rounded-full bg-sun/10 border border-sun/20">
              <AlertTriangle className="w-3 h-3" />
              {timeline.unassigned_measures_count} ej tidslagda
            </span>
          )}
        </div>
        <button
          onClick={onCreateVisit}
          className="px-3 py-1.5 rounded-lg bg-glow/10 text-glow text-xs font-600
            hover:bg-glow/20 border border-glow/20 transition-colors cursor-pointer"
        >
          + Nytt besök
        </button>
      </div>

      {/* Timeline container */}
      <div className="rounded-xl bg-ocean/40 border border-reef/30 overflow-visible">
        {/* Time axis */}
        <div className="border-b border-reef/20 bg-deep/60 rounded-t-xl">
          <TimelineAxis
            shiftStart={shiftStart}
            shiftEnd={shiftEnd}
            scheduleDate={scheduleDate}
          />
        </div>

        {/* Employee rows */}
        {timeline.employees.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-xs text-sediment">
              Inga anställda tilldelade
            </p>
          </div>
        ) : !hasVisits ? (
          <div className="px-4 py-8 text-center space-y-2">
            <p className="text-xs text-sediment">
              Inga besök skapade ännu
            </p>
            <button
              onClick={onCreateVisit}
              className="text-xs text-glow/70 hover:text-glow transition-colors cursor-pointer"
            >
              Skapa första besöket →
            </button>
          </div>
        ) : (
          <div>
            {timeline.employees.map((emp) => (
              <EmployeeTimelineRow
                key={emp.employee_id}
                employee={emp}
                shiftStart={shiftStart}
                shiftEnd={shiftEnd}
                onDeleteVisit={(id) => deleteVisit.mutate(id)}
                onUpdateVisitTime={(id, time) =>
                  updateVisit.mutate({ careVisitId: id, planned_start_time: time })
                }
                isUpdatingVisit={updateVisit.isPending}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
