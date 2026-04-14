import { Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  GraduationCap,
  ClipboardCheck,
  Crosshair,
  Users,
  Shield,
  Settings,
  Bell,
  Search,
  ChevronDown,
  ShieldAlert,
  Award,
  BookOpen,
  ArrowLeftRight,
  LogOut,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import SidebarNavItem from "./SidebarNavItem";
import { usePortal } from "@/contexts/PortalContext";

const AppLayout = () => {
  const { role, setRole, userName, userEmail, logout } = usePortal();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r border-sidebar-border bg-sidebar">
        {/* Logo */}
        <div className="flex items-center gap-3 border-b border-sidebar-border px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg cyber-gradient">
            <ShieldAlert className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-base font-bold text-foreground tracking-tight">CyberAware</h1>
            <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
              {role === "admin" ? "Admin Portal" : "Trainee Portal"}
            </p>
          </div>
        </div>

        {/* Portal Toggle */}
        <div className="px-3 pt-3">
          <button
            onClick={() => setRole(role === "admin" ? "trainee" : "admin")}
            className="flex w-full items-center gap-2 rounded-lg bg-primary/10 px-3 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary/20"
          >
            <ArrowLeftRight className="h-3.5 w-3.5" />
            Switch to {role === "admin" ? "Trainee" : "Admin"} Portal
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {role === "admin" ? (
            <>
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Overview</p>
              <SidebarNavItem to="/" icon={LayoutDashboard} label="Dashboard" />

              <p className="mb-2 mt-6 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Training</p>
              <SidebarNavItem to="/training" icon={GraduationCap} label="Courses" badge={3} />
              <SidebarNavItem to="/assessments" icon={ClipboardCheck} label="Assessments" />

              <p className="mb-2 mt-6 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Security</p>
              <SidebarNavItem to="/phishing" icon={Crosshair} label="Phishing Sim" />
              <SidebarNavItem to="/monitoring" icon={Shield} label="Monitoring" />

              <p className="mb-2 mt-6 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Admin</p>
              <SidebarNavItem to="/users" icon={Users} label="Users" />
              <SidebarNavItem to="/settings" icon={Settings} label="Settings" />
            </>
          ) : (
            <>
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Learning</p>
              <SidebarNavItem to="/my-courses" icon={BookOpen} label="My Courses" />
              <SidebarNavItem to="/assessments" icon={ClipboardCheck} label="Assessments" />
              <SidebarNavItem to="/certificates" icon={Award} label="Certificates" />
            </>
          )}
        </nav>

        {/* User */}
        <div className="border-t border-sidebar-border p-3">
          <div className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-sidebar-accent transition-colors cursor-pointer">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
              {userName.split(" ").map((n) => n[0]).join("")}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{userName}</p>
              <p className="text-[11px] text-muted-foreground truncate">{userEmail}</p>
            </div>
            <button
              onClick={() => { logout(); navigate("/login"); }}
              className="p-1.5 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="flex h-14 items-center justify-between border-b border-border bg-background/80 backdrop-blur-sm px-6">
          <div className="flex items-center gap-3 rounded-lg bg-muted px-3 py-1.5 w-80">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              placeholder="Search users, courses, reports..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
            />
            <kbd className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">⌘K</kbd>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative rounded-lg p-2 hover:bg-muted transition-colors">
              <Bell className="h-4.5 w-4.5 text-muted-foreground" />
              <span className="absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full bg-destructive border-2 border-background" />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
