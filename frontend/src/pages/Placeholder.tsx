import { Construction } from "lucide-react";
import { useLocation } from "react-router-dom";

export default function Placeholder() {
  const location = useLocation();
  const name = location.pathname
    .split("/")
    .filter(Boolean)
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(" / ") || "Page";

  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div className="text-center animate-fade-up">
        <div className="w-16 h-16 rounded-2xl bg-ocean/60 border border-reef flex items-center justify-center mx-auto mb-5">
          <Construction className="w-7 h-7 text-mist/30" strokeWidth={1.5} />
        </div>
        <h2 className="font-display text-lg font-700 text-moon mb-2">{name}</h2>
        <p className="text-sm text-sediment max-w-xs">
          This section is under development. The API is ready — the UI is coming next.
        </p>
      </div>
    </div>
  );
}
