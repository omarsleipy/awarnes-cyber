import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CyberButton } from "@/components/CyberButton";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ClipboardCheck, Clock, ShieldAlert, Lock, FileCheck, AlertTriangle, Plus, Trash2, Key, CheckCircle2, Users } from "lucide-react";
import { api, mockUsers } from "@/services/api";
import { usePortal } from "@/contexts/PortalContext";
import { useToast } from "@/hooks/use-toast";

interface Question {
  question: string;
  options: string[];
  correct: number;
}

const exams = [
  { id: 1, title: "Phishing Identification Exam", description: "Identify phishing emails, URLs, and social engineering attempts.", questions: 30, duration: "45 min", attempts: "2/3", status: "available" as const, difficulty: "Intermediate", proctored: true, examId: "e1" },
  { id: 2, title: "Email Security Assessment", description: "Test your knowledge on secure email protocols and encryption.", questions: 25, duration: "30 min", attempts: "0/3", status: "locked" as const, difficulty: "Beginner", proctored: true, examId: "e2" },
  { id: 3, title: "Data Privacy Certification", description: "Comprehensive exam covering GDPR, data classification, and privacy.", questions: 50, duration: "60 min", attempts: "1/3", status: "passed" as const, score: 92, difficulty: "Advanced", proctored: true, examId: "e3" },
  { id: 4, title: "Incident Response Protocol", description: "Assess your ability to follow incident response procedures.", questions: 20, duration: "25 min", attempts: "3/3", status: "failed" as const, score: 54, difficulty: "Intermediate", proctored: true, examId: "e4" },
];

