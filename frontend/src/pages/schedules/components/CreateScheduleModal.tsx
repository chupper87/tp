import { useState, type FormEvent } from "react";
import { X, Loader2, AlertCircle } from "lucide-react";
import { SHIFT_TYPES, SHIFT_LABELS, SHIFT_COLORS } from "../constants";
import { useCreateSchedule } from "../hooks";
import type { ApiError } from "../../../api/client";

interface CreateScheduleModalProps {
  defaultDate: string;
  defaultShiftType?: string;
  onClose: () => void;
  onCreated: (id: string) => void;
}

export default function CreateScheduleModal({
  defaultDate,
  defaultShiftType,
  onClose,
  onCreated,
}: CreateScheduleModalProps) {
  const [date, setDate] = useState(defaultDate);
  const [shiftType, setShiftType] = useState<string>(defaultShiftType ?? "morning");
  const [isCustom, setIsCustom] = useState(!defaultShiftType || !SHIFT_TYPES.includes(defaultShiftType as typeof SHIFT_TYPES[number]));
  const [customShift, setCustomShift] = useState("");

  const createSchedule = useCreateSchedule();
  const error = createSchedule.error as ApiError | null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      const result = await createSchedule.mutateAsync({
        date,
        ...(isCustom
          ? { custom_shift: customShift }
          : { shift_type: shiftType }),
      });
      onCreated(result.id);
    } catch {
      // error captured in mutation state
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-abyss/80 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="card-glow rounded-2xl bg-ocean/95 p-6 w-full max-w-md animate-fade-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-display font-700 text-moon">Nytt schema</h2>
          <button
            onClick={onClose}
            className="text-sediment hover:text-moon transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="flex items-start gap-3 p-3 rounded-lg bg-coral/10 border border-coral/20">
              <AlertCircle className="w-4 h-4 text-coral mt-0.5 shrink-0" />
              <p className="text-sm text-coral">{error.detail}</p>
            </div>
          )}

          {/* Date */}
          <div>
            <label className="block text-xs font-600 text-mist/80 uppercase tracking-wider mb-2">
              Datum
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="w-full h-10 px-4 rounded-lg bg-deep border border-reef text-moon text-sm font-display focus:border-glow/50 focus:outline-none transition-colors"
            />
          </div>

          {/* Shift type */}
          <div>
            <label className="block text-xs font-600 text-mist/80 uppercase tracking-wider mb-2">
              Passtyp
            </label>
            <div className="grid grid-cols-2 gap-2">
              {SHIFT_TYPES.map((st) => {
                const active = !isCustom && shiftType === st;
                const colors = SHIFT_COLORS[st];
                return (
                  <button
                    key={st}
                    type="button"
                    onClick={() => {
                      setIsCustom(false);
                      setShiftType(st);
                    }}
                    className={`h-9 rounded-lg text-xs font-600 border transition-all cursor-pointer ${
                      active
                        ? colors
                        : "bg-mid/20 border-reef/40 text-mist/50 hover:border-reef-light"
                    }`}
                  >
                    {SHIFT_LABELS[st]}
                  </button>
                );
              })}
            </div>
            <button
              type="button"
              onClick={() => setIsCustom(true)}
              className={`mt-2 w-full h-9 rounded-lg text-xs font-600 border transition-all cursor-pointer ${
                isCustom
                  ? "bg-sediment/20 text-mist/80 border-sediment/30"
                  : "bg-mid/20 border-reef/40 text-mist/50 hover:border-reef-light"
              }`}
            >
              Anpassat
            </button>
          </div>

          {/* Custom shift name */}
          {isCustom && (
            <div>
              <label className="block text-xs font-600 text-mist/80 uppercase tracking-wider mb-2">
                Anpassat passnamn
              </label>
              <input
                type="text"
                value={customShift}
                onChange={(e) => setCustomShift(e.target.value)}
                required
                maxLength={50}
                placeholder="T.ex. Extra 09-12"
                className="w-full h-10 px-4 rounded-lg bg-deep border border-reef text-moon placeholder:text-sediment text-sm font-display focus:border-glow/50 focus:outline-none transition-colors"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 h-10 rounded-lg border border-reef text-mist/60 hover:text-moon hover:border-reef-light text-sm font-600 transition-colors cursor-pointer"
            >
              Avbryt
            </button>
            <button
              type="submit"
              disabled={createSchedule.isPending}
              className="flex-1 h-10 rounded-lg bg-glow/90 hover:bg-glow text-abyss font-700 text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
            >
              {createSchedule.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Skapa"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
