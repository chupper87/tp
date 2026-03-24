export const SHIFT_TYPES = ["morning", "day", "evening", "night"] as const;

export const SHIFT_LABELS: Record<string, string> = {
  morning: "Morgon",
  day: "Dag",
  evening: "Kväll",
  night: "Natt",
};

export const SHIFT_COLORS: Record<string, string> = {
  morning: "bg-sun/15 text-sun border-sun/20",
  day: "bg-current/15 text-current border-current/20",
  evening: "bg-glow/15 text-glow border-glow/20",
  night: "bg-mist/10 text-mist border-mist/20",
  custom: "bg-sediment/20 text-mist/80 border-sediment/30",
};

export const SHIFT_DOT_COLORS: Record<string, string> = {
  morning: "bg-sun",
  day: "bg-current",
  evening: "bg-glow",
  night: "bg-mist",
  custom: "bg-sediment",
};

export const TIME_OF_DAY_LABELS: Record<string, string> = {
  morning: "Morgon",
  midday: "Mitt på dagen",
  afternoon: "Eftermiddag",
  evening: "Kväll",
  night: "Natt",
};

export const WEEKDAY_LABELS = ["Mån", "Tis", "Ons", "Tor", "Fre", "Lör", "Sön"];

// --- Date utilities ---

export function getMonday(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function getWeekDates(monday: Date): Date[] {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

export function getISOWeekNumber(date: Date): number {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

export function formatDateISO(date: Date): string {
  return date.toISOString().split("T")[0];
}

export function isToday(date: Date): boolean {
  const now = new Date();
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  );
}

// --- Timeline utilities ---

export const SHIFT_TIME_BOUNDARIES: Record<string, { start: string; end: string }> = {
  morning: { start: "06:00", end: "14:00" },
  day: { start: "08:00", end: "16:00" },
  evening: { start: "14:00", end: "22:00" },
  night: { start: "22:00", end: "06:00" },
};

/** Parse "HH:MM" or "HH:MM:SS" into total minutes since midnight. */
export function timeToMinutes(timeStr: string): number {
  const [h, m] = timeStr.split(":").map(Number);
  return h * 60 + m;
}

/** Convert minutes since midnight to "HH:MM" string. */
export function minutesToTime(minutes: number): string {
  const m = ((minutes % (24 * 60)) + 24 * 60) % (24 * 60);
  const hh = String(Math.floor(m / 60)).padStart(2, "0");
  const mm = String(m % 60).padStart(2, "0");
  return `${hh}:${mm}`;
}

/** Get shift duration in minutes, handling midnight wrap. */
export function shiftDurationMinutes(startStr: string, endStr: string): number {
  const start = timeToMinutes(startStr);
  const end = timeToMinutes(endStr);
  if (end > start) return end - start;
  return 24 * 60 - start + end;
}

/** Get position (0–100%) of a time within a shift. */
export function timePositionPercent(
  timeStr: string,
  shiftStart: string,
  shiftEnd: string,
): number {
  const total = shiftDurationMinutes(shiftStart, shiftEnd);
  if (total === 0) return 0;
  const start = timeToMinutes(shiftStart);
  const t = timeToMinutes(timeStr);
  let offset = t - start;
  if (offset < 0) offset += 24 * 60;
  return (offset / total) * 100;
}

/** Get width (0–100%) for a duration within a shift. */
export function durationWidthPercent(
  durationMin: number,
  shiftStart: string,
  shiftEnd: string,
): number {
  const total = shiftDurationMinutes(shiftStart, shiftEnd);
  if (total === 0) return 0;
  return (durationMin / total) * 100;
}
