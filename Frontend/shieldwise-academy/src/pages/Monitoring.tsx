import StatCard from "@/components/StatCard";
import { CyberButton } from "@/components/CyberButton";
import { Badge } from "@/components/ui/badge";
import { Shield, Activity, AlertTriangle, Eye, Wifi, Monitor } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";

const activityData = [
  { time: "00:00", events: 12 },
  { time: "04:00", events: 5 },
  { time: "08:00", events: 45 },
  { time: "12:00", events: 78 },
  { time: "16:00", events: 62 },
  { time: "20:00", events: 23 },
  { time: "23:59", events: 8 },
];

const alerts = [
  { id: 1, type: "critical", title: "Unauthorized access attempt", user: "Unknown", ip: "192.168.1.45", time: "2 min ago" },
  { id: 2, type: "warning", title: "Multiple failed login attempts", user: "john.doe", ip: "10.0.0.22", time: "18 min ago" },
  { id: 3, type: "warning", title: "Exam tab switch detected (2/3)", user: "sarah.m", ip: "10.0.0.58", time: "32 min ago" },
  { id: 4, type: "info", title: "USB device connected during exam", user: "alex.k", ip: "10.0.0.91", time: "1 hr ago" },
  { id: 5, type: "critical", title: "Data exfiltration pattern detected", user: "guest_12", ip: "172.16.0.5", time: "2 hrs ago" },
];

const Monitoring = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Behavioral Monitoring</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time suspicious activity tracking</p>
        </div>
        <CyberButton variant="outline">
          <Eye className="h-4 w-4" /> Live View
        </CyberButton>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard title="Active Sessions" value="142" icon={Monitor} change="12 during exams" changeType="neutral" />
        <StatCard title="Alerts Today" value="7" icon={AlertTriangle} change="2 critical" changeType="negative" />
        <StatCard title="Network Events" value="1,293" icon={Wifi} change="Normal baseline" changeType="positive" />
      </div>

      {/* Activity Chart */}
      <div className="stat-card rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Network Activity (24h)</h3>
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

      {/* Alerts */}
      <div className="stat-card rounded-xl p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">Security Alerts</h3>
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-center gap-3 rounded-lg bg-muted/50 px-4 py-3">
              <div className={`h-2.5 w-2.5 rounded-full shrink-0 ${
                alert.type === "critical" ? "bg-destructive animate-pulse" :
                alert.type === "warning" ? "bg-warning" : "bg-primary"
              }`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{alert.title}</p>
                <p className="text-xs text-muted-foreground">
                  User: {alert.user} · IP: <span className="font-mono">{alert.ip}</span>
                </p>
              </div>
              <span className="text-xs text-muted-foreground whitespace-nowrap">{alert.time}</span>
              <Badge variant="outline" className={
                alert.type === "critical" ? "bg-destructive/20 text-destructive border-destructive/30" :
                alert.type === "warning" ? "bg-warning/20 text-warning border-warning/30" :
                "bg-primary/20 text-primary border-primary/30"
              }>
                {alert.type}
              </Badge>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Monitoring;
