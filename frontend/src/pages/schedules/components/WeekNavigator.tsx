import { ChevronLeft, ChevronRight } from "lucide-react";
import { getISOWeekNumber } from "../constants";

interface WeekNavigatorProps {
  weekStart: Date;
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
}

export default function WeekNavigator({
  weekStart,
  onPrev,
  onNext,
  onToday,
}: WeekNavigatorProps) {
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  const weekNum = getISOWeekNumber(weekStart);

  const fmt = (d: Date) =>
    d.toLocaleDateString("sv-SE", { day: "numeric", month: "short" });
  const year = weekEnd.getFullYear();

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onPrev}
        className="w-8 h-8 rounded-lg bg-ocean border border-reef flex items-center justify-center text-mist/60 hover:text-moon hover:border-reef-light transition-colors cursor-pointer"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      <button
        onClick={onNext}
        className="w-8 h-8 rounded-lg bg-ocean border border-reef flex items-center justify-center text-mist/60 hover:text-moon hover:border-reef-light transition-colors cursor-pointer"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
      <span className="font-display font-600 text-moon text-sm">
        Vecka {weekNum}:
        <span className="text-mist/60 font-400 ml-1.5">
          {fmt(weekStart)} – {fmt(weekEnd)} {year}
        </span>
      </span>
      <button
        onClick={onToday}
        className="ml-2 px-3 h-7 rounded-md bg-mid/60 border border-reef text-xs text-mist/70 hover:text-moon hover:border-reef-light transition-colors cursor-pointer"
      >
        Idag
      </button>
    </div>
  );
}
