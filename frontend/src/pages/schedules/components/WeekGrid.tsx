import {
  SHIFT_TYPES,
  SHIFT_LABELS,
  WEEKDAY_LABELS,
  getWeekDates,
  formatDateISO,
  isToday,
} from "../constants";
import type { ScheduleOut } from "../types";
import ShiftSlot from "./ShiftSlot";

interface WeekGridProps {
  weekStart: Date;
  schedules: ScheduleOut[];
  onCreateClick: (date: string, shiftType: string) => void;
}

export default function WeekGrid({
  weekStart,
  schedules,
  onCreateClick,
}: WeekGridProps) {
  const days = getWeekDates(weekStart);

  // Index schedules by "date|shift_type_or_custom"
  const scheduleMap = new Map<string, ScheduleOut>();
  const customByDate = new Map<string, ScheduleOut[]>();

  for (const s of schedules) {
    if (s.shift_type) {
      scheduleMap.set(`${s.date}|${s.shift_type}`, s);
    } else {
      const existing = customByDate.get(s.date) ?? [];
      existing.push(s);
      customByDate.set(s.date, existing);
    }
  }

  const hasCustom = customByDate.size > 0;

  return (
    <div className="card-glow rounded-xl bg-ocean/60 overflow-hidden">
      {/* Header row — day labels */}
      <div className="grid grid-cols-[80px_repeat(7,1fr)] border-b border-reef">
        <div className="px-3 py-2" />
        {days.map((day, i) => {
          const today = isToday(day);
          return (
            <div
              key={i}
              className="px-2 py-2 text-center border-l border-reef/30"
            >
              <p className="text-[10px] text-mist/50 uppercase tracking-wider font-600">
                {WEEKDAY_LABELS[i]}
              </p>
              <p
                className={`text-sm font-700 mt-0.5 ${
                  today
                    ? "text-glow"
                    : "text-moon"
                }`}
              >
                {day.getDate()}
              </p>
            </div>
          );
        })}
      </div>

      {/* Shift rows */}
      {SHIFT_TYPES.map((shift) => (
        <div
          key={shift}
          className="grid grid-cols-[80px_repeat(7,1fr)] border-b border-reef/20"
        >
          <div className="px-3 py-2 flex items-center">
            <span className="text-[10px] text-mist/40 uppercase tracking-wider font-600">
              {SHIFT_LABELS[shift]}
            </span>
          </div>
          {days.map((day, i) => {
            const dateStr = formatDateISO(day);
            const schedule = scheduleMap.get(`${dateStr}|${shift}`);
            return (
              <div
                key={i}
                className="px-1.5 py-1.5 border-l border-reef/20"
              >
                <ShiftSlot
                  schedule={schedule}
                  onCreateClick={() => onCreateClick(dateStr, shift)}
                />
              </div>
            );
          })}
        </div>
      ))}

      {/* Custom shift row */}
      {hasCustom && (
        <div className="grid grid-cols-[80px_repeat(7,1fr)]">
          <div className="px-3 py-2 flex items-center">
            <span className="text-[10px] text-mist/40 uppercase tracking-wider font-600">
              Anpassat
            </span>
          </div>
          {days.map((day, i) => {
            const dateStr = formatDateISO(day);
            const customs = customByDate.get(dateStr) ?? [];
            return (
              <div
                key={i}
                className="px-1.5 py-1.5 border-l border-reef/20 space-y-1"
              >
                {customs.map((s) => (
                  <ShiftSlot key={s.id} schedule={s} onCreateClick={() => {}} />
                ))}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
