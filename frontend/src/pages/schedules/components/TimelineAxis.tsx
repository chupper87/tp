import { useMemo } from "react";
import {
  timeToMinutes,
  shiftDurationMinutes,
} from "../constants";

interface TimelineAxisProps {
  shiftStart: string;
  shiftEnd: string;
  scheduleDate?: string;
}

export default function TimelineAxis({
  shiftStart,
  shiftEnd,
  scheduleDate,
}: TimelineAxisProps) {
  const ticks = useMemo(() => {
    const startMin = timeToMinutes(shiftStart);
    const totalMin = shiftDurationMinutes(shiftStart, shiftEnd);
    const result: { label: string; pct: number; isMajor: boolean }[] = [];

    for (let offset = 0; offset <= totalMin; offset += 30) {
      const min = (startMin + offset) % (24 * 60);
      const h = Math.floor(min / 60);
      const m = min % 60;
      const isMajor = m === 0;
      const label = isMajor ? String(h).padStart(2, "0") : "";
      const pct = (offset / totalMin) * 100;
      result.push({ label, pct, isMajor });
    }
    return result;
  }, [shiftStart, shiftEnd]);

  // "Now" indicator
  const nowPct = useMemo(() => {
    if (!scheduleDate) return null;
    const today = new Date().toISOString().split("T")[0];
    if (scheduleDate !== today) return null;

    const now = new Date();
    const nowMin = now.getHours() * 60 + now.getMinutes();
    const startMin = timeToMinutes(shiftStart);
    const totalMin = shiftDurationMinutes(shiftStart, shiftEnd);
    let offset = nowMin - startMin;
    if (offset < 0) offset += 24 * 60;
    if (offset > totalMin) return null;
    return (offset / totalMin) * 100;
  }, [shiftStart, shiftEnd, scheduleDate]);

  return (
    <div className="relative h-8 ml-[140px] mr-[80px]">
      {ticks.map((tick, i) => (
        <div
          key={i}
          className="absolute top-0 flex flex-col items-center"
          style={{ left: `${tick.pct}%` }}
        >
          <div
            className={`${
              tick.isMajor
                ? "h-3 w-px bg-reef-light/60"
                : "h-1.5 w-px bg-reef/30"
            }`}
          />
          {tick.label && (
            <span className="font-data text-[10px] text-sediment mt-0.5 -translate-x-1/2">
              {tick.label}
            </span>
          )}
        </div>
      ))}

      {/* Now indicator */}
      {nowPct !== null && (
        <div
          className="absolute top-0 bottom-0 w-px bg-glow z-10"
          style={{ left: `${nowPct}%` }}
        >
          <span className="absolute -top-0.5 left-1 text-[9px] font-data text-glow font-700">
            Nu
          </span>
          <div className="absolute top-0 w-1.5 h-1.5 rounded-full bg-glow -translate-x-[2px] animate-pulse" />
        </div>
      )}
    </div>
  );
}
