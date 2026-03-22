import { Outlet, Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import Sidebar from "../components/Sidebar";
import { useAuth } from "../hooks/useAuth";

export default function AppLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-abyss flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-glow animate-spin" />
          <p className="text-sm text-mist/60">Laddar...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen bg-abyss overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
