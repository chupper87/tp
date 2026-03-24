import { useState, useRef, useEffect } from "react";
import { Search, X } from "lucide-react";

interface Person {
  id: string;
  first_name: string;
  last_name: string;
}

interface PersonSearchDropdownProps<T extends Person> {
  items: T[];
  excludeIds: Set<string>;
  placeholder: string;
  onSelect: (item: T) => void;
  renderExtra?: (item: T) => React.ReactNode;
}

export default function PersonSearchDropdown<T extends Person>({
  items,
  excludeIds,
  placeholder,
  onSelect,
  renderExtra,
}: PersonSearchDropdownProps<T>) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const filtered = items.filter((item) => {
    if (excludeIds.has(item.id)) return false;
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      item.first_name.toLowerCase().includes(q) ||
      item.last_name.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setQuery("");
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }
  }, [open]);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 text-xs text-glow/70 hover:text-glow transition-colors cursor-pointer"
      >
        <span className="w-5 h-5 rounded-full border border-dashed border-glow/40 flex items-center justify-center">
          +
        </span>
        {placeholder}
      </button>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="flex items-center gap-2 h-8 px-3 rounded-lg bg-deep border border-reef focus-within:border-glow/50 transition-colors">
        <Search className="w-3.5 h-3.5 text-sediment shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="flex-1 bg-transparent text-sm text-moon placeholder:text-sediment outline-none"
        />
        <button
          onClick={() => {
            setOpen(false);
            setQuery("");
          }}
          className="text-sediment hover:text-moon transition-colors cursor-pointer"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Dropdown */}
      <div className="absolute z-10 top-full left-0 right-0 mt-1 rounded-lg bg-deep border border-reef shadow-lg max-h-48 overflow-y-auto">
        {filtered.length === 0 ? (
          <p className="px-3 py-2 text-xs text-sediment">Inga resultat</p>
        ) : (
          filtered.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                onSelect(item);
                setOpen(false);
                setQuery("");
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-mist/80 hover:bg-mid/40 hover:text-moon transition-colors text-left cursor-pointer"
            >
              <span>
                {item.first_name} {item.last_name}
              </span>
              {renderExtra?.(item)}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
