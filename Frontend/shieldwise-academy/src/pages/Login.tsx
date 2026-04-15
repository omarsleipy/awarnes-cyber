import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CyberButton } from "@/components/CyberButton";
import { Input } from "@/components/ui/input";
import { ShieldAlert, LogIn, Eye, EyeOff } from "lucide-react";
import { usePortal } from "@/contexts/PortalContext";
import { api } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const Login = () => {
  const navigate = useNavigate();
  const { setRole, setIsAuthenticated } = usePortal();
  const { toast } = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [organizationId, setOrganizationId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const res = await api.login(email, password, organizationId || undefined);
    setLoading(false);

    if (res.success && res.user) {
      setRole(res.user.role as "super_admin" | "admin" | "trainee");
      setIsAuthenticated(true);
      toast({ title: "Welcome back!", description: `Logged in as ${res.user.name}` });
      navigate("/");
    } else {
      setError("Invalid email or password. Try admin@corp.com or john@corp.com");
    }
  };

  const quickLogin = async (type: "admin" | "trainee") => {
    const loginEmail = type === "admin" ? "admin@corp.com" : "john@corp.com";
    setEmail(loginEmail);
    setPassword("password");
    setLoading(true);
    const quickOrg = type === "admin" ? "1" : "";
    const res = await api.login(loginEmail, "password", quickOrg || undefined);
    setLoading(false);
    if (res.success && res.user) {
      setRole(res.user.role as "super_admin" | "admin" | "trainee");
      setIsAuthenticated(true);
      toast({ title: "Welcome back!", description: `Logged in as ${res.user.name}` });
      navigate("/");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-8 animate-fade-in">
        {/* Logo */}
        <div className="text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl cyber-gradient mb-4">
            <ShieldAlert className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold text-foreground tracking-tight">CyberAware</h1>
          <p className="text-sm text-muted-foreground mt-1">Enterprise Cybersecurity Awareness Platform</p>
        </div>

        {/* Login Form */}
        <div className="stat-card rounded-xl p-8 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Sign In</h2>
            <p className="text-xs text-muted-foreground mt-1">Enter your corporate credentials</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Email</label>
              <Input
                type="email"
                placeholder="you@corp.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(""); }}
                className="bg-muted border-border"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Organization ID (optional)</label>
              <Input
                placeholder="1"
                value={organizationId}
                onChange={(e) => { setOrganizationId(e.target.value); setError(""); }}
                className="bg-muted border-border"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Password</label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(""); }}
                  className="bg-muted border-border pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</p>
            )}

            <CyberButton type="submit" className="w-full" disabled={loading || !email || !password}>
              <LogIn className="h-4 w-4" />
              {loading ? "Signing in..." : "Sign In"}
            </CyberButton>
          </form>

          {/* Quick Login */}
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground">Quick Access</span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <CyberButton variant="outline" size="sm" onClick={() => quickLogin("admin")} className="w-full">
                Admin Login
              </CyberButton>
              <CyberButton variant="outline" size="sm" onClick={() => quickLogin("trainee")} className="w-full">
                Trainee Login
              </CyberButton>
            </div>
          </div>
        </div>

        <p className="text-center text-[11px] text-muted-foreground">
          No public registration. Contact your IT administrator for access.
        </p>
      </div>
    </div>
  );
};

export default Login;
