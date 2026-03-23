import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AppLayout from "./layouts/AppLayout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Employees from "./pages/Employees";
import Customers from "./pages/Customers";
import Placeholder from "./pages/Placeholder";
import ScheduleList from "./pages/schedules/ScheduleList";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        // Don't retry auth errors
        if (error && "status" in error && (error.status === 401 || error.status === 403)) {
          return false;
        }
        return failureCount < 2;
      },
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="employees" element={<Employees />} />
            <Route path="customers" element={<Customers />} />
            <Route path="measures" element={<Placeholder />} />
            <Route path="schedules" element={<ScheduleList />} />
            <Route path="schedules/:id" element={<Placeholder />} />
            <Route path="visits" element={<Placeholder />} />
            <Route path="absences" element={<Placeholder />} />
            <Route path="reports" element={<Placeholder />} />
            <Route path="audit" element={<Placeholder />} />
            {/* Employee self-service */}
            <Route path="my/schedule" element={<Placeholder />} />
            <Route path="my/visits" element={<Placeholder />} />
            <Route path="my/absences" element={<Placeholder />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
