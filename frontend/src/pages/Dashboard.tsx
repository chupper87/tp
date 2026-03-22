import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Heart,
  CalendarDays,
  ClipboardCheck,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../hooks/useAuth";

interface EmployeeOut {
  id: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
}

interface CustomerOut {
  id: string;
  first_name: string;
  last_name: string;
  care_level: string;
  approved_hours: number | null;
  is_active: boolean;
}

interface ScheduleOut {
  id: string;
  date: string;
  shift_type: string | null;
  custom_shift: string | null;
}

interface VisitSummary {
  date_from: string;
  date_to: string;
  total: number;
  by_status: { status: string; count: number }[];
}

interface ContinuityRow {
  customer_id: string;
  first_name: string;
  last_name: string;
  total_visits: number;
  unique_employees: number;
  continuity_score: number;
}

interface ContinuityReport {
  date_from: string;
  date_to: string;
  average_score: number;
  rows: ContinuityRow[];
}

function today() {
  return new Date().toISOString().split("T")[0];
}

function thirtyDaysAgo() {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return d.toISOString().split("T")[0];
}

function formatShift(s: ScheduleOut) {
  if (s.shift_type) return s.shift_type.charAt(0).toUpperCase() + s.shift_type.slice(1);
  return s.custom_shift ?? "Custom";
}

const shiftColors: Record<string, string> = {
  morning: "bg-sun/15 text-sun border-sun/20",
  day: "bg-current/15 text-current border-current/20",
  evening: "bg-glow/15 text-glow border-glow/20",
  night: "bg-mist/10 text-mist border-mist/20",
};

