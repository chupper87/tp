import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Loader2,
  Plus,
  Trash2,
  AlertCircle,
  Heart,
  Clock,
} from "lucide-react";
import { api } from "../../api/client";
import type { ApiError } from "../../api/client";
import {
  useCustomerMeasures,
  useAddCustomerMeasure,
  useUpdateCustomerMeasure,
  useRemoveCustomerMeasure,
} from "./hooks";
import type { CustomerMeasureOut } from "./types";

interface CustomerOut {
  id: string;
  first_name: string;
  last_name: string;
  key_number: number;
  address: string;
  care_level: string | null;
  gender: string | null;
  approved_hours: number | null;
  is_active: boolean;
}

interface MeasureBrief {
  id: string;
  name: string;
  default_duration: number;
  time_of_day: string | null;
  is_active: boolean;
}

const CARE_LEVEL_LABELS: Record<string, string> = {
  high: "Hög",
  medium: "Medel",
  low: "Låg",
};

const CARE_LEVEL_COLORS: Record<string, string> = {
  high: "bg-coral/10 text-coral border-coral/20",
  medium: "bg-sun/10 text-sun border-sun/20",
  low: "bg-kelp/10 text-kelp border-kelp/20",
};

const FREQUENCY_LABELS: Record<string, string> = {
  daily: "Daglig",
  weekly: "Veckovis",
  biweekly: "Varannan vecka",
  monthly: "Månadsvis",
};

const TIME_OF_DAY_LABELS: Record<string, string> = {
  morning: "Morgon",
  midday: "Mitt på dagen",
  afternoon: "Eftermiddag",
  evening: "Kväll",
  night: "Natt",
};

