import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CalendarDays, Plus } from "lucide-react";
import { getMonday, formatDateISO } from "./constants";
import { useScheduleList } from "./hooks";
import WeekNavigator from "./components/WeekNavigator";
import WeekGrid from "./components/WeekGrid";
import CreateScheduleModal from "./components/CreateScheduleModal";

export default function ScheduleList() {
  const navigate = useNavigate();
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));
  const [modal, setModal] = useState<{
    date: string;
    shiftType?: string;
  } | null>(null);

  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);

  const dateFrom = formatDateISO(weekStart);
  const dateTo = formatDateISO(weekEnd);

  const { data: schedules, isLoading } = useScheduleList(dateFrom, dateTo);

  function handlePrev() {
    setWeekStart((prev) => {
      const d = new Date(prev);
      d.setDate(d.getDate() - 7);
      return d;
    });
  }

  function handleNext() {
    setWeekStart((prev) => {
      const d = new Date(prev);
      d.setDate(d.getDate() + 7);
      return d;
    });
  }

  function handleToday() {
    setWeekStart(getMonday(new Date()));
  }

  return (
    <div className="p-8 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 animate-fade-up">
        <div>
          <h1 className="font-display text-2xl font-800 text-moon">Scheman</h1>
          <p className="text-sm text-mist/50 mt-1">
            {schedules?.length ?? 0} pass denna vecka
          </p>
        </div>
        <button
          onClick={() =>
            setModal({ date: formatDateISO(new Date()), shiftType: "morning" })
          }
          className="flex items-center gap-2 h-10 px-4 rounded-lg bg-glow/90 hover:bg-glow text-abyss font-600 text-sm transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Skapa schema
        </button>
      </div>

      {/* Week navigator */}
      <div className="mb-5 animate-fade-up stagger-1">
        <WeekNavigator
          weekStart={weekStart}
          onPrev={handlePrev}
          onNext={handleNext}
          onToday={handleToday}
        />
      </div>

      {/* Calendar grid */}
      {isLoading ? (
        <div className="card-glow rounded-xl bg-ocean/60 p-8 animate-pulse">
          <div className="grid grid-cols-[80px_repeat(7,1fr)] gap-2">
            {Array.from({ length: 40 }).map((_, i) => (
              <div key={i} className="h-12 bg-mid/30 rounded-lg" />
            ))}
          </div>
        </div>
      ) : (
        <div className="animate-fade-up stagger-2">
          <WeekGrid
            weekStart={weekStart}
            schedules={schedules ?? []}
            onCreateClick={(date, shiftType) =>
              setModal({ date, shiftType })
            }
          />
        </div>
      )}

      {/* Empty state for no schedules at all */}
      {!isLoading && schedules?.length === 0 && (
        <div className="text-center mt-8 animate-fade-up stagger-3">
          <CalendarDays
            className="w-10 h-10 text-sediment mx-auto mb-3"
            strokeWidth={1}
          />
          <p className="text-sm text-sediment">
            Inga scheman denna vecka — klicka på ett tomt fält för att skapa
          </p>
        </div>
      )}

      {/* Create modal */}
      {modal && (
        <CreateScheduleModal
          defaultDate={modal.date}
          defaultShiftType={modal.shiftType}
          onClose={() => setModal(null)}
          onCreated={(id) => {
            setModal(null);
            navigate(`/schedules/${id}`);
          }}
        />
      )}
    </div>
  );
}
