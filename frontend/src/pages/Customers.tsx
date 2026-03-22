import { useQuery } from "@tanstack/react-query";
import { Heart, Plus, Search } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";

interface CustomerOut {
  id: string;
  first_name: string;
  last_name: string;
  key_number: string;
  address: string;
  care_level: string | null;
  gender: string | null;
  approved_hours: number | null;
  is_active: boolean;
  created_at: string;
}

const careLevelBadge: Record<string, string> = {
  high: "bg-coral/10 text-coral border-coral/20",
  medium: "bg-sun/10 text-sun border-sun/20",
  low: "bg-kelp/10 text-kelp border-kelp/20",
};

export default function Customers() {
  const [search, setSearch] = useState("");

  const { data: customers, isLoading } = useQuery({
    queryKey: ["customers"],
    queryFn: () => api.get<CustomerOut[]>("/customers/"),
  });

  const filtered =
    customers?.filter((c) => {
      const q = search.toLowerCase();
      return (
        c.first_name.toLowerCase().includes(q) ||
        c.last_name.toLowerCase().includes(q) ||
        c.address.toLowerCase().includes(q)
      );
    }) ?? [];

  return (
    <div className="p-8 max-w-[1400px]">
      <div className="flex items-center justify-between mb-6 animate-fade-up">
        <div>
          <h1 className="font-display text-2xl font-800 text-moon">Customers</h1>
          <p className="text-sm text-mist/50 mt-1">
            {customers?.length ?? 0} care recipients
          </p>
        </div>
        <button className="flex items-center gap-2 h-10 px-4 rounded-lg bg-glow/90 hover:bg-glow text-abyss font-600 text-sm transition-colors cursor-pointer">
          <Plus className="w-4 h-4" />
          Add customer
        </button>
      </div>

      <div className="relative mb-5 animate-fade-up stagger-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sediment" />
        <input
          type="text"
          placeholder="Search customers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm h-10 pl-10 pr-4 rounded-lg bg-ocean border border-reef text-moon placeholder:text-sediment text-sm font-display focus:border-glow/50 focus:outline-none transition-colors"
        />
      </div>

      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-14 bg-ocean/60 rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="card-glow rounded-xl bg-ocean/60 overflow-hidden animate-fade-up stagger-2">
          <table className="w-full">
            <thead>
              <tr className="border-b border-reef">
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">Name</th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">Address</th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">Care Level</th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">Approved hrs/mo</th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">Key</th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((cust) => (
                <tr key={cust.id} className="border-b border-reef/30 hover:bg-mid/20 transition-colors cursor-pointer">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-mid flex items-center justify-center text-xs font-700 text-current/80">
                        {cust.first_name[0]}{cust.last_name[0]}
                      </div>
                      <span className="text-sm font-600 text-moon">{cust.first_name} {cust.last_name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-sm text-mist/60">{cust.address}</td>
                  <td className="px-5 py-3">
                    {cust.care_level ? (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-600 border capitalize ${careLevelBadge[cust.care_level] ?? ""}`}>
                        {cust.care_level}
                      </span>
                    ) : (
                      <span className="text-xs text-sediment">—</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-sm text-mist/60 font-data">{cust.approved_hours ?? "—"}</td>
                  <td className="px-5 py-3 text-sm text-mist/40 font-data">{cust.key_number}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center gap-1.5 text-xs ${cust.is_active ? "text-kelp" : "text-sediment"}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${cust.is_active ? "bg-kelp" : "bg-sediment"}`} />
                      {cust.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-12">
                    <Heart className="w-10 h-10 text-sediment mx-auto mb-3" strokeWidth={1} />
                    <p className="text-sm text-sediment">{search ? "No customers match your search" : "No customers found"}</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
