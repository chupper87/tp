import { useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Loader2, Users, Heart, ListChecks, Clock } from "lucide-react";
import {
  DndContext,
  DragOverlay,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { SHIFT_LABELS, SHIFT_COLORS } from "./constants";
import {
  useScheduleDetail,
  useActiveEmployees,
  useActiveCustomers,
  useActiveMeasures,
  useAssignEmployee,
  useAssignCustomer,
  useAddMeasure,
  useScheduleFulfillment,
  useScheduleUtilization,
  useContinuityPreview,
  useAutoPopulateMeasures,
} from "./hooks";
import type { ApiError } from "../../api/client";
import type { EmployeeBrief, CustomerBrief } from "./types";
import EmployeeSection from "./components/EmployeeSection";
import CustomerSection from "./components/CustomerSection";
import MeasuresSection from "./components/MeasuresSection";
import SummaryBar from "./components/SummaryBar";
import ResourcePool from "./components/ResourcePool";
import DraggableCard from "./components/DraggableCard";
import PersonSearchDropdown from "./components/PersonSearchDropdown";
import TimelineView from "./components/TimelineView";
import CustomerScheduleView from "./components/CustomerScheduleView";
import CreateVisitModal from "./components/CreateVisitModal";

const ROLE_LABELS: Record<string, string> = {
  assistant_nurse: "USK",
  care_assistant: "VB",
  nurse: "SSK",
  team_leader: "AL",
};

const CARE_LEVEL_COLORS: Record<string, string> = {
  low: "bg-kelp/20 text-kelp",
  medium: "bg-sun/20 text-sun",
  high: "bg-coral/20 text-coral",
};

const CARE_LEVEL_LABELS: Record<string, string> = {
  low: "Låg",
  medium: "Medel",
  high: "Hög",
};

const WEEKDAY_FULL = [
  "Söndag",
  "Måndag",
  "Tisdag",
  "Onsdag",
  "Torsdag",
  "Fredag",
  "Lördag",
];

function formatFullDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  const weekday = WEEKDAY_FULL[d.getDay()];
  const formatted = d.toLocaleDateString("sv-SE", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return `${weekday} ${formatted}`;
}

export default function ScheduleDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: schedule, isLoading } = useScheduleDetail(id!);
  const { data: allEmployees } = useActiveEmployees();
  const { data: allCustomers } = useActiveCustomers();
  const { data: allMeasures } = useActiveMeasures();

  // Planning intelligence queries
  const { data: fulfillment } = useScheduleFulfillment(id!);
  const { data: utilization } = useScheduleUtilization(id!);
  const { data: continuity } = useContinuityPreview(id!);

  const assignEmployee = useAssignEmployee(id!);
  const assignCustomer = useAssignCustomer(id!);
  const addMeasure = useAddMeasure(id!);
  const autoPopulate = useAutoPopulateMeasures(id!);

  // View tab state
  type ViewTab = "planning" | "employees" | "customers";
  const [activeView, setActiveView] = useState<ViewTab>("planning");
  const [showCreateVisit, setShowCreateVisit] = useState(false);

  // Auto-populate toast state
  const [autoPopulatePrompt, setAutoPopulatePrompt] = useState<{
    customerId: string;
    customerName: string;
  } | null>(null);

  // DnD state
  const [activeItem, setActiveItem] = useState<{
    type: string;
    id: string;
    label: string;
    extra?: string;
  } | null>(null);

  // Pool search filters
  const [empQuery, setEmpQuery] = useState("");
  const [custQuery, setCustQuery] = useState("");
  const [measureQuery, setMeasureQuery] = useState("");

  // Sensors with activation constraints
  const sensors = useSensors(
    useSensor(MouseSensor, {
      activationConstraint: { distance: 5 },
    }),
    useSensor(TouchSensor, {
      activationConstraint: { delay: 200, tolerance: 5 },
    }),
  );

  // Compute assigned ID sets
  const assignedEmployeeIds = useMemo(
    () => new Set(schedule?.employees.map((e) => e.employee_id) ?? []),
    [schedule?.employees],
  );
  const assignedCustomerIds = useMemo(
    () => new Set(schedule?.customers.map((c) => c.customer_id) ?? []),
    [schedule?.customers],
  );
  const assignedMeasureKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const m of schedule?.measures ?? []) {
      keys.add(`${m.customer_id}|${m.measure_id}|${m.time_of_day ?? ""}`);
    }
    return keys;
  }, [schedule?.measures]);

  // Filtered pool items
  const filteredEmployees = useMemo(() => {
    return (allEmployees ?? []).filter((e) => {
      if (assignedEmployeeIds.has(e.id)) return false;
      if (!empQuery) return true;
      const q = empQuery.toLowerCase();
      return (
        e.first_name.toLowerCase().includes(q) ||
        e.last_name.toLowerCase().includes(q)
      );
    });
  }, [allEmployees, assignedEmployeeIds, empQuery]);

  const filteredCustomers = useMemo(() => {
    return (allCustomers ?? []).filter((c) => {
      if (assignedCustomerIds.has(c.id)) return false;
      if (!custQuery) return true;
      const q = custQuery.toLowerCase();
      return (
        c.first_name.toLowerCase().includes(q) ||
        c.last_name.toLowerCase().includes(q)
      );
    });
  }, [allCustomers, assignedCustomerIds, custQuery]);

  const filteredMeasures = useMemo(() => {
    return (allMeasures ?? []).filter((m) => {
      if (!measureQuery) return true;
      return m.name.toLowerCase().includes(measureQuery.toLowerCase());
    });
  }, [allMeasures, measureQuery]);

  // Compute summary totals from fulfillment data
  const summaryTotals = useMemo(() => {
    const customers = fulfillment?.customers ?? [];
    let totalRequired = 0;
    let totalFulfilled = 0;
    for (const c of customers) {
      totalRequired += c.total_required;
      totalFulfilled += c.total_fulfilled;
    }
    return { totalRequired, totalFulfilled };
  }, [fulfillment]);

  // DnD handlers
  function handleDragStart(event: DragStartEvent) {
    const { type, id: itemId } = event.active.data.current as {
      type: string;
      id: string;
    };
    let label = "";
    let extra = "";

    if (type === "employee") {
      const emp = allEmployees?.find((e) => e.id === itemId);
      if (emp) {
        label = `${emp.first_name} ${emp.last_name}`;
        extra = ROLE_LABELS[emp.role] ?? emp.role;
      }
    } else if (type === "customer") {
      const cust = allCustomers?.find((c) => c.id === itemId);
      if (cust) {
        label = `${cust.first_name} ${cust.last_name}`;
        extra = cust.care_level
          ? CARE_LEVEL_LABELS[cust.care_level] ?? cust.care_level
          : "";
      }
    } else if (type === "measure") {
      const meas = allMeasures?.find((m) => m.id === itemId);
      if (meas) {
        label = meas.name;
        extra = `${meas.default_duration} min`;
      }
    }

    setActiveItem({ type, id: itemId, label, extra });
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveItem(null);
    const { active, over } = event;
    if (!over) return;

    const dragType = active.data.current?.type as string;
    const dropZone = over.data.current?.zone as string;

    if (dragType === "employee" && dropZone === "employees") {
      assignEmployee.mutate({
        employee_id: active.data.current!.id as string,
      });
    } else if (dragType === "customer" && dropZone === "customers") {
      const custId = active.data.current!.id as string;
      const cust = allCustomers?.find((c) => c.id === custId);
      assignCustomer.mutate(
        { customer_id: custId },
        {
          onSuccess: () => {
            if (cust) {
              setAutoPopulatePrompt({
                customerId: custId,
                customerName: `${cust.first_name} ${cust.last_name}`,
              });
            }
          },
        },
      );
    } else if (dragType === "measure" && dropZone === "customer-measures") {
      const customerId = over.data.current?.customerId as string;
      const measureId = active.data.current!.id as string;
      if (!assignedMeasureKeys.has(`${customerId}|${measureId}|`)) {
        addMeasure.mutate({
          customer_id: customerId,
          measure_id: measureId,
        });
      }
    }
  }

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-glow animate-spin" />
      </div>
    );
  }

  if (!schedule) {
    return (
      <div className="p-8">
        <Link
          to="/schedules"
          className="flex items-center gap-1.5 text-sm text-mist/50 hover:text-moon transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka
        </Link>
        <p className="text-sm text-sediment">Schemat hittades inte</p>
      </div>
    );
  }

  const shiftKey = schedule.shift_type ?? "custom";
  const shiftLabel = schedule.shift_type
    ? SHIFT_LABELS[schedule.shift_type]
    : schedule.custom_shift ?? "Anpassat";
  const shiftColors = SHIFT_COLORS[shiftKey] ?? SHIFT_COLORS.custom;

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="p-6 max-w-[1600px]">
        {/* Back link */}
        <Link
          to="/schedules"
          className="flex items-center gap-1.5 text-sm text-mist/50 hover:text-moon transition-colors mb-4 animate-fade-up"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka
        </Link>

        {/* Header */}
        <div className="mb-5 animate-fade-up stagger-1">
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-600 border ${shiftColors}`}
            >
              {shiftLabel}
            </span>
            <h1 className="font-display text-xl font-800 text-moon">
              {formatFullDate(schedule.date)}
            </h1>
          </div>
        </div>

        {/* Three-column layout */}
        <div className="grid grid-cols-[240px_1fr_240px] gap-4 animate-fade-up stagger-2">
          {/* Left pool: employees + customers */}
          <div className="space-y-3">
            <ResourcePool
              title="Anställda"
              count={filteredEmployees.length}
              onSearch={setEmpQuery}
              placeholder="Sök anställd..."
            >
              {filteredEmployees.length === 0 ? (
                <p className="text-xs text-sediment py-1">
                  Inga tillgängliga
                </p>
              ) : (
                filteredEmployees.map((emp) => (
                  <DraggableCard key={emp.id} id={emp.id} type="employee">
                    <span className="text-xs text-mist/80 flex-1 truncate">
                      {emp.first_name} {emp.last_name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-mid/40 text-mist/50 shrink-0">
                      {ROLE_LABELS[emp.role] ?? emp.role}
                    </span>
                  </DraggableCard>
                ))
              )}
            </ResourcePool>

            <ResourcePool
              title="Kunder"
              count={filteredCustomers.length}
              onSearch={setCustQuery}
              placeholder="Sök kund..."
            >
              {filteredCustomers.length === 0 ? (
                <p className="text-xs text-sediment py-1">
                  Inga tillgängliga
                </p>
              ) : (
                filteredCustomers.map((cust) => (
                  <DraggableCard key={cust.id} id={cust.id} type="customer">
                    <span className="text-xs text-mist/80 flex-1 truncate">
                      {cust.first_name} {cust.last_name}
                    </span>
                    {cust.care_level && (
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded shrink-0 ${
                          CARE_LEVEL_COLORS[cust.care_level] ??
                          "bg-mid/40 text-mist/50"
                        }`}
                      >
                        {CARE_LEVEL_LABELS[cust.care_level] ??
                          cust.care_level}
                      </span>
                    )}
                  </DraggableCard>
                ))
              )}
            </ResourcePool>
          </div>

          {/* Center: planning cockpit */}
          <div className="space-y-4">
            {/* Summary bar */}
            <SummaryBar
              totalRequired={summaryTotals.totalRequired}
              totalFulfilled={summaryTotals.totalFulfilled}
              totalPlannedMinutes={utilization?.total_planned_minutes ?? 0}
              totalCapacityMinutes={utilization?.total_capacity_minutes ?? 0}
              utilizationPct={utilization?.utilization_pct ?? 0}
              averageFamiliarity={continuity?.average_familiarity ?? 0}
              employeeCount={utilization?.employee_count ?? 0}
            />

            {/* View tabs */}
            <div className="flex items-center gap-1 p-1 rounded-lg bg-mid/20 border border-reef/20 w-fit">
              {(
                [
                  { key: "planning", label: "Planering" },
                  { key: "employees", label: "Anställda" },
                  { key: "customers", label: "Kunder" },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveView(tab.key)}
                  className={`px-3 py-1.5 rounded-md text-xs font-600 transition-colors cursor-pointer ${
                    activeView === tab.key
                      ? "bg-glow/15 text-glow border border-glow/20"
                      : "text-mist/50 hover:text-moon hover:bg-mid/20 border border-transparent"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Planning view */}
            {activeView === "planning" && (
              <>
                {/* Employee + Customer drop zones */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <EmployeeSection
                    scheduleId={schedule.id}
                    employees={schedule.employees}
                    assignError={assignEmployee.error as ApiError | null}
                    familiarityEntries={continuity?.entries ?? []}
                  />
                  <CustomerSection
                    scheduleId={schedule.id}
                    customers={schedule.customers}
                    assignError={assignCustomer.error as ApiError | null}
                  />
                </div>

                {/* Fallback search dropdowns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <PersonSearchDropdown<EmployeeBrief>
                    items={allEmployees ?? []}
                    excludeIds={assignedEmployeeIds}
                    placeholder="Lägg till anställd"
                    onSelect={(emp) =>
                      assignEmployee.mutate({ employee_id: emp.id })
                    }
                    renderExtra={(emp) => (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-mid/40 text-mist/50">
                        {ROLE_LABELS[emp.role] ?? emp.role}
                      </span>
                    )}
                  />
                  <PersonSearchDropdown<CustomerBrief>
                    items={allCustomers ?? []}
                    excludeIds={assignedCustomerIds}
                    placeholder="Lägg till kund"
                    onSelect={(cust) =>
                      assignCustomer.mutate(
                        { customer_id: cust.id },
                        {
                          onSuccess: () =>
                            setAutoPopulatePrompt({
                              customerId: cust.id,
                              customerName: `${cust.first_name} ${cust.last_name}`,
                            }),
                        },
                      )
                    }
                    renderExtra={(cust) => {
                      if (!cust.care_level) return null;
                      return (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded ${
                            CARE_LEVEL_COLORS[cust.care_level] ??
                            "bg-mid/40 text-mist/50"
                          }`}
                        >
                          {CARE_LEVEL_LABELS[cust.care_level]}
                        </span>
                      );
                    }}
                  />
                </div>

                {/* Fulfillment cards */}
                <MeasuresSection
                  scheduleId={schedule.id}
                  customers={schedule.customers}
                  measures={schedule.measures}
                  fulfillmentCustomers={fulfillment?.customers ?? []}
                />
              </>
            )}

            {/* Employee timeline view */}
            {activeView === "employees" && (
              <TimelineView
                scheduleId={schedule.id}
                scheduleDate={schedule.date}
                onCreateVisit={() => setShowCreateVisit(true)}
              />
            )}

            {/* Customer schedule view */}
            {activeView === "customers" && (
              <CustomerScheduleView scheduleId={schedule.id} />
            )}
          </div>

          {/* Right pool: measures */}
          <div>
            <ResourcePool
              title="Insatser"
              count={filteredMeasures.length}
              onSearch={setMeasureQuery}
              placeholder="Sök insats..."
            >
              {filteredMeasures.length === 0 ? (
                <p className="text-xs text-sediment py-1">
                  Inga tillgängliga
                </p>
              ) : (
                filteredMeasures.map((meas) => (
                  <DraggableCard key={meas.id} id={meas.id} type="measure">
                    <span className="text-xs text-mist/80 flex-1 truncate">
                      {meas.name}
                    </span>
                    <span className="flex items-center gap-0.5 text-[10px] text-sediment shrink-0">
                      <Clock className="w-3 h-3" />
                      {meas.default_duration}m
                    </span>
                  </DraggableCard>
                ))
              )}
            </ResourcePool>
          </div>
        </div>
      </div>

      {/* Auto-populate toast */}
      {autoPopulatePrompt && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-fade-up">
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-deep border border-reef/60 shadow-[0_4px_24px_rgba(0,0,0,0.5)]">
            <ListChecks className="w-4 h-4 text-glow shrink-0" />
            <span className="text-sm text-moon">
              Lägg till insatser för{" "}
              <span className="font-600">
                {autoPopulatePrompt.customerName}
              </span>{" "}
              automatiskt?
            </span>
            <button
              onClick={() => {
                autoPopulate.mutate(autoPopulatePrompt.customerId);
                setAutoPopulatePrompt(null);
              }}
              className="px-3 py-1 rounded-lg bg-glow/15 text-glow text-xs font-600 hover:bg-glow/25 transition-colors cursor-pointer"
            >
              Ja, lägg till
            </button>
            <button
              onClick={() => setAutoPopulatePrompt(null)}
              className="px-3 py-1 rounded-lg bg-mid/30 text-mist/60 text-xs font-600 hover:bg-mid/50 transition-colors cursor-pointer"
            >
              Nej
            </button>
          </div>
        </div>
      )}

      {/* Create visit modal */}
      {showCreateVisit && schedule && (
        <CreateVisitModal
          scheduleId={schedule.id}
          employees={schedule.employees}
          customers={schedule.customers}
          measures={schedule.measures}
          onClose={() => setShowCreateVisit(false)}
        />
      )}

      {/* Drag overlay — the floating ghost card */}
      <DragOverlay>
        {activeItem && (
          <div className="flex items-center gap-2 h-9 px-3 rounded-lg bg-ocean border-2 border-glow/60 shadow-[0_0_20px_rgba(45,212,191,0.3)] scale-105 rotate-1">
            {activeItem.type === "employee" && (
              <Users className="w-3.5 h-3.5 text-glow shrink-0" />
            )}
            {activeItem.type === "customer" && (
              <Heart className="w-3.5 h-3.5 text-glow shrink-0" />
            )}
            {activeItem.type === "measure" && (
              <ListChecks className="w-3.5 h-3.5 text-glow shrink-0" />
            )}
            <span className="text-xs font-600 text-moon">
              {activeItem.label}
            </span>
            {activeItem.extra && (
              <span className="text-[10px] text-glow/70">
                {activeItem.extra}
              </span>
            )}
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}
