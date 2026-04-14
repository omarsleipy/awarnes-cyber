import StatCard from "@/components/StatCard";
import { CyberButton } from "@/components/CyberButton";
import {
  Users,
  ShieldCheck,
  AlertTriangle,
  GraduationCap,
  TrendingUp,
  Crosshair,
  ArrowRight,
  Activity,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
} from "recharts";

const trainingData = [
  { month: "Jan", completed: 45, pending: 12 },
  { month: "Feb", completed: 52, pending: 8 },
  { month: "Mar", completed: 61, pending: 15 },
  { month: "Apr", completed: 58, pending: 10 },
  { month: "May", completed: 73, pending: 6 },
  { month: "Jun", completed: 82, pending: 4 },
];

const phishingData = [
  { name: "Clicked", value: 12, color: "hsl(0, 72%, 51%)" },
  { name: "Reported", value: 58, color: "hsl(142, 76%, 36%)" },
  { name: "Ignored", value: 30, color: "hsl(38, 92%, 50%)" },
];

const threatData = [
  { day: "Mon", threats: 3 },
  { day: "Tue", threats: 7 },
  { day: "Wed", threats: 2 },
  { day: "Thu", threats: 5 },
  { day: "Fri", threats: 1 },
  { day: "Sat", threats: 0 },
  { day: "Sun", threats: 1 },
];

const recentActivity = [
  { user: "John D.", action: "Completed Phishing Module", time: "2 min ago", status: "success" },
  { user: "Sarah M.", action: "Failed exam attempt (2/3)", time: "15 min ago", status: "warning" },
  { user: "Alex K.", action: "Tab switch warning issued", time: "32 min ago", status: "danger" },
  { user: "Maria L.", action: "Certificate generated", time: "1 hr ago", status: "success" },
  { user: "David R.", action: "Account provisioned via CSV", time: "2 hrs ago", status: "neutral" },
];

const Dashboard = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Security Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Enterprise cybersecurity awareness overview
          </p>
        </div>
        <CyberButton>
          Generate Report <ArrowRight className="h-4 w-4" />
        </CyberButton>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Users"
          value="1,247"
          change="+43 this month"
          changeType="positive"
          icon={Users}
          className="animate-fade-in"
        />
        <StatCard
          title="Compliance Rate"
          value="87%"
          change="+5.2% vs last month"
          changeType="positive"
          icon={ShieldCheck}
          className="animate-fade-in [animation-delay:100ms]"
        />
        <StatCard
          title="Phishing Click Rate"
          value="12%"
          change="-3.1% vs last month"
          changeType="positive"
          icon={Crosshair}
          className="animate-fade-in [animation-delay:200ms]"
        />
        <StatCard
          title="Active Threats"
          value="3"
          change="2 critical"
          changeType="negative"
          icon={AlertTriangle}
          className="animate-fade-in [animation-delay:300ms]"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Training Completion Chart */}
        <div className="stat-card rounded-xl p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Training Completion</h3>
              <p className="text-xs text-muted-foreground">Monthly overview</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-primary" />
                Completed
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-warning" />
                Pending
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={trainingData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215, 20%, 20%)" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: "hsl(215, 16%, 55%)", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "hsl(215, 16%, 55%)", fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: "hsl(215, 25%, 17%)",
                  border: "1px solid hsl(215, 20%, 25%)",
                  borderRadius: "8px",
                  color: "hsl(210, 40%, 96%)",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="completed" fill="hsl(188, 95%, 43%)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="pending" fill="hsl(38, 92%, 50%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Phishing Results */}
        <div className="stat-card rounded-xl p-5">
          <h3 className="text-sm font-semibold text-foreground mb-1">Phishing Simulation</h3>
          <p className="text-xs text-muted-foreground mb-4">Last campaign results</p>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={phishingData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={75}
                paddingAngle={3}
                dataKey="value"
              >
                {phishingData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "hsl(215, 25%, 17%)",
                  border: "1px solid hsl(215, 20%, 25%)",
                  borderRadius: "8px",
                  color: "hsl(210, 40%, 96%)",
                  fontSize: 12,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 text-xs">
            {phishingData.map((entry) => (
              <span key={entry.name} className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: entry.color }} />
                {entry.name} ({entry.value}%)
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Threat Trend */}
        <div className="stat-card rounded-xl p-5">
          <div className="mb-4 flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Threat Trend</h3>
          </div>
          <ResponsiveContainer width="100%" height={140}>
            <AreaChart data={threatData}>
              <defs>
                <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(188, 95%, 43%)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="hsl(188, 95%, 43%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" tick={{ fill: "hsl(215, 16%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Area type="monotone" dataKey="threats" stroke="hsl(188, 95%, 43%)" fill="url(#threatGrad)" strokeWidth={2} />
              <Tooltip
                contentStyle={{
                  background: "hsl(215, 25%, 17%)",
                  border: "1px solid hsl(215, 20%, 25%)",
                  borderRadius: "8px",
                  color: "hsl(210, 40%, 96%)",
                  fontSize: 12,
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Activity */}
        <div className="stat-card rounded-xl p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Recent Activity</h3>
            <CyberButton variant="ghost" size="sm">View All</CyberButton>
          </div>
          <div className="space-y-3">
            {recentActivity.map((item, idx) => (
              <div key={idx} className="flex items-center gap-3 rounded-lg bg-muted/50 px-3 py-2.5">
                <div className={`h-2 w-2 rounded-full ${
                  item.status === "success" ? "bg-success" :
                  item.status === "warning" ? "bg-warning" :
                  item.status === "danger" ? "bg-destructive" :
                  "bg-muted-foreground"
                }`} />
                <span className="text-sm font-medium text-foreground min-w-[80px]">{item.user}</span>
                <span className="flex-1 text-sm text-muted-foreground">{item.action}</span>
                <span className="text-xs text-muted-foreground">{item.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
