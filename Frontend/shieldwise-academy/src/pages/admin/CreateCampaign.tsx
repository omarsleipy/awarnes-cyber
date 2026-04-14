import { useState } from "react";
import { CyberButton } from "@/components/CyberButton";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import StatCard from "@/components/StatCard";
import { Crosshair, Send, MousePointerClick, ShieldAlert, Mail, Plus } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { api, mockCampaigns } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const clickRateData = [
  { dept: "Finance", rate: 18 },
  { dept: "HR", rate: 14 },
  { dept: "Engineering", rate: 6 },
  { dept: "Sales", rate: 22 },
  { dept: "Legal", rate: 8 },
  { dept: "Marketing", rate: 16 },
];

const templates = [
  { id: "password-reset", name: "Password Reset", preview: "Your corporate password expires in 24 hours. Click here to reset..." },
  { id: "it-alert", name: "IT Security Alert", preview: "Unusual login detected on your account. Verify your identity..." },
  { id: "exec-request", name: "Executive Request", preview: "Hi, I need you to purchase gift cards urgently. Reply ASAP..." },
  { id: "benefits", name: "Benefits Notice", preview: "Open enrollment is ending. Update your benefits selections now..." },
];

const CreateCampaign = () => {
  const { toast } = useToast();
  const [campaigns, setCampaigns] = useState(mockCampaigns);
  const [showCreate, setShowCreate] = useState(false);
  const [newCampaign, setNewCampaign] = useState({ name: "", template: "", targetDept: "All" });

  const handleCreate = async () => {
    const camp = await api.createCampaign(newCampaign);
    setCampaigns((prev) => [...prev, camp]);
    setShowCreate(false);
    setNewCampaign({ name: "", template: "", targetDept: "All" });
    toast({ title: "Campaign Created", description: `"${newCampaign.name}" saved as draft.` });
  };

  const totalSent = campaigns.reduce((a, c) => a + c.sent, 0);
  const totalClicked = campaigns.reduce((a, c) => a + c.clicked, 0);
  const totalReported = campaigns.reduce((a, c) => a + c.reported, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Phishing Simulation</h1>
          <p className="text-sm text-muted-foreground mt-1">Create campaigns and track click rates</p>
        </div>
        <CyberButton onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" /> New Campaign
        </CyberButton>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard title="Total Sent" value={totalSent.toString()} icon={Mail} change={`${campaigns.length} campaigns`} changeType="neutral" />
        <StatCard title="Click Rate" value={totalSent > 0 ? `${((totalClicked / totalSent) * 100).toFixed(1)}%` : "0%"} icon={MousePointerClick} change="-3.1% vs Q3" changeType="positive" />
        <StatCard title="Report Rate" value={totalSent > 0 ? `${((totalReported / totalSent) * 100).toFixed(1)}%` : "0%"} icon={ShieldAlert} change="+8% vs Q3" changeType="positive" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="stat-card rounded-xl p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Click Rate by Department</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={clickRateData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(215, 20%, 20%)" horizontal={false} />
              <XAxis type="number" tick={{ fill: "hsl(215, 16%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
              <YAxis dataKey="dept" type="category" tick={{ fill: "hsl(215, 16%, 55%)", fontSize: 11 }} axisLine={false} tickLine={false} width={80} />
              <Tooltip contentStyle={{ background: "hsl(215, 25%, 17%)", border: "1px solid hsl(215, 20%, 25%)", borderRadius: "8px", color: "hsl(210, 40%, 96%)", fontSize: 12 }} formatter={(v: number) => [`${v}%`, "Click Rate"]} />
              <Bar dataKey="rate" fill="hsl(0, 72%, 51%)" radius={[0, 4, 4, 0]} barSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="stat-card rounded-xl p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Campaigns</h3>
          <div className="space-y-3">
            {campaigns.map((c) => (
              <div key={c.id} className="flex items-center gap-3 rounded-lg bg-muted/50 px-3 py-2.5">
                <Crosshair className="h-4 w-4 text-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{c.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {c.sent > 0 ? `${c.sent} sent · ${c.clicked} clicked · ${c.reported} reported` : "Not sent yet"}
                  </p>
                </div>
                <Badge variant="outline" className={
                  c.status === "active" ? "bg-primary/20 text-primary border-primary/30" :
                  c.status === "completed" ? "bg-success/20 text-success border-success/30" :
                  "bg-muted text-muted-foreground border-border"
                }>{c.status}</Badge>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Create Campaign Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="bg-card border-border max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-foreground">Create Phishing Campaign</DialogTitle>
            <DialogDescription>Configure and launch a simulated phishing attack</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input placeholder="Campaign Name" value={newCampaign.name} onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })} className="bg-muted border-border" />
            <Select value={newCampaign.template} onValueChange={(v) => setNewCampaign({ ...newCampaign, template: v })}>
              <SelectTrigger className="bg-muted border-border"><SelectValue placeholder="Select Template" /></SelectTrigger>
              <SelectContent>
                {templates.map((t) => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
              </SelectContent>
            </Select>
            {newCampaign.template && (
              <div className="rounded-lg bg-muted/50 p-3 border border-border">
                <p className="text-xs text-muted-foreground mb-1">Preview:</p>
                <p className="text-sm text-foreground italic">{templates.find((t) => t.id === newCampaign.template)?.preview}</p>
              </div>
            )}
            <Select value={newCampaign.targetDept} onValueChange={(v) => setNewCampaign({ ...newCampaign, targetDept: v })}>
              <SelectTrigger className="bg-muted border-border"><SelectValue /></SelectTrigger>
              <SelectContent>
                {["All", "Finance", "HR", "Engineering", "Sales", "Legal", "Marketing", "IT"].map((d) => (
                  <SelectItem key={d} value={d}>{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <CyberButton variant="outline" onClick={() => setShowCreate(false)}>Cancel</CyberButton>
            <CyberButton onClick={handleCreate} disabled={!newCampaign.name || !newCampaign.template}>
              <Send className="h-4 w-4" /> Create Campaign
            </CyberButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CreateCampaign;
