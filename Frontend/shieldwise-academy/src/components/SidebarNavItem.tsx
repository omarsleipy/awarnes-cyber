import { cn } from "@/lib/utils";
import { NavLink as RouterNavLink } from "react-router-dom";
import { LucideIcon } from "lucide-react";

interface SidebarNavItemProps {
  to: string;
  icon: LucideIcon;
  label: string;
  badge?: string | number;
}

const SidebarNavItem = ({ to, icon: Icon, label, badge }: SidebarNavItemProps) => {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
          isActive
            ? "bg-primary/10 text-primary cyber-border"
            : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        )
      }
    >
      <Icon className="h-4.5 w-4.5 shrink-0" />
      <span className="flex-1">{label}</span>
      {badge !== undefined && (
        <span className="rounded-full bg-primary/20 px-2 py-0.5 text-xs font-semibold text-primary">
          {badge}
        </span>
      )}
    </RouterNavLink>
  );
};

export default SidebarNavItem;
