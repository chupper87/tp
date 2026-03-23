import { useState } from "react";
import { Search, ChevronDown, ChevronUp } from "lucide-react";

interface ResourcePoolProps {
  title: string;
  count: number;
  children: React.ReactNode;
  onSearch: (query: string) => void;
  placeholder: string;
}

export default function ResourcePool({
  title,
  count,
  children,
  onSearch,
  placeholder,
}: ResourcePoolProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [query, setQuery] = useState("");

  function handleSearch(value: string) {
    setQuery(value);
    onSearch(value);
  }

  return (
    <div className="card-glow rounded-xl bg-ocean/60">
      {/* Header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-3 py-2.5 cursor-pointer"
      >
        <span className="text-xs font-600 text-moon uppercase tracking-wider">
          {title}
          <span className="text-sediment font-400 ml-1.5 normal-case tracking-normal">
            ({count})
          </span>
        </span>
        {collapsed ? (
          <ChevronDown className="w-3.5 h-3.5 text-sediment" />
        ) : (
          <ChevronUp className="w-3.5 h-3.5 text-sediment" />
        )}
      </button>

      {!collapsed && (
        <>
          {/* Search */}
          <div className="px-2.5 pb-2">
            <div className="flex items-center gap-2 h-7 px-2 rounded-md bg-deep border border-reef/40 focus-within:border-glow/50 transition-colors">
              <Search className="w-3 h-3 text-sediment shrink-0" />
              <input
                type="text"
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder={placeholder}
                className="flex-1 bg-transparent text-xs text-moon placeholder:text-sediment outline-none"
              />
            </div>
          </div>

          {/* Items */}
          <div className="px-2.5 pb-2.5 space-y-1 max-h-64 overflow-y-auto">
            {children}
          </div>
        </>
      )}
    </div>
  );
}
