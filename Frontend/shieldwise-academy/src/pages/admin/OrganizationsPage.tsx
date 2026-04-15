import { useEffect, useState } from "react";
import { CyberButton } from "@/components/CyberButton";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { api, type Organization } from "@/services/api";

const OrganizationsPage = () => {
  const { toast } = useToast();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [newName, setNewName] = useState("");
  const [ldapForms, setLdapForms] = useState<
    Record<string, { ldapServer: string; ldapPort: number; ldapBaseDn: string; ldapBindDn: string; ldapBindPassword: string; ldapUserFilter: string; ldapUseSsl: boolean }>
  >({});

  const loadOrganizations = async () => {
    const rows = await api.getOrganizations();
    setOrganizations(rows);
  };

  useEffect(() => {
    void loadOrganizations();
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    await api.createOrganization(newName.trim());
    setNewName("");
    await loadOrganizations();
    toast({ title: "Organization created", description: "New company tenant added." });
  };

  const handleToggleStatus = async (org: Organization) => {
    const next = org.status === "active" ? "suspended" : "active";
    await api.updateOrganizationStatus(org.id, next);
    await loadOrganizations();
  };

  const handleToggleAuth = async (org: Organization) => {
    const next = org.authMode === "local" ? "ldap" : "local";
    await api.updateOrganizationAuthMode(org.id, next);
    await loadOrganizations();
  };

  const updateLdapField = (orgId: string, key: string, value: string | boolean | number) => {
    setLdapForms((prev) => ({
      ...prev,
      [orgId]: {
        ldapServer: "",
        ldapPort: 389,
        ldapBaseDn: "",
        ldapBindDn: "",
        ldapBindPassword: "",
        ldapUserFilter: "(objectClass=person)",
        ldapUseSsl: false,
        ...prev[orgId],
        [key]: value,
      },
    }));
  };

  const saveLdap = async (orgId: string) => {
    const form = ldapForms[orgId];
    if (!form) return;
    await api.updateOrganizationLdap(orgId, form);
    toast({ title: "LDAP settings saved", description: `Organization ${orgId} LDAP config updated.` });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Organizations</h1>
        <p className="text-sm text-muted-foreground mt-1">Super Admin control for tenants, auth mode, and suspension.</p>
      </div>

      <div className="stat-card rounded-xl p-4 flex gap-2 max-w-xl">
        <Input
          placeholder="New organization name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="bg-muted border-border"
        />
        <CyberButton onClick={handleCreate}>Create</CyberButton>
      </div>

      <div className="space-y-4">
        {organizations.map((org) => {
          const ldap = ldapForms[org.id] ?? {
            ldapServer: org.ldapServer ?? "",
            ldapPort: org.ldapPort ?? 389,
            ldapBaseDn: org.ldapBaseDn ?? "",
            ldapBindDn: org.ldapBindDn ?? "",
            ldapBindPassword: "",
            ldapUserFilter: org.ldapUserFilter ?? "(objectClass=person)",
            ldapUseSsl: org.ldapUseSsl ?? false,
          };
          return (
            <div key={org.id} className="stat-card rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-base font-semibold text-foreground">{org.name}</p>
                  <p className="text-xs text-muted-foreground">Org ID: {org.id}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className={org.status === "active" ? "bg-success/20 text-success border-success/30" : "bg-destructive/20 text-destructive border-destructive/30"}>
                    {org.status}
                  </Badge>
                  <Badge variant="outline">{org.authMode.toUpperCase()}</Badge>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between rounded-lg border border-border p-3">
                  <span className="text-sm text-foreground">Active Organization</span>
                  <Switch checked={org.status === "active"} onCheckedChange={() => void handleToggleStatus(org)} />
                </div>
                <div className="flex items-center justify-between rounded-lg border border-border p-3">
                  <span className="text-sm text-foreground">Use LDAP Auth</span>
                  <Switch checked={org.authMode === "ldap"} onCheckedChange={() => void handleToggleAuth(org)} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Input placeholder="LDAP server" value={ldap.ldapServer} onChange={(e) => updateLdapField(org.id, "ldapServer", e.target.value)} className="bg-muted border-border" />
                <Input placeholder="LDAP port" type="number" value={ldap.ldapPort} onChange={(e) => updateLdapField(org.id, "ldapPort", Number(e.target.value || 389))} className="bg-muted border-border" />
                <Input placeholder="Base DN" value={ldap.ldapBaseDn} onChange={(e) => updateLdapField(org.id, "ldapBaseDn", e.target.value)} className="bg-muted border-border" />
                <Input placeholder="Bind DN" value={ldap.ldapBindDn} onChange={(e) => updateLdapField(org.id, "ldapBindDn", e.target.value)} className="bg-muted border-border" />
                <Input placeholder="Bind Password" type="password" value={ldap.ldapBindPassword} onChange={(e) => updateLdapField(org.id, "ldapBindPassword", e.target.value)} className="bg-muted border-border" />
                <Input placeholder="User filter" value={ldap.ldapUserFilter} onChange={(e) => updateLdapField(org.id, "ldapUserFilter", e.target.value)} className="bg-muted border-border" />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Switch checked={ldap.ldapUseSsl} onCheckedChange={(v) => updateLdapField(org.id, "ldapUseSsl", v)} />
                  <span className="text-sm text-foreground">LDAP SSL</span>
                </div>
                <CyberButton variant="outline" onClick={() => void saveLdap(org.id)}>Save LDAP</CyberButton>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OrganizationsPage;