const DAY_LABELS: [string, string][] = [
  ["monday", "Mån"],
  ["tuesday", "Tis"],
  ["wednesday", "Ons"],
  ["thursday", "Tor"],
  ["friday", "Fre"],
  ["saturday", "Lör"],
  ["sunday", "Sön"],
];

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: customer, isLoading: loadingCustomer } = useQuery({
    queryKey: ["customers", id],
    queryFn: () => api.get<CustomerOut>(`/customers/${id}`),
    enabled: !!id,
  });

  const { data: measures, isLoading: loadingMeasures } = useCustomerMeasures(
    id!,
  );

  const { data: allMeasures } = useQuery({
    queryKey: ["measures", { active: true }],
    queryFn: () => api.get<MeasureBrief[]>("/measures/?is_active=true"),
    staleTime: 60_000,
  });

  if (loadingCustomer) {
    return (
      <div className="p-8 flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-glow animate-spin" />
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="p-8">
        <Link
          to="/customers"
          className="flex items-center gap-1.5 text-sm text-mist/50 hover:text-moon transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka
        </Link>
        <p className="text-sm text-sediment">Kund hittades inte</p>
      </div>
    );
  }

  // No longer filter out assigned measures — same measure can be added
  // multiple times with different time_of_day (e.g. Tillsyn morning + night)

  return (
    <div className="p-8 max-w-[1000px]">
      {/* Back link */}
      <Link
        to="/customers"
        className="flex items-center gap-1.5 text-sm text-mist/50 hover:text-moon transition-colors mb-4 animate-fade-up"
      >
        <ArrowLeft className="w-4 h-4" />
        Tillbaka till kunder
      </Link>

      {/* Customer header */}
      <div className="card-glow rounded-xl bg-ocean/60 p-5 mb-5 animate-fade-up stagger-1">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-mid flex items-center justify-center text-lg font-700 text-current/80 shrink-0">
            {customer.first_name[0]}
            {customer.last_name[0]}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="font-display text-xl font-800 text-moon">
                {customer.first_name} {customer.last_name}
              </h1>
              {customer.care_level && (
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-600 border ${CARE_LEVEL_COLORS[customer.care_level] ?? ""}`}
                >
                  {CARE_LEVEL_LABELS[customer.care_level] ??
                    customer.care_level}
                </span>
              )}
              <span
                className={`inline-flex items-center gap-1.5 text-xs ${customer.is_active ? "text-kelp" : "text-sediment"}`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${customer.is_active ? "bg-kelp" : "bg-sediment"}`}
                />
                {customer.is_active ? "Aktiv" : "Inaktiv"}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-mist/50">
              <span>{customer.address}</span>
              <span className="text-sediment">·</span>
              <span>Nyckel: {customer.key_number}</span>
              {customer.approved_hours && (
                <>
                  <span className="text-sediment">·</span>
                  <span>
                    {customer.approved_hours} beviljade tim/mån
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Care plan */}
      <div className="animate-fade-up stagger-2">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-sm font-700 text-moon uppercase tracking-wider">
            Omsorgsplan
          </h2>
          <span className="text-xs text-sediment">
            {measures?.length ?? 0} insatser
          </span>
        </div>

        <div className="card-glow rounded-xl bg-ocean/60 overflow-hidden">
          {loadingMeasures ? (
            <div className="p-8 animate-pulse">
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-10 bg-mid/30 rounded-lg" />
                ))}
              </div>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="grid grid-cols-[1fr_100px_100px_100px_140px_40px] gap-2 px-4 py-2.5 border-b border-reef">
                <span className="text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Insats
                </span>
                <span className="text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Frekvens
                </span>
                <span className="text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Tid på dygnet
                </span>
                <span className="text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Tid (min)
                </span>
                <span className="text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Dagar
                </span>
                <span />
              </div>

              {/* Rows */}
              {measures?.map((cm) => (
                <CarePlanRow
                  key={cm.id}
                  customerId={id!}
                  measure={cm}
                />
              ))}

              {measures?.length === 0 && (
                <div className="text-center py-8">
                  <Heart
                    className="w-8 h-8 text-sediment mx-auto mb-2"
                    strokeWidth={1}
                  />
                  <p className="text-xs text-sediment">
                    Ingen omsorgsplan ännu — lägg till insatser nedan
                  </p>
                </div>
              )}

              {/* Add form */}
              <AddMeasureForm
                customerId={id!}
                allMeasures={allMeasures ?? []}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Care plan row ---

function CarePlanRow({
  customerId,
  measure,
}: {
  customerId: string;
  measure: CustomerMeasureOut;
}) {
  const update = useUpdateCustomerMeasure(customerId);
  const remove = useRemoveCustomerMeasure(customerId);

  const duration = measure.customer_duration ?? measure.measure_default_duration;
  const days = measure.days_of_week ?? [];

  function toggleDay(day: string) {
    const newDays = days.includes(day)
      ? days.filter((d) => d !== day)
      : [...days, day];
    update.mutate({
      id: measure.id,
      days_of_week: newDays.length > 0 ? newDays : [],
    });
  }

  return (
    <div className="grid grid-cols-[1fr_100px_100px_100px_140px_40px] gap-2 items-center px-4 py-2 border-b border-reef/20 hover:bg-mid/10 transition-colors group">
      <span className="text-sm text-mist/80">{measure.measure_name}</span>
      <span className="text-xs text-mist/50">
        {FREQUENCY_LABELS[measure.frequency] ?? measure.frequency}
      </span>
      <span className="text-xs text-mist/50">
        {measure.time_of_day
          ? TIME_OF_DAY_LABELS[measure.time_of_day]
          : "—"}
      </span>
      <span className="font-data text-xs text-mist/50 flex items-center gap-1">
        <Clock className="w-3 h-3" />
        {duration}
      </span>
      <div className="flex gap-0.5">
        {DAY_LABELS.map(([key, label]) => (
          <button
            key={key}
            onClick={() => toggleDay(key)}
            disabled={update.isPending}
            className={`w-5 h-5 rounded text-[9px] flex items-center justify-center font-600 cursor-pointer transition-all ${
              days.includes(key)
                ? "bg-glow/20 text-glow hover:bg-glow/30"
                : "bg-mid/20 text-sediment/40 hover:bg-mid/30 hover:text-sediment"
            }`}
          >
            {label[0]}
          </button>
        ))}
      </div>
      <button
        onClick={() => remove.mutate(measure.id)}
        disabled={remove.isPending}
        className="opacity-0 group-hover:opacity-100 text-sediment hover:text-coral transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center"
      >
        {remove.isPending ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Trash2 className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  );
}

// --- Add measure form ---

function AddMeasureForm({
  customerId,
  allMeasures,
}: {
  customerId: string;
  allMeasures: MeasureBrief[];
}) {
  const [open, setOpen] = useState(false);
  const [measureId, setMeasureId] = useState("");
  const [frequency, setFrequency] = useState("daily");
  const [timeOfDay, setTimeOfDay] = useState("");
  const [daysOfWeek, setDaysOfWeek] = useState<string[]>([]);
  const [customDuration, setCustomDuration] = useState("");

  const add = useAddCustomerMeasure(customerId);
  const error = add.error as ApiError | null;

  const available = allMeasures;
  const selected = allMeasures.find((m) => m.id === measureId);

  function handleSubmit() {
    if (!measureId) return;
    add.mutate(
      {
        measure_id: measureId,
        frequency,
        ...(timeOfDay ? { time_of_day: timeOfDay } : {}),
        ...(daysOfWeek.length > 0 ? { days_of_week: daysOfWeek } : {}),
        ...(customDuration
          ? { customer_duration: parseInt(customDuration, 10) }
          : {}),
      },
      {
        onSuccess: () => {
          setOpen(false);
          setMeasureId("");
          setFrequency("daily");
          setTimeOfDay("");
          setDaysOfWeek([]);
          setCustomDuration("");
        },
      },
    );
  }

  function toggleDay(day: string) {
    setDaysOfWeek((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day],
    );
  }

  if (!open) {
    return (
      <div className="px-4 py-3">
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 text-xs text-glow/70 hover:text-glow transition-colors cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          Lägg till insats
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 py-3 border-t border-reef/30 space-y-3">
      {error && (
        <div className="flex items-start gap-2 p-2 rounded-lg bg-coral/10 border border-coral/20">
          <AlertCircle className="w-3.5 h-3.5 text-coral mt-0.5 shrink-0" />
          <p className="text-xs text-coral">{error.detail}</p>
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        {/* Measure select */}
        <div>
          <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1">
            Insats
          </label>
          <select
            value={measureId}
            onChange={(e) => setMeasureId(e.target.value)}
            className="w-full h-8 px-2 rounded-md bg-deep border border-reef text-sm text-moon focus:border-glow/50 focus:outline-none transition-colors"
          >
            <option value="">Välj insats...</option>
            {available.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.default_duration} min)
              </option>
            ))}
          </select>
        </div>

        {/* Frequency */}
        <div>
          <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1">
            Frekvens
          </label>
          <select
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
            className="w-full h-8 px-2 rounded-md bg-deep border border-reef text-sm text-moon focus:border-glow/50 focus:outline-none transition-colors"
          >
            <option value="daily">Daglig</option>
            <option value="weekly">Veckovis</option>
            <option value="biweekly">Varannan vecka</option>
            <option value="monthly">Månadsvis</option>
          </select>
        </div>

        {/* Time of day */}
        <div>
          <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1">
            Tid på dygnet
          </label>
          <select
            value={timeOfDay}
            onChange={(e) => setTimeOfDay(e.target.value)}
            className="w-full h-8 px-2 rounded-md bg-deep border border-reef text-sm text-moon focus:border-glow/50 focus:outline-none transition-colors"
          >
            <option value="">
              {selected?.time_of_day
                ? TIME_OF_DAY_LABELS[selected.time_of_day]
                : "Standard"}
            </option>
            {Object.entries(TIME_OF_DAY_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Days of week (for weekly) */}
      {(frequency === "weekly" || frequency === "biweekly") && (
        <div>
          <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1.5">
            Dagar
          </label>
          <div className="flex gap-1.5">
            {DAY_LABELS.map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => toggleDay(key)}
                className={`w-9 h-7 rounded text-xs font-600 border transition-all cursor-pointer ${
                  daysOfWeek.includes(key)
                    ? "bg-glow/20 text-glow border-glow/30"
                    : "bg-mid/20 border-reef/40 text-mist/50 hover:border-reef-light"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Duration override + actions */}
      <div className="flex items-end gap-3">
        <div className="w-32">
          <label className="block text-[10px] font-600 text-mist/50 uppercase tracking-wider mb-1">
            Anpassad tid (min)
          </label>
          <input
            type="number"
            value={customDuration}
            onChange={(e) => setCustomDuration(e.target.value)}
            placeholder={selected ? String(selected.default_duration) : "—"}
            min={1}
            max={480}
            className="w-full h-8 px-2 rounded-md bg-deep border border-reef text-sm text-moon placeholder:text-sediment focus:border-glow/50 focus:outline-none transition-colors"
          />
        </div>
        <div className="flex gap-2 ml-auto">
          <button
            onClick={() => setOpen(false)}
            className="h-8 px-3 rounded-md border border-reef text-xs text-mist/60 hover:text-moon hover:border-reef-light transition-colors cursor-pointer"
          >
            Avbryt
          </button>
          <button
            onClick={handleSubmit}
            disabled={!measureId || add.isPending}
            className="h-8 px-4 rounded-md bg-glow/90 hover:bg-glow text-abyss text-xs font-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 cursor-pointer"
          >
            {add.isPending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              "Lägg till"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
