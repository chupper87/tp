import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import type { ScheduleOut } from "../types";
import { SHIFT_LABELS, SHIFT_COLORS } from "../constants";

interface ShiftSlotProps {
  schedule?: ScheduleOut;
  onCreateClick: () => void;
}

export default function ShiftSlot({ schedule, onCreateClick }: ShiftSlotProps) {
  if (!schedule) {
    return (
      <button
        onClick={onCreateClick}
        className="w-full h-full min-h-[48px] rounded-lg border border-dashed border-reef/30 hover:border-reef-light hover:bg-mid/10 transition-all group flex items-center justify-center cursor-pointer"
      >
        <Plus className="w-3.5 h-3.5 text-sediment opacity-0 group-hover:opacity-100 transition-opacity" />
      </button>
    );
  }

  const shiftKey = schedule.shift_type ?? "custom";
  const label = schedule.shift_type
    ? SHIFT_LABELS[schedule.shift_type]
    : schedule.custom_shift ?? "Anpassat";
  const colors = SHIFT_COLORS[shiftKey] ?? SHIFT_COLORS.custom;

  return (
    <Link
      to={`/schedules/${schedule.id}`}
      className="block w-full min-h-[48px] rounded-lg bg-ocean/60 border border-reef/40 hover:border-reef-light hover:bg-mid/20 transition-all p-2"
    >
      <span
        className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-600 border ${colors}`}
      >
        {label}
      </span>
    </Link>
  );
}