const Assessments = () => {
  const { role } = usePortal();
  const { toast } = useToast();
  const navigate = useNavigate();

  // Password dialog state
  const [passwordDialog, setPasswordDialog] = useState(false);
  const [selectedExam, setSelectedExam] = useState<typeof exams[0] | null>(null);
  const [examPassword, setExamPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [loading, setLoading] = useState(false);

  // Exam creation state (admin)
  const [creationStep, setCreationStep] = useState(0);
  const [newTitle, setNewTitle] = useState("");
  const [newDuration, setNewDuration] = useState("30");
  const [newQuestions, setNewQuestions] = useState<Question[]>([{ question: "", options: ["", "", "", ""], correct: 0 }]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [generatedPasswords, setGeneratedPasswords] = useState<{ userId: string; password: string }[]>([]);

  // --- Trainee: Enter exam password ---
  const handleEnterExam = (exam: typeof exams[0]) => {
    setSelectedExam(exam);
    setExamPassword("");
    setPasswordError("");
    setPasswordDialog(true);
  };

  const handlePasswordSubmit = async () => {
    if (!selectedExam) return;
    setLoading(true);
    const res = await api.validateExamPassword(selectedExam.examId, examPassword);
    setLoading(false);
    if (res.valid) {
      setPasswordDialog(false);
      navigate(`/exam/${selectedExam.examId}`);
    } else {
      setPasswordError(res.error || "Invalid password");
    }
  };

  // --- Admin: Exam creation helpers ---
  const addQuestion = () => setNewQuestions((p) => [...p, { question: "", options: ["", "", "", ""], correct: 0 }]);
  const removeQuestion = (i: number) => setNewQuestions((p) => p.filter((_, idx) => idx !== i));
  const updateQuestion = (i: number, field: string, value: any) => {
    setNewQuestions((prev) => prev.map((q, idx) => idx === i ? { ...q, [field]: value } : q));
  };
  const updateOption = (qi: number, oi: number, value: string) => {
    setNewQuestions((prev) => prev.map((q, idx) => idx === qi ? { ...q, options: q.options.map((o, j) => j === oi ? value : o) } : q));
  };
  const toggleUser = (uid: string) => {
    setSelectedUsers((prev) => prev.includes(uid) ? prev.filter((u) => u !== uid) : [...prev, uid]);
  };
  const handleCreateExam = async () => {
    const res = await api.createExam({ title: newTitle, questions: newQuestions, allowedUsers: selectedUsers });
    setGeneratedPasswords(res.passwords);
    setCreationStep(3);
    toast({ title: "Exam Created", description: `${res.passwords.length} unique passwords generated.` });
  };
  const resetCreation = () => {
    setCreationStep(0);
    setNewTitle("");
    setNewDuration("30");
    setNewQuestions([{ question: "", options: ["", "", "", ""], correct: 0 }]);
    setSelectedUsers([]);
    setGeneratedPasswords([]);
  };

  const creationSteps = ["Details", "Questions", "Users", "Passwords"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Security Assessments</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {role === "admin" ? "Manage exams and generate access passwords" : "Proctored exams with anti-cheating enforcement"}
          </p>
        </div>
      </div>

      {role === "admin" ? (
        <Tabs defaultValue="exams" className="space-y-6">
          <TabsList className="bg-muted">
            <TabsTrigger value="exams">All Exams</TabsTrigger>
            <TabsTrigger value="create">Create Exam</TabsTrigger>
          </TabsList>

          {/* All Exams Tab */}
          <TabsContent value="exams" className="space-y-4">
            {renderExamList(false)}
          </TabsContent>

          {/* Create Exam Tab */}
          <TabsContent value="create" className="space-y-6">
            {/* Stepper */}
            <div className="flex items-center gap-2 flex-wrap">
              {creationSteps.map((s, i) => (
                <div key={s} className="flex items-center gap-2">
                  <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${i <= creationStep ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
                    {i < creationStep ? <CheckCircle2 className="h-4 w-4" /> : i + 1}
                  </div>
                  <span className={`text-xs font-medium ${i <= creationStep ? "text-foreground" : "text-muted-foreground"}`}>{s}</span>
                  {i < creationSteps.length - 1 && <div className={`h-px w-8 ${i < creationStep ? "bg-primary" : "bg-border"}`} />}
                </div>
              ))}
            </div>

            {creationStep === 0 && (
              <div className="stat-card rounded-xl p-6 space-y-4 max-w-xl animate-fade-in">
                <Input placeholder="Exam Title" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} className="bg-muted border-border" />
                <Input placeholder="Duration (minutes)" type="number" value={newDuration} onChange={(e) => setNewDuration(e.target.value)} className="bg-muted border-border" />
                <CyberButton onClick={() => setCreationStep(1)} disabled={!newTitle}>Next: Add Questions</CyberButton>
              </div>
            )}

            {creationStep === 1 && (
              <div className="space-y-4 animate-fade-in">
                {newQuestions.map((q, qi) => (
                  <div key={qi} className="stat-card rounded-xl p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-muted-foreground">Question {qi + 1}</span>
                      {newQuestions.length > 1 && (
                        <button onClick={() => removeQuestion(qi)} className="text-destructive hover:text-destructive/80"><Trash2 className="h-4 w-4" /></button>
                      )}
                    </div>
                    <Input placeholder="Question text" value={q.question} onChange={(e) => updateQuestion(qi, "question", e.target.value)} className="bg-muted border-border" />
                    <div className="grid grid-cols-2 gap-2">
                      {q.options.map((opt, oi) => (
                        <div key={oi} className="flex items-center gap-2">
                          <button onClick={() => updateQuestion(qi, "correct", oi)} className={`h-5 w-5 rounded-full border-2 shrink-0 ${q.correct === oi ? "border-primary bg-primary" : "border-border"}`} />
                          <Input placeholder={`Option ${String.fromCharCode(65 + oi)}`} value={opt} onChange={(e) => updateOption(qi, oi, e.target.value)} className="bg-muted border-border text-sm" />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                <div className="flex gap-2">
                  <CyberButton variant="outline" onClick={addQuestion}><Plus className="h-4 w-4" /> Add Question</CyberButton>
                  <CyberButton onClick={() => setCreationStep(2)} disabled={newQuestions.some((q) => !q.question || q.options.some((o) => !o))}>Next: Select Users</CyberButton>
                </div>
              </div>
            )}

            {creationStep === 2 && (
              <div className="space-y-4 animate-fade-in">
                <div className="stat-card rounded-xl overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                        <th className="px-5 py-3 text-left w-10"></th>
                        <th className="px-5 py-3 text-left">User</th>
                        <th className="px-5 py-3 text-left">Department</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mockUsers.filter((u) => u.role === "trainee").map((user) => (
                        <tr key={user.id} className="border-b border-border/50 hover:bg-muted/30 cursor-pointer" onClick={() => toggleUser(user.id)}>
                          <td className="px-5 py-3">
                            <div className={`h-5 w-5 rounded border-2 flex items-center justify-center ${selectedUsers.includes(user.id) ? "border-primary bg-primary" : "border-border"}`}>
                              {selectedUsers.includes(user.id) && <CheckCircle2 className="h-3 w-3 text-primary-foreground" />}
                            </div>
                          </td>
                          <td className="px-5 py-3">
                            <p className="text-sm font-medium text-foreground">{user.name}</p>
                            <p className="text-xs text-muted-foreground">{user.email}</p>
                          </td>
                          <td className="px-5 py-3 text-sm text-muted-foreground">{user.department}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex gap-2">
                  <CyberButton variant="outline" onClick={() => setCreationStep(1)}>Back</CyberButton>
                  <CyberButton onClick={handleCreateExam} disabled={selectedUsers.length === 0}>
                    <Key className="h-4 w-4" /> Create & Generate Passwords ({selectedUsers.length})
                  </CyberButton>
                </div>
              </div>
            )}

            {creationStep === 3 && (
              <div className="space-y-4 animate-fade-in">
                <div className="cyber-border rounded-xl p-4 bg-primary/5 flex items-start gap-3">
                  <Key className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-foreground">Unique Passwords Generated</p>
                    <p className="text-xs text-muted-foreground mt-1">Each user has a unique password. Send via SMTP.</p>
                  </div>
                </div>
                <div className="stat-card rounded-xl overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                        <th className="px-5 py-3 text-left">User</th>
                        <th className="px-5 py-3 text-left">Exam Password</th>
                      </tr>
                    </thead>
                    <tbody>
                      {generatedPasswords.map((pw) => {
                        const user = mockUsers.find((u) => u.id === pw.userId);
                        return (
                          <tr key={pw.userId} className="border-b border-border/50">
                            <td className="px-5 py-3">
                              <p className="text-sm font-medium text-foreground">{user?.name}</p>
                              <p className="text-xs text-muted-foreground">{user?.email}</p>
                            </td>
                            <td className="px-5 py-3">
                              <code className="rounded bg-muted px-2 py-1 text-sm font-mono text-primary">{pw.password}</code>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="flex gap-2">
                  <CyberButton variant="outline" onClick={resetCreation}>Create Another</CyberButton>
                  <CyberButton onClick={() => toast({ title: "Passwords Sent", description: "Exam passwords sent via SMTP." })}>Send via SMTP</CyberButton>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      ) : (
        <>
          {/* Anti-cheat notice */}
          <div className="cyber-border rounded-xl p-4 flex items-start gap-3 bg-primary/5">
            <ShieldAlert className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-foreground">Proctored Environment</p>
              <p className="text-xs text-muted-foreground mt-1">
                All exams are monitored. Text copying is disabled. After 3 tab-switch warnings, the exam will be terminated.
              </p>
            </div>
          </div>
          {renderExamList(true)}
        </>
      )}

      {/* Password Dialog */}
      <Dialog open={passwordDialog} onOpenChange={setPasswordDialog}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground">Enter Exam Password</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Enter the unique password provided by your administrator to access "{selectedExam?.title}".
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <Input
              type="password"
              placeholder="Exam password..."
              value={examPassword}
              onChange={(e) => { setExamPassword(e.target.value); setPasswordError(""); }}
              className="bg-muted border-border"
            />
            {passwordError && <p className="text-xs text-destructive">{passwordError}</p>}
          </div>
          <DialogFooter>
            <CyberButton variant="outline" onClick={() => setPasswordDialog(false)}>Cancel</CyberButton>
            <CyberButton onClick={handlePasswordSubmit} disabled={!examPassword || loading}>
              {loading ? "Verifying..." : "Start Exam"}
            </CyberButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );

  function renderExamList(isTrainee: boolean) {
    return (
      <div className="space-y-4">
        {exams.map((exam, idx) => (
          <div key={exam.id} className="stat-card rounded-xl p-5 flex flex-col md:flex-row md:items-center gap-4 animate-fade-in" style={{ animationDelay: `${idx * 80}ms` }}>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-base font-semibold text-foreground">{exam.title}</h3>
                {exam.status === "passed" && <Badge variant="outline" className="bg-success/20 text-success border-success/30">Passed ({exam.score}%)</Badge>}
                {exam.status === "failed" && <Badge variant="outline" className="bg-destructive/20 text-destructive border-destructive/30">Failed ({exam.score}%)</Badge>}
                {exam.status === "locked" && <Badge variant="outline" className="bg-muted text-muted-foreground border-border"><Lock className="h-3 w-3 mr-1" /> Requires Password</Badge>}
              </div>
              <p className="text-xs text-muted-foreground">{exam.description}</p>
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><ClipboardCheck className="h-3.5 w-3.5" /> {exam.questions} questions</span>
                <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> {exam.duration}</span>
                <span>Attempts: {exam.attempts}</span>
                <span className="text-primary font-medium">{exam.difficulty}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {exam.status === "passed" && (
                <CyberButton variant="secondary" size="sm" onClick={() => navigate("/certificates")}>
                  <FileCheck className="h-3.5 w-3.5" /> Certificate
                </CyberButton>
              )}
              {exam.status === "failed" && (
                <CyberButton variant="outline" size="sm" disabled>
                  <AlertTriangle className="h-3.5 w-3.5" /> No attempts left
                </CyberButton>
              )}
              {exam.status === "available" && (
                <CyberButton size="sm" onClick={() => handleEnterExam(exam)}>
                  <Key className="h-3.5 w-3.5" /> Enter Exam Password
                </CyberButton>
              )}
              {exam.status === "locked" && (
                <CyberButton variant="ghost" size="sm" disabled>
                  <Lock className="h-3.5 w-3.5" /> Complete prerequisite
                </CyberButton>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }
};

export default Assessments;
