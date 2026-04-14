import { useState, useEffect } from "react";
import { CyberButton } from "@/components/CyberButton";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Shield, Key, Mail, Server, Bell, Globe, CheckCircle2, Loader2 } from "lucide-react";
import { api } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const AdminSettingsPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  // SMTP
  const [smtp, setSmtp] = useState({ host: "", port: 587, username: "", password: "", encryption: "TLS", fromName: "", fromEmail: "" });
  // LDAP
  const [ldap, setLdap] = useState({ server: "", port: 389, baseDn: "", bindDn: "", bindPassword: "", userFilter: "", useSsl: false });

  useEffect(() => {
    api.getSmtpConfig().then(setSmtp);
    api.getLdapConfig().then(setLdap);
  }, []);

  const handleSaveSmtp = async () => {
    setLoading(true);
    await api.saveSmtpConfig(smtp);
    setLoading(false);
    toast({ title: "SMTP Saved", description: "Email configuration updated." });
  };

  const handleTestSmtp = async () => {
    setLoading(true);
    const res = await api.testSmtpConnection();
    setLoading(false);
    toast({ title: res.success ? "Connection OK" : "Failed", description: res.message || "SMTP test complete." });
  };

  const handleSaveLdap = async () => {
    setLoading(true);
    await api.saveLdapConfig(ldap);
    setLoading(false);
    toast({ title: "LDAP Saved", description: "Directory configuration updated." });
  };

  const handleTestLdap = async () => {
    setLoading(true);
    const res = await api.testLdapConnection();
    setLoading(false);
    toast({ title: res.success ? "Connection OK" : "Failed", description: res.success ? `${res.usersFound} users found.` : "Connection failed." });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Platform configuration and integrations</p>
      </div>

      <Tabs defaultValue="smtp" className="space-y-4">
        <TabsList className="bg-muted">
          <TabsTrigger value="smtp"><Mail className="h-4 w-4 mr-1.5" /> SMTP</TabsTrigger>
          <TabsTrigger value="ldap"><Server className="h-4 w-4 mr-1.5" /> LDAP / AD</TabsTrigger>
          <TabsTrigger value="security"><Shield className="h-4 w-4 mr-1.5" /> Security</TabsTrigger>
          <TabsTrigger value="api"><Globe className="h-4 w-4 mr-1.5" /> API</TabsTrigger>
        </TabsList>

        <TabsContent value="smtp">
          <div className="stat-card rounded-xl p-6 space-y-4 max-w-xl">
            <h3 className="text-sm font-semibold text-foreground">SMTP Configuration</h3>
            <div className="grid grid-cols-2 gap-3">
              <Input placeholder="SMTP Host" value={smtp.host} onChange={(e) => setSmtp({ ...smtp, host: e.target.value })} className="bg-muted border-border" />
              <Input placeholder="Port" type="number" value={smtp.port} onChange={(e) => setSmtp({ ...smtp, port: +e.target.value })} className="bg-muted border-border" />
            </div>
            <Input placeholder="Username" value={smtp.username} onChange={(e) => setSmtp({ ...smtp, username: e.target.value })} className="bg-muted border-border" />
            <Input placeholder="Password" type="password" value={smtp.password} onChange={(e) => setSmtp({ ...smtp, password: e.target.value })} className="bg-muted border-border" />
            <div className="grid grid-cols-2 gap-3">
              <Input placeholder="From Name" value={smtp.fromName} onChange={(e) => setSmtp({ ...smtp, fromName: e.target.value })} className="bg-muted border-border" />
              <Input placeholder="From Email" value={smtp.fromEmail} onChange={(e) => setSmtp({ ...smtp, fromEmail: e.target.value })} className="bg-muted border-border" />
            </div>
            <div className="flex gap-2">
              <CyberButton onClick={handleSaveSmtp} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Save
              </CyberButton>
              <CyberButton variant="outline" onClick={handleTestSmtp} disabled={loading}>Test Connection</CyberButton>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="ldap">
          <div className="stat-card rounded-xl p-6 space-y-4 max-w-xl">
            <h3 className="text-sm font-semibold text-foreground">LDAP / Active Directory</h3>
            <div className="grid grid-cols-2 gap-3">
              <Input placeholder="Server URL" value={ldap.server} onChange={(e) => setLdap({ ...ldap, server: e.target.value })} className="bg-muted border-border" />
              <Input placeholder="Port" type="number" value={ldap.port} onChange={(e) => setLdap({ ...ldap, port: +e.target.value })} className="bg-muted border-border" />
            </div>
            <Input placeholder="Base DN" value={ldap.baseDn} onChange={(e) => setLdap({ ...ldap, baseDn: e.target.value })} className="bg-muted border-border" />
            <Input placeholder="Bind DN" value={ldap.bindDn} onChange={(e) => setLdap({ ...ldap, bindDn: e.target.value })} className="bg-muted border-border" />
            <Input placeholder="Bind Password" type="password" value={ldap.bindPassword} onChange={(e) => setLdap({ ...ldap, bindPassword: e.target.value })} className="bg-muted border-border" />
            <Input placeholder="User Filter" value={ldap.userFilter} onChange={(e) => setLdap({ ...ldap, userFilter: e.target.value })} className="bg-muted border-border" />
            <div className="flex items-center gap-3">
              <Switch checked={ldap.useSsl} onCheckedChange={(v) => setLdap({ ...ldap, useSsl: v })} />
              <span className="text-sm text-foreground">Use SSL/TLS</span>
            </div>
            <div className="flex gap-2">
              <CyberButton onClick={handleSaveLdap} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Save
              </CyberButton>
              <CyberButton variant="outline" onClick={handleTestLdap} disabled={loading}>Test Connection</CyberButton>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="security">
          <div className="stat-card rounded-xl p-6 space-y-4 max-w-xl">
            <h3 className="text-sm font-semibold text-foreground">Security Policies</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between"><span className="text-sm text-foreground">Enforce MFA</span><Switch defaultChecked /></div>
              <div className="flex items-center justify-between"><span className="text-sm text-foreground">Session timeout (30 min)</span><Switch defaultChecked /></div>
              <div className="flex items-center justify-between"><span className="text-sm text-foreground">Password expiry (90 days)</span><Switch /></div>
              <div className="flex items-center justify-between"><span className="text-sm text-foreground">IP Whitelisting</span><Switch /></div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="api">
          <div className="stat-card rounded-xl p-6 space-y-4 max-w-xl">
            <h3 className="text-sm font-semibold text-foreground">API & Integrations</h3>
            <div className="space-y-3">
              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-xs text-muted-foreground mb-1">API Key</p>
                <code className="text-sm font-mono text-primary">cyb_live_****************************</code>
              </div>
              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-xs text-muted-foreground mb-1">Webhook Endpoint</p>
                <code className="text-sm font-mono text-foreground">https://api.corp.com/webhooks/cyberaware</code>
              </div>
            </div>
            <CyberButton variant="outline" size="sm">Regenerate API Key</CyberButton>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminSettingsPage;