function ShiftBadge({ schedule }: { schedule: ScheduleOut }) {
  const key = schedule.shift_type ?? "custom";
  const colors = shiftColors[key] ?? "bg-sediment/20 text-mist/80 border-sediment/30";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-600 border ${colors}`}>
      {formatShift(schedule)}
    </span>
  );
}

function ScoreRing({ score, size = 56 }: { score: number; size?: number }) {
  const radius = (size - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - score);
  const color =
    score >= 0.8
      ? "var(--color-glow)"
      : score >= 0.5
        ? "var(--color-sun)"
        : "var(--color-coral)";

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-reef)"
          strokeWidth={3}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center font-data text-xs font-600"
        style={{ color }}
      >
        {Math.round(score * 100)}
      </span>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  trend,
  className = "",
  delay = 0,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  trend?: "up" | "down";
  className?: string;
  delay?: number;
}) {
  return (
    <div
      className={`card-glow rounded-xl bg-ocean/60 p-5 animate-fade-up ${className}`}
      style={{ animationDelay: `${delay * 0.06}s` }}
    >
      <div className="flex items-start justify-between">
        <div className="w-9 h-9 rounded-lg bg-mid/80 flex items-center justify-center">
          <Icon className="w-[18px] h-[18px] text-glow" strokeWidth={1.5} />
        </div>
        {trend && (
          <div
            className={`flex items-center gap-1 text-xs font-data ${
              trend === "up" ? "text-kelp" : "text-coral"
            }`}
          >
            {trend === "up" ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
          </div>
        )}
      </div>
      <p className="mt-4 font-data text-2xl font-700 text-moon">{value}</p>
      <p className="mt-1 text-xs text-mist/60 font-500">{label}</p>
      {sub && <p className="mt-0.5 text-[10px] text-sediment font-data">{sub}</p>}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="p-8 space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-mid/60 rounded-lg" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-ocean/60 rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 h-64 bg-ocean/60 rounded-xl" />
        <div className="h-64 bg-ocean/60 rounded-xl" />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { isAdmin } = useAuth();
  const dateFrom = thirtyDaysAgo();
  const dateTo = today();

  const { data: employees, isLoading: loadingEmp } = useQuery({
    queryKey: ["employees"],
    queryFn: () => api.get<EmployeeOut[]>("/employees/"),
    enabled: isAdmin,
  });

  const { data: customers, isLoading: loadingCust } = useQuery({
    queryKey: ["customers"],
    queryFn: () => api.get<CustomerOut[]>("/customers/"),
    enabled: isAdmin,
  });

  const { data: todaySchedules, isLoading: loadingSched } = useQuery({
    queryKey: ["schedules", "today"],
    queryFn: () =>
      api.get<ScheduleOut[]>(`/schedules/?date_from=${dateTo}&date_to=${dateTo}`),
    enabled: isAdmin,
  });

  const { data: visitSummary, isLoading: loadingVisits } = useQuery({
    queryKey: ["reports", "visit-summary", dateFrom, dateTo],
    queryFn: () =>
      api.get<VisitSummary>(
        `/reports/visit-summary?date_from=${dateFrom}&date_to=${dateTo}`,
      ),
    enabled: isAdmin,
  });

  const { data: continuity, isLoading: loadingCont } = useQuery({
    queryKey: ["reports", "continuity", dateFrom, dateTo],
    queryFn: () =>
      api.get<ContinuityReport>(
        `/reports/continuity?date_from=${dateFrom}&date_to=${dateTo}`,
      ),
    enabled: isAdmin,
  });

  const isLoading =
    loadingEmp || loadingCust || loadingSched || loadingVisits || loadingCont;

  if (isLoading) return <DashboardSkeleton />;

  const activeEmployees = employees?.filter((e) => e.is_active).length ?? 0;
  const activeCustomers = customers?.filter((c) => c.is_active).length ?? 0;
  const completedVisits =
    visitSummary?.by_status.find((s) => s.status === "completed")?.count ?? 0;
  const plannedVisits =
    visitSummary?.by_status.find((s) => s.status === "planned")?.count ?? 0;

  // Sort continuity by score ascending (worst first — needs attention)
  const continuityRows = [...(continuity?.rows ?? [])].sort(
    (a, b) => a.continuity_score - b.continuity_score,
  );
  const lowContinuity = continuityRows.filter((r) => r.continuity_score < 0.6);

  return (
    <div className="p-8 max-w-[1400px]">
      {/* Header */}
      <div className="mb-8 animate-fade-up">
        <h1 className="font-display text-2xl font-800 text-moon">Dashboard</h1>
        <p className="text-sm text-mist/50 mt-1">
          Overview for {new Date().toLocaleDateString("en-SE", { month: "long", day: "numeric", year: "numeric" })}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={Users}
          label="Active employees"
          value={activeEmployees}
          sub={`${employees?.length ?? 0} total`}
          delay={1}
        />
        <StatCard
          icon={Heart}
          label="Active customers"
          value={activeCustomers}
          sub={`${customers?.length ?? 0} total`}
          delay={2}
        />
        <StatCard
          icon={ClipboardCheck}
          label="Completed visits"
          value={completedVisits}
          sub={`Last 30 days`}
          trend="up"
          delay={3}
        />
        <StatCard
          icon={CalendarDays}
          label="Planned visits"
          value={plannedVisits}
          sub="Upcoming"
          delay={4}
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Today's schedules */}
        <div className="lg:col-span-2 card-glow rounded-xl bg-ocean/60 p-6 animate-fade-up stagger-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-glow" strokeWidth={1.5} />
              <h2 className="font-display font-700 text-moon">Today's Shifts</h2>
            </div>
            <Link
              to="/schedules"
              className="text-xs text-mist/50 hover:text-glow transition-colors flex items-center gap-1"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {todaySchedules && todaySchedules.length > 0 ? (
            <div className="space-y-2">
              {todaySchedules.map((schedule) => (
                <Link
                  key={schedule.id}
                  to={`/schedules/${schedule.id}`}
                  className="flex items-center justify-between p-3 rounded-lg bg-mid/30 hover:bg-mid/50 border border-reef/50 hover:border-reef-light transition-all group"
                >
                  <div className="flex items-center gap-3">
                    <ShiftBadge schedule={schedule} />
                    <span className="text-sm text-mist/80 font-data">
                      {schedule.date}
                    </span>
                  </div>
                  <ArrowRight className="w-4 h-4 text-sediment group-hover:text-mist/60 transition-colors" />
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <CalendarDays className="w-10 h-10 text-sediment mb-3" strokeWidth={1} />
              <p className="text-sm text-sediment">No shifts scheduled today</p>
              <Link
                to="/schedules"
                className="mt-3 text-xs text-glow/70 hover:text-glow transition-colors"
              >
                Create a schedule
              </Link>
            </div>
          )}
        </div>

        {/* Continuity overview */}
        <div className="card-glow rounded-xl bg-ocean/60 p-6 animate-fade-up stagger-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-glow" strokeWidth={1.5} />
              <h2 className="font-display font-700 text-moon">Continuity</h2>
            </div>
            <Link
              to="/reports"
              className="text-xs text-mist/50 hover:text-glow transition-colors"
            >
              Reports
            </Link>
          </div>

          {/* Average score */}
          {continuity && (
            <div className="flex items-center gap-4 mb-5 p-3 rounded-lg bg-mid/30 border border-reef/50">
              <ScoreRing score={continuity.average_score} />
              <div>
                <p className="text-xs text-mist/60">Avg. score</p>
                <p className="font-data text-lg font-600 text-moon">
                  {(continuity.average_score * 100).toFixed(1)}%
                </p>
                <p className="text-[10px] text-sediment">Last 30 days</p>
              </div>
            </div>
          )}

          {/* Low continuity alerts */}
          {lowContinuity.length > 0 ? (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 mb-1">
                <AlertTriangle className="w-3 h-3 text-sun" />
                <p className="text-[10px] text-sun/80 uppercase tracking-wider font-600">
                  Needs attention
                </p>
              </div>
              {lowContinuity.slice(0, 5).map((row) => (
                <div
                  key={row.customer_id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-mid/20 border border-reef/30"
                >
                  <div>
                    <p className="text-sm text-moon/90">
                      {row.first_name} {row.last_name}
                    </p>
                    <p className="text-[10px] text-sediment font-data">
                      {row.unique_employees} workers / {row.total_visits} visits
                    </p>
                  </div>
                  <ScoreRing score={row.continuity_score} size={40} />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-xs text-kelp/60">All continuity scores above 60%</p>
            </div>
          )}
        </div>
      </div>

      {/* Visit summary */}
      {visitSummary && visitSummary.total > 0 && (
        <div className="mt-4 card-glow rounded-xl bg-ocean/60 p-6 animate-fade-up stagger-6">
          <div className="flex items-center gap-2 mb-4">
            <ClipboardCheck className="w-4 h-4 text-glow" strokeWidth={1.5} />
            <h2 className="font-display font-700 text-moon">Visit Summary</h2>
            <span className="text-xs text-sediment font-data ml-auto">Last 30 days</span>
          </div>
          <div className="flex gap-6 flex-wrap">
            {visitSummary.by_status.map((s) => {
              const statusColors: Record<string, string> = {
                completed: "text-kelp",
                planned: "text-current",
                canceled: "text-coral",
                no_show: "text-sun",
                partially_completed: "text-mist",
                rescheduled: "text-drift",
              };
              return (
                <div key={s.status} className="flex items-baseline gap-2">
                  <span className={`font-data text-xl font-700 ${statusColors[s.status] ?? "text-mist"}`}>
                    {s.count}
                  </span>
                  <span className="text-xs text-sediment capitalize">
                    {s.status.replace("_", " ")}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
