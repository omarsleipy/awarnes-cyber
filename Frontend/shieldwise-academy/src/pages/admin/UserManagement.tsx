import { useState, useEffect } from "react";
import { CyberButton } from "@/components/CyberButton";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Users, UserPlus, Upload, Search, MoreHorizontal } from "lucide-react";
import { api, mockUsers } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const UserManagement = () => {
  const { toast } = useToast();
  const [users, setUsers] = useState(mockUsers);
  const [search, setSearch] = useState("");
  const [showAddUser, setShowAddUser] = useState(false);
  const [showCsvUpload, setShowCsvUpload] = useState(false);
  const [newUser, setNewUser] = useState({ name: "", email: "", role: "trainee", department: "" });

  const filtered = users.filter((u) =>
    u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase())
  );

  const handleAddUser = async () => {
    const user = await api.addUser(newUser);
    setUsers((prev) => [...prev, user]);
    setShowAddUser(false);
    setNewUser({ name: "", email: "", role: "trainee", department: "" });
    toast({ title: "User Added", description: `${newUser.name} has been provisioned.` });
  };

  const handleCsvUpload = async () => {
    const res = await api.bulkUploadUsers("mock-csv-data");
    setShowCsvUpload(false);
    toast({ title: "CSV Import Complete", description: `${res.imported} imported, ${res.skipped} skipped, ${res.errors} errors.` });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">User Management</h1>
          <p className="text-sm text-muted-foreground mt-1">Provision and manage platform users</p>
        </div>
        <div className="flex gap-2">
          <CyberButton variant="outline" onClick={() => setShowCsvUpload(true)}>
            <Upload className="h-4 w-4" /> CSV Import
          </CyberButton>
          <CyberButton onClick={() => setShowAddUser(true)}>
            <UserPlus className="h-4 w-4" /> Add User
          </CyberButton>
        </div>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3 rounded-lg bg-muted px-3 py-1.5 w-full max-w-md">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          placeholder="Search users..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
        />
      </div>

      {/* Users Table */}
      <div className="stat-card rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <th className="px-5 py-3 text-left">User</th>
              <th className="px-5 py-3 text-left">Role</th>
              <th className="px-5 py-3 text-left">Department</th>
              <th className="px-5 py-3 text-left">Status</th>
              <th className="px-5 py-3 text-left">Courses</th>
              <th className="px-5 py-3 text-left">Last Login</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((user) => (
              <tr key={user.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                      {user.name.split(" ").map((n) => n[0]).join("")}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{user.name}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3">
                  <Badge variant="outline" className={user.role === "admin" ? "bg-primary/20 text-primary border-primary/30" : "bg-muted text-muted-foreground border-border"}>
                    {user.role}
                  </Badge>
                </td>
                <td className="px-5 py-3 text-sm text-muted-foreground">{user.department}</td>
                <td className="px-5 py-3">
                  <Badge variant="outline" className={user.status === "active" ? "bg-success/20 text-success border-success/30" : "bg-destructive/20 text-destructive border-destructive/30"}>
                    {user.status}
                  </Badge>
                </td>
                <td className="px-5 py-3 text-sm text-foreground">{user.completedCourses}</td>
                <td className="px-5 py-3 text-sm text-muted-foreground">{user.lastLogin}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add User Dialog */}
      <Dialog open={showAddUser} onOpenChange={setShowAddUser}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground">Add New User</DialogTitle>
            <DialogDescription>Manually provision a user account</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input placeholder="Full Name" value={newUser.name} onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} className="bg-muted border-border" />
            <Input placeholder="Email" type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} className="bg-muted border-border" />
            <Input placeholder="Department" value={newUser.department} onChange={(e) => setNewUser({ ...newUser, department: e.target.value })} className="bg-muted border-border" />
            <Select value={newUser.role} onValueChange={(v) => setNewUser({ ...newUser, role: v })}>
              <SelectTrigger className="bg-muted border-border">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="trainee">Trainee</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <CyberButton variant="outline" onClick={() => setShowAddUser(false)}>Cancel</CyberButton>
            <CyberButton onClick={handleAddUser} disabled={!newUser.name || !newUser.email}>Add User</CyberButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* CSV Upload Dialog */}
      <Dialog open={showCsvUpload} onOpenChange={setShowCsvUpload}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground">CSV Bulk Import</DialogTitle>
            <DialogDescription>Upload a CSV file with user data (name, email, department, role)</DialogDescription>
          </DialogHeader>
          <div className="border-2 border-dashed border-border rounded-xl p-8 text-center">
            <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">Drag & drop CSV file or click to browse</p>
            <p className="text-xs text-muted-foreground mt-1">Expected columns: name, email, department, role</p>
            <CyberButton variant="outline" size="sm" className="mt-4">Select File</CyberButton>
          </div>
          <DialogFooter>
            <CyberButton variant="outline" onClick={() => setShowCsvUpload(false)}>Cancel</CyberButton>
            <CyberButton onClick={handleCsvUpload}>Import Users</CyberButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;
