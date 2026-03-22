import { NavLink, useNavigate } from "react-router-dom";
import {
  Clock,
  LayoutDashboard,
  Users,
  Heart,
  ListChecks,
  CalendarDays,
  ClipboardCheck,
  CalendarOff,
  BarChart3,
  ScrollText,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth";

interface NavItem {
  to: string;
  icon: React.ElementType;
  label: string;
}

const adminNav: NavItem[] = [
  { to: "/", icon: LayoutDashboard, label: "Översikt" },
  { to: "/employees", icon: Users, label: "Anställda" },
  { to: "/customers", icon: Heart, label: "Kunder" },
  { to: "/measures", icon: ListChecks, label: "Insatser" },
  { to: "/schedules", icon: CalendarDays, label: "Scheman" },
  { to: "/visits", icon: ClipboardCheck, label: "Besök" },
  { to: "/absences", icon: CalendarOff, label: "Frånvaro" },
  { to: "/reports", icon: BarChart3, label: "Rapporter" },
  { to: "/audit", icon: ScrollText, label: "Händelselogg" },
];

const employeeNav: NavItem[] = [
  { to: "/", icon: LayoutDashboard, label: "Översikt" },
  { to: "/my/schedule", icon: CalendarDays, label: "Mitt schema" },
  { to: "/my/visits", icon: ClipboardCheck, label: "Mina besök" },
  { to: "/my/absences", icon: CalendarOff, label: "Min frånvaro" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();
  const navItems = isAdmin ? adminNav : employeeNav;

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <aside
      className={`${
        collapsed ? "w-[72px]" : "w-[240px]"
      } h-screen bg-deep border-r border-reef flex flex-col transition-all duration-300 ease-in-out shrink-0`}
    >
      {/* Brand */}
      <div className="h-16 flex items-center px-5 border-b border-reef">
        <Clock className="w-6 h-6 text-glow shrink-0" strokeWidth={1.5} />
        {!collapsed && (
          <span className="ml-3 font-display font-800 text-sm tracking-[0.15em] text-moon uppercase">
            Timepiece
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 h-10 rounded-lg transition-all duration-200 group ${
                collapsed ? "justify-center px-0" : "px-3"
              } ${
                isActive
                  ? "bg-glow/10 text-glow"
                  : "text-mist/60 hover:text-moon hover:bg-mid/60"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={`w-[18px] h-[18px] shrink-0 ${
                    isActive ? "text-glow" : "text-mist/40 group-hover:text-mist/80"
                  }`}
                  strokeWidth={isActive ? 2 : 1.5}
                />
                {!collapsed && (
                  <span className="text-sm font-500 truncate">{item.label}</span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-reef p-3 space-y-1">
        {/* User info */}
        {!collapsed && user && (
          <div className="px-3 py-2 mb-1">
            <p className="text-xs text-mist/80 truncate">{user.email}</p>
            <p className="text-[10px] text-sediment uppercase tracking-wider mt-0.5">
              {isAdmin ? "Administratör" : "Anställd"}
            </p>
          </div>
        )}

        {/* Logout */}
        <button
          onClick={handleLogout}
          className={`flex items-center gap-3 h-10 w-full rounded-lg text-mist/40 hover:text-coral hover:bg-coral/5 transition-all duration-200 cursor-pointer ${
            collapsed ? "justify-center px-0" : "px-3"
          }`}
        >
          <LogOut className="w-[18px] h-[18px] shrink-0" strokeWidth={1.5} />
          {!collapsed && <span className="text-sm font-500">Logga ut</span>}
        </button>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`flex items-center gap-3 h-10 w-full rounded-lg text-sediment hover:text-mist/60 hover:bg-mid/40 transition-all duration-200 cursor-pointer ${
            collapsed ? "justify-center px-0" : "px-3"
          }`}
        >
          {collapsed ? (
            <ChevronRight className="w-[18px] h-[18px]" strokeWidth={1.5} />
          ) : (
            <>
              <ChevronLeft className="w-[18px] h-[18px]" strokeWidth={1.5} />
              <span className="text-sm font-500">Minimera</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
