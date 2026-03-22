import { useQuery } from "@tanstack/react-query";
import { Users, Plus, Search } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";

interface EmployeeOut {
  id: string;
  user: { id: string; email: string; is_admin: boolean; is_active: boolean };
  first_name: string;
  last_name: string;
  phone: string | null;
  role: string;
  employment_type: string;
  employment_degree: number | null;
  weekly_hours: number | null;
  is_active: boolean;
  created_at: string;
}

const roleBadge: Record<string, string> = {
  admin: "bg-glow/10 text-glow border-glow/20",
  assistant_nurse: "bg-current/10 text-current border-current/20",
  care_assistant: "bg-sun/10 text-sun border-sun/20",
  employee: "bg-mist/10 text-mist border-mist/20",
};

function formatRole(role: string) {
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Employees() {
  const [search, setSearch] = useState("");

  const { data: employees, isLoading } = useQuery({
    queryKey: ["employees"],
    queryFn: () => api.get<EmployeeOut[]>("/employees/"),
  });

  const filtered =
    employees?.filter((e) => {
      const q = search.toLowerCase();
      return (
        e.first_name.toLowerCase().includes(q) ||
        e.last_name.toLowerCase().includes(q) ||
        e.user.email.toLowerCase().includes(q)
      );
    }) ?? [];

  return (
    <div className="p-8 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 animate-fade-up">
        <div>
          <h1 className="font-display text-2xl font-800 text-moon">Employees</h1>
          <p className="text-sm text-mist/50 mt-1">
            {employees?.length ?? 0} employees registered
          </p>
        </div>
        <button className="flex items-center gap-2 h-10 px-4 rounded-lg bg-glow/90 hover:bg-glow text-abyss font-600 text-sm transition-colors cursor-pointer">
          <Plus className="w-4 h-4" />
          Add employee
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-5 animate-fade-up stagger-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sediment" />
        <input
          type="text"
          placeholder="Search employees..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm h-10 pl-10 pr-4 rounded-lg bg-ocean border border-reef text-moon placeholder:text-sediment text-sm font-display focus:border-glow/50 focus:outline-none transition-colors"
        />
      </div>

      {/* Table */}
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
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Name
                </th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Email
                </th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Role
                </th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Hours / week
                </th>
                <th className="text-left px-5 py-3 text-[10px] font-600 text-mist/50 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((emp) => (
                <tr
                  key={emp.id}
                  className="border-b border-reef/30 hover:bg-mid/20 transition-colors cursor-pointer"
                >
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-mid flex items-center justify-center text-xs font-700 text-glow/80">
                        {emp.first_name[0]}
                        {emp.last_name[0]}
                      </div>
                      <span className="text-sm font-600 text-moon">
                        {emp.first_name} {emp.last_name}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-sm text-mist/60 font-data">
                    {emp.user.email}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-600 border ${roleBadge[emp.role] ?? roleBadge.employee}`}
                    >
                      {formatRole(emp.role)}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-sm text-mist/60 font-data">
                    {emp.weekly_hours ?? "—"}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center gap-1.5 text-xs ${
                        emp.is_active ? "text-kelp" : "text-sediment"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          emp.is_active ? "bg-kelp" : "bg-sediment"
                        }`}
                      />
                      {emp.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-12">
                    <Users className="w-10 h-10 text-sediment mx-auto mb-3" strokeWidth={1} />
                    <p className="text-sm text-sediment">
                      {search ? "No employees match your search" : "No employees found"}
                    </p>
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
