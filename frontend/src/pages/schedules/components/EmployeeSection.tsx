import { X, Loader2, AlertCircle } from "lucide-react";
import { useRemoveEmployee } from "../hooks";
import type { ScheduleEmployeeOut } from "../types";
import type { ApiError } from "../../../api/client";
import DroppableZone from "./DroppableZone";

interface EmployeeSectionProps {
  scheduleId: string;
  employees: ScheduleEmployeeOut[];
  assignError: ApiError | null;
}

export default function EmployeeSection({
  scheduleId,
  employees,
  assignError,
}: EmployeeSectionProps) {
  const remove = useRemoveEmployee(scheduleId);

  return (
    <DroppableZone
      id="employee-drop"
      zone="employees"
      accepts={["employee"]}
      className="card-glow bg-ocean/60 p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-600 text-moon">
          Anställda ({employees.length})
        </h3>
      </div>

      {assignError && (
        <div className="flex items-start gap-2 p-2 rounded-lg bg-coral/10 border border-coral/20 mb-3">
          <AlertCircle className="w-3.5 h-3.5 text-coral mt-0.5 shrink-0" />
          <p className="text-xs text-coral">{assignError.detail}</p>
        </div>
      )}

      <div className="space-y-1.5">
        {employees.map((se) => (
          <div
            key={se.employee_id}
            className="flex items-center gap-2 h-8 px-3 rounded-lg bg-mid/20"
          >
            <span className="text-sm text-mist/80 flex-1 truncate">
              {se.employee.first_name} {se.employee.last_name}
            </span>
            <button
              onClick={() =>
                remove.mutate({ employee_id: se.employee_id })
              }
              disabled={remove.isPending}
              className="text-sediment hover:text-coral transition-colors cursor-pointer disabled:opacity-50"
            >
              {remove.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <X className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        ))}
        {employees.length === 0 && (
          <p className="text-xs text-sediment py-1">
            Dra anställda hit eller sök nedan
          </p>
        )}
      </div>
    </DroppableZone>
  );
}
