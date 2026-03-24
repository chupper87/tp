import { Loader2, AlertTriangle, Clock } from "lucide-react";
import { useCustomerSchedule } from "../hooks";
import { timeToMinutes, minutesToTime } from "../constants";
import type { CustomerDay, CustomerVisit } from "../types";

interface CustomerScheduleViewProps {
  scheduleId: string;
}

const CARE_LEVEL_COLORS: Record<string, string> = {
  low: "bg-kelp/15 text-kelp",
  medium: "bg-sun/15 text-sun",
  high: "bg-coral/15 text-coral",
};

const CARE_LEVEL_LABELS: Record<string, string> = {
  low: "Låg",
  medium: "Medel",
  high: "Hög",
};

export default function CustomerScheduleView({
  scheduleId,
}: CustomerScheduleViewProps) {
  const { data, isLoading } = useCustomerSchedule(scheduleId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 text-glow animate-spin" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-600 text-moon">Kundschema</h3>

      {data.customers.length === 0 ? (
        <div className="px-4 py-8 text-center">
          <p className="text-xs text-sediment">Inga kunder tilldelade</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {data.customers.map((customer) => (
            <CustomerDayCard key={customer.customer_id} customer={customer} />
          ))}
        </div>
      )}
    </div>
  );
}

function CustomerDayCard({ customer }: { customer: CustomerDay }) {
  const hasWarnings = customer.warnings.length > 0;
  const borderColor = hasWarnings
    ? "border-l-coral"
    : customer.visits.length > 0
      ? "border-l-glow"
      : "border-l-sediment/30";

  return (
    <div
      className={`rounded-xl bg-ocean/60 border border-reef/30 border-l-[3px] ${borderColor}`}
    >
      {/* Header */}
      <div className="px-3.5 py-2.5 border-b border-reef/15 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-600 text-moon truncate">
            {customer.customer_name}
          </span>
          {customer.care_level && (
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded font-600 ${
                CARE_LEVEL_COLORS[customer.care_level] ?? "bg-mid/40 text-mist/50"
              }`}
            >
              {CARE_LEVEL_LABELS[customer.care_level] ?? customer.care_level}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <HoursGauge
            plannedMinutes={customer.total_planned_minutes_today}
            approvedMonthly={customer.approved_hours_monthly}
          />
          <span className="font-data text-xs text-mist/50">
            {customer.total_planned_minutes_today}m
          </span>
        </div>
      </div>

      {/* Warnings */}
      {hasWarnings && (
        <div className="px-3.5 py-2 border-b border-reef/10 space-y-1">
          {customer.warnings.map((w, i) => (
            <div
              key={i}
              className="flex items-center gap-1.5 text-[11px] text-coral/80"
            >
              <AlertTriangle className="w-3 h-3 shrink-0" />
              {w}
            </div>
          ))}
        </div>
      )}

      {/* Visits */}
      <div className="px-3.5 py-2 space-y-1.5">
        {customer.visits.length === 0 ? (
          <p className="text-xs text-sediment py-1">
            Inga besök schemalagda
          </p>
        ) : (
          customer.visits.map((visit, i) => (
            <VisitRow
              key={visit.care_visit_id}
              visit={visit}
              prevVisit={i > 0 ? customer.visits[i - 1] : undefined}
            />
          ))
        )}
      </div>
    </div>
  );
}

function VisitRow({
  visit,
  prevVisit,
}: {
  visit: CustomerVisit;
  prevVisit?: CustomerVisit;
}) {
  const startStr = minutesToTime(timeToMinutes(visit.planned_start_time));
  const endStr = minutesToTime(timeToMinutes(visit.planned_end_time));

  // Gap from previous visit
  let gapMin = 0;
  if (prevVisit) {
    gapMin =
      timeToMinutes(visit.planned_start_time) -
      timeToMinutes(prevVisit.planned_end_time);
  }

  return (
    <>
      {gapMin > 0 && (
        <div className="flex items-center gap-2 py-0.5">
          <div className="flex-1 h-px bg-reef/15 border-t border-dashed border-reef/20" />
          <span className="font-data text-[9px] text-sediment/50">
            {gapMin}m
          </span>
          <div className="flex-1 h-px bg-reef/15 border-t border-dashed border-reef/20" />
        </div>
      )}
      <div className="flex items-start gap-2.5 py-1">
        {/* Time */}
        <div className="w-[80px] shrink-0">
          <span className="font-data text-[11px] text-mist/60">
            {startStr}–{endStr}
          </span>
        </div>
        {/* Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-[11px] text-mist/50">
              {visit.employee_names.join(", ")}
            </span>
            <span className="font-data text-[10px] text-sediment flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />
              {visit.duration}m
            </span>
          </div>
          <div className="flex flex-wrap gap-x-2 gap-y-0.5">
            {visit.measures.map((m, j) => (
              <span key={j} className="text-xs text-mist/70">
                {m.measure_name}{" "}
                <span className="font-data text-sediment">
                  {m.duration}m
                </span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function HoursGauge({
  plannedMinutes,
  approvedMonthly,
}: {
  plannedMinutes: number;
  approvedMonthly: number | null;
}) {
  if (!approvedMonthly || approvedMonthly <= 0) return null;

  // Rough daily estimate: monthly hours / 30 days
  const dailyBudgetMin = (approvedMonthly * 60) / 30;
  const pct = Math.min((plannedMinutes / dailyBudgetMin) * 100, 100);
  const isOver = plannedMinutes > dailyBudgetMin;

  return (
    <div className="w-16 h-1.5 rounded-full bg-reef/20 overflow-hidden" title={
      `${plannedMinutes}m av ~${Math.round(dailyBudgetMin)}m daglig budget`
    }>
      <div
        className={`h-full rounded-full transition-all duration-500 ${
          isOver ? "bg-coral" : pct > 80 ? "bg-sun" : "bg-glow"
        }`}
        style={{ width: `${Math.min(pct, 100)}%` }}
      />
    </div>
  );
}
