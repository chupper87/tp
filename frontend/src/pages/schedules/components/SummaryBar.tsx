import { ListChecks, Clock, Users } from "lucide-react";
import ScoreRing from "../../../components/ScoreRing";

interface SummaryBarProps {
  totalRequired: number;
  totalFulfilled: number;
  totalPlannedMinutes: number;
  totalCapacityMinutes: number;
  utilizationPct: number;
  averageFamiliarity: number;
  employeeCount: number;
}

function utilizationColor(pct: number): string {
  if (pct > 100) return "var(--color-coral)";
  if (pct >= 80) return "var(--color-sun)";
  return "var(--color-glow)";
}

export default function SummaryBar({
  totalRequired,
  totalFulfilled,
  totalPlannedMinutes,
  totalCapacityMinutes,
  utilizationPct,
  averageFamiliarity,
  employeeCount,
}: SummaryBarProps) {
  const fulfillmentPct =
    totalRequired > 0 ? (totalFulfilled / totalRequired) * 100 : 0;
  const fulfillmentColor =
    fulfillmentPct >= 100
      ? "var(--color-kelp)"
      : fulfillmentPct > 0
        ? "var(--color-sun)"
        : "var(--color-coral)";

  const plannedHours = (totalPlannedMinutes / 60).toFixed(1);
  const capacityHours = (totalCapacityMinutes / 60).toFixed(1);
  const utilColor = utilizationColor(utilizationPct);

  return (
    <div className="flex items-stretch rounded-xl bg-deep/80 border border-reef/60 overflow-hidden">
      {/* Fulfillment cell */}
      <div className="flex-1 px-4 py-3 border-r border-reef/30">
        <div className="flex items-center gap-1.5 mb-1.5">
          <ListChecks
            className="w-3.5 h-3.5"
            style={{ color: fulfillmentColor }}
          />
          <span className="text-[10px] text-sediment uppercase tracking-widest font-600">
            Insatser
          </span>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="font-data text-lg text-moon">
            {totalFulfilled}/{totalRequired}
          </span>
          <span className="text-[10px] text-sediment">planerade</span>
        </div>
        <div className="mt-2 h-1 rounded-full bg-reef overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.min(fulfillmentPct, 100)}%`,
              backgroundColor: fulfillmentColor,
            }}
          />
        </div>
      </div>

      {/* Utilization cell */}
      <div className="flex-1 px-4 py-3 border-r border-reef/30">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Clock className="w-3.5 h-3.5" style={{ color: utilColor }} />
          <span className="text-[10px] text-sediment uppercase tracking-widest font-600">
            Beläggning
          </span>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="font-data text-lg text-moon">
            {plannedHours}h
          </span>
          <span className="text-[10px] text-sediment">
            / {capacityHours}h
          </span>
          <span
            className="font-data text-xs font-600 ml-auto"
            style={{ color: utilColor }}
          >
            {utilizationPct.toFixed(0)}%
          </span>
        </div>
        <div className="mt-2 h-1 rounded-full bg-reef overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.min(utilizationPct, 100)}%`,
              backgroundColor: utilColor,
            }}
          />
        </div>
      </div>

      {/* Continuity cell */}
      <div className="flex-1 px-4 py-3 flex items-center gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Users className="w-3.5 h-3.5 text-mist/50" />
            <span className="text-[10px] text-sediment uppercase tracking-widest font-600">
              Kontinuitet
            </span>
          </div>
          <span className="text-[10px] text-sediment">
            {employeeCount} anställda
          </span>
        </div>
        <ScoreRing
          score={averageFamiliarity}
          size={40}
          strokeWidth={2.5}
          label={`${Math.round(averageFamiliarity * 100)}% kontinuitet`}
        />
      </div>
    </div>
  );
}
