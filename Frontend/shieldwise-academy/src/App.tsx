import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { PortalProvider, usePortal } from "./contexts/PortalContext";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Training from "./pages/Training";
import Assessments from "./pages/Assessments";
import Monitoring from "./pages/Monitoring";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

// Trainee pages
import MyCourses from "./pages/trainee/MyCourses";
import ExamEngine from "./pages/trainee/ExamEngine";
import MyCertificates from "./pages/trainee/MyCertificates";

// Admin pages
import UserManagement from "./pages/admin/UserManagement";
import CreateCampaign from "./pages/admin/CreateCampaign";
import AdminSettingsPage from "./pages/admin/SettingsPage";

const queryClient = new QueryClient();

const ProtectedRoutes = () => {
  const { isAuthenticated } = usePortal();
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/assessments" element={<Assessments />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/training" element={<Training />} />
        <Route path="/users" element={<UserManagement />} />
        <Route path="/settings" element={<AdminSettingsPage />} />
        <Route path="/phishing" element={<CreateCampaign />} />
        <Route path="/my-courses" element={<MyCourses />} />
        <Route path="/exam/:examId" element={<ExamEngine />} />
        <Route path="/certificates" element={<MyCertificates />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <PortalProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/*" element={<ProtectedRoutes />} />
          </Routes>
        </BrowserRouter>
      </PortalProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
