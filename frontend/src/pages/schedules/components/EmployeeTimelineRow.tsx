import {
  timeToMinutes,
  timePositionPercent,
  durationWidthPercent,
  minutesToTime,
} from "../constants";
import type { EmployeeTimeline } from "../types";
import VisitBlock from "./VisitBlock";

interface EmployeeTimelineRowProps {
  employee: EmployeeTimeline;
  shiftStart: string;
  shiftEnd: string;
  onDeleteVisit?: (careVisitId: string) => void;
}

export default function EmployeeTimelineRow({
  employee,
  shiftStart,
  shiftEnd,
  onDeleteVisit,
}: EmployeeTimelineRowProps) {
  return (
    <div className="flex items-stretch group/row">
      {/* Employee name column */}
      <div className="w-[140px] shrink-0 flex items-center px-3 py-2 border-r border-reef/20">
        <div className="min-w-0">
          <p className="text-xs font-600 text-moon truncate">
            {employee.employee_name}
          </p>
          <p className="font-data text-[10px] text-sediment">
            {employee.total_visit_minutes}m planerat
          </p>
        </div>
      </div>

      {/* Timeline track */}
      <div className="flex-1 relative h-12 bg-deep/40 border-b border-reef/10">
        {/* Hour gridlines */}
        <HourGridlines shiftStart={shiftStart} shiftEnd={shiftEnd} />

        {/* Visit blocks */}
        {employee.visits.map((visit) => {
          const leftPct = timePositionPercent(
            visit.planned_start_time,
            shiftStart,
            shiftEnd,
          );
          const widthPct = durationWidthPercent(
            visit.duration,
            shiftStart,
            shiftEnd,
          );
          return (
            <VisitBlock
              key={visit.care_visit_id}
              visit={visit}
              leftPct={leftPct}
              widthPct={widthPct}
              onDelete={onDeleteVisit}
            />
          );
        })}

        {/* Gap indicators */}
        {employee.visits.map((visit, i) => {
          if (i + 1 >= employee.visits.length) return null;
          const nextVisit = employee.visits[i + 1];
          const endMin = timeToMinutes(visit.planned_end_time);
          const nextStartMin = timeToMinutes(nextVisit.planned_start_time);
          const gapMin = nextStartMin - endMin;
          if (gapMin <= 0) return null;

          const gapLeftPct = timePositionPercent(
            visit.planned_end_time,
            shiftStart,
            shiftEnd,
          );
          const gapWidthPct = durationWidthPercent(
            gapMin,
            shiftStart,
            shiftEnd,
          );

          return (
            <div
              key={`gap-${i}`}
              className="absolute top-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none"
              style={{
                left: `${gapLeftPct}%`,
                width: `${gapWidthPct}%`,
              }}
            >
              {gapMin >= 10 && (
                <span className="font-data text-[9px] text-sediment/60 bg-deep/60 px-1 rounded">
                  {gapMin}m
                </span>
              )}
              {gapMin >= 60 && (
                <span className="absolute -bottom-2.5 font-data text-[8px] text-sun/50">
                  ledig
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Utilization badge */}
      <div className="w-[80px] shrink-0 flex items-center justify-center">
        <span className="font-data text-[11px] text-mist/50">
          {minutesToTime(employee.total_visit_minutes)}
        </span>
      </div>
    </div>
  );
}

function HourGridlines({
  shiftStart,
  shiftEnd,
}: {
  shiftStart: string;
  shiftEnd: string;
}) {
  const startMin = timeToMinutes(shiftStart);
  const endMin = timeToMinutes(shiftEnd);
  const total = endMin > startMin ? endMin - startMin : 24 * 60 - startMin + endMin;

  const lines: number[] = [];
  for (let offset = 60; offset < total; offset += 60) {
    lines.push((offset / total) * 100);
  }

  return (
    <>
      {lines.map((pct, i) => (
        <div
          key={i}
          className="absolute top-0 bottom-0 w-px bg-reef/10"
          style={{ left: `${pct}%` }}
        />
      ))}
    </>
  );
}
