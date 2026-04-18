import { useEffect, useState } from "react";
import StatCard from "@/components/StatCard";
import { CyberButton } from "@/components/CyberButton";
import { Badge } from "@/components/ui/badge";
import { Shield, Activity, AlertTriangle, Eye, Wifi, Monitor, Loader2 } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { api } from "@/services/api";

type ActivityRow = Awaited<ReturnType<typeof api.getMonitoringActivities>>[number];

const activityData = [
  { time: "00:00", events: 12 },
  { time: "04:00", events: 5 },
  { time: "08:00", events: 45 },
  { time: "12:00", events: 78 },
  { time: "16:00", events: 62 },
  { time: "20:00", events: 23 },
  { time: "23:59", events: 8 },
];

function severityBadgeVariant(sev: string): "destructive" | "default" | "secondary" | "outline" {
  if (sev === "critical") return "destructive";
  if (sev === "warning") return "secondary";
  return "outline";
}

const Monitoring = () => {
  const [rows, setRows] = useState<ActivityRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const data = await api.getMonitoringActivities();
      if (!cancelled) {
        setRows(data);
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const criticalCount = rows.filter((r) => r.severity === "critical").length;
  const phishingCount = rows.filter((r) => r.activity_type.startsWith("phishing_")).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Behavioral Monitoring</h1>
          <p className="text-sm text-muted-foreground mt-1">Suspicious activity and phishing simulation events for your organization</p>
        </div>
        <CyberButton variant="outline" disabled={loading} onClick={() => api.getMonitoringActivities().then(setRows)}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />} Refresh
        </CyberButton>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard title="Events loaded" value={String(rows.length)} icon={Monitor} change="From API" changeType="neutral" />
        <StatCard title="Critical" value={String(criticalCount)} icon={AlertTriangle} change="Includes phishing clicks" changeType="negative" />
        <StatCard title="Phishing module" value={String(phishingCount)} icon={Shield} change="Link / pixel / credential" changeType="neutral" />
      </div>

      {/* Activity Chart (placeholder aggregate — hook to analytics later) */}
      <div className="stat-card rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Network Activity (sample 24h)</h3>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={activityData}>
            <defs>
              <linearGradient id="actGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(188, 95%, 43%)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(188, 95%, 43%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(215, 20%, 20%)" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: "hsl(215, 16%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "hsl(215, 16%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: "hsl(215, 25%, 17%)", border: "1px solid hsl(215, 20%, 25%)", borderRadius: "8px", color: "hsl(210, 40%, 96%)", fontSize: 12 }} />
            <Area type="monotone" dataKey="events" stroke="hsl(188, 95%, 43%)" fill="url(#actGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Live alerts from backend */}
      <div className="stat-card rounded-xl p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">Security alerts (your organization)</h3>
        {loading ? (
          <div className="flex items-center gap-2 text-muted-foreground text-sm py-8 justify-center">
            <Loader2 className="h-5 w-5 animate-spin" /> Loading events…
          </div>
        ) : rows.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">No suspicious activity recorded yet.</p>
        ) : (
          <div className="space-y-2 max-h-[480px] overflow-y-auto">
            {rows.map((alert) => (
              <div key={alert.id} className="flex flex-col gap-1 rounded-lg bg-muted/50 px-4 py-3 sm:flex-row sm:items-start sm:gap-3">
                <div
                  className={`h-2.5 w-2.5 rounded-full shrink-0 mt-1.5 ${
                    alert.severity === "critical" ? "bg-destructive animate-pulse" :
                    alert.severity === "warning" ? "bg-warning" : "bg-primary"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{alert.title}</p>
                  <p className="text-xs text-muted-foreground font-mono mt-0.5">{alert.activity_type}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    User ID: {alert.user_id ?? "—"} · IP: <span className="font-mono">{alert.ip_address ?? "—"}</span>
                  </p>
                  {alert.details && (
                    <p className="text-xs text-muted-foreground mt-1 break-words">{alert.details}</p>
                  )}
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap sm:self-center">
                  {alert.created_at ? new Date(alert.created_at).toLocaleString() : ""}
                </span>
                <Badge variant={severityBadgeVariant(alert.severity)} className="shrink-0 sm:self-center capitalize">
                  {alert.severity}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Wifi className="h-3 w-3" />
        Phishing tracks: link → <code className="text-[10px]">/api/phishing/track/&lt;token&gt;</code>, pixel →{" "}
        <code className="text-[10px]">.../open.png</code>, credentials → POST{" "}
        <code className="text-[10px]">.../credential</code>
      </div>
    </div>
  );
};

export default Monitoring;
