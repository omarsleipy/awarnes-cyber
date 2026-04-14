import { useState } from "react";
import { CyberButton } from "@/components/CyberButton";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { ClipboardCheck, Plus, Trash2, Key, Users, CheckCircle2 } from "lucide-react";
import { api, mockUsers } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

interface Question {
  question: string;
  options: string[];
  correct: number;
}

const ExamCreation = () => {
  const { toast } = useToast();
  const [step, setStep] = useState(0); // 0=details, 1=questions, 2=users, 3=passwords
  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState("30");
  const [questions, setQuestions] = useState<Question[]>([{ question: "", options: ["", "", "", ""], correct: 0 }]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [generatedPasswords, setGeneratedPasswords] = useState<{ userId: string; password: string }[]>([]);

  const addQuestion = () => setQuestions((p) => [...p, { question: "", options: ["", "", "", ""], correct: 0 }]);
  const removeQuestion = (i: number) => setQuestions((p) => p.filter((_, idx) => idx !== i));

  const updateQuestion = (i: number, field: string, value: any) => {
    setQuestions((prev) => prev.map((q, idx) => idx === i ? { ...q, [field]: value } : q));
  };

  const updateOption = (qi: number, oi: number, value: string) => {
    setQuestions((prev) => prev.map((q, idx) => idx === qi ? { ...q, options: q.options.map((o, j) => j === oi ? value : o) } : q));
  };

  const toggleUser = (uid: string) => {
    setSelectedUsers((prev) => prev.includes(uid) ? prev.filter((u) => u !== uid) : [...prev, uid]);
  };

  const handleCreate = async () => {
    const res = await api.createExam({ title, questions, allowedUsers: selectedUsers });
    setGeneratedPasswords(res.passwords);
    setStep(3);
    toast({ title: "Exam Created", description: `${res.passwords.length} unique passwords generated.` });
  };

  const steps = ["Exam Details", "Questions", "Allowed Users", "Passwords"];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Create Assessment</h1>
        <p className="text-sm text-muted-foreground mt-1">Build exams and generate unique access passwords</p>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-2">
        {steps.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${i <= step ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
              {i < step ? <CheckCircle2 className="h-4 w-4" /> : i + 1}
            </div>
            <span className={`text-xs font-medium ${i <= step ? "text-foreground" : "text-muted-foreground"}`}>{s}</span>
            {i < steps.length - 1 && <div className={`h-px w-8 ${i < step ? "bg-primary" : "bg-border"}`} />}
          </div>
        ))}
      </div>

      {/* Step 0: Details */}
      {step === 0 && (
        <div className="stat-card rounded-xl p-6 space-y-4 max-w-xl animate-fade-in">
          <Input placeholder="Exam Title" value={title} onChange={(e) => setTitle(e.target.value)} className="bg-muted border-border" />
          <Input placeholder="Duration (minutes)" type="number" value={duration} onChange={(e) => setDuration(e.target.value)} className="bg-muted border-border" />
          <CyberButton onClick={() => setStep(1)} disabled={!title}>Next: Add Questions</CyberButton>
        </div>
      )}

      {/* Step 1: Questions */}
      {step === 1 && (
        <div className="space-y-4 animate-fade-in">
          {questions.map((q, qi) => (
            <div key={qi} className="stat-card rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">Question {qi + 1}</span>
                {questions.length > 1 && (
                  <button onClick={() => removeQuestion(qi)} className="text-destructive hover:text-destructive/80"><Trash2 className="h-4 w-4" /></button>
                )}
              </div>
              <Input placeholder="Question text" value={q.question} onChange={(e) => updateQuestion(qi, "question", e.target.value)} className="bg-muted border-border" />
              <div className="grid grid-cols-2 gap-2">
                {q.options.map((opt, oi) => (
                  <div key={oi} className="flex items-center gap-2">
                    <button
                      onClick={() => updateQuestion(qi, "correct", oi)}
                      className={`h-5 w-5 rounded-full border-2 shrink-0 ${q.correct === oi ? "border-primary bg-primary" : "border-border"}`}
                    />
                    <Input placeholder={`Option ${String.fromCharCode(65 + oi)}`} value={opt} onChange={(e) => updateOption(qi, oi, e.target.value)} className="bg-muted border-border text-sm" />
                  </div>
                ))}
              </div>
            </div>
          ))}
          <div className="flex gap-2">
            <CyberButton variant="outline" onClick={addQuestion}><Plus className="h-4 w-4" /> Add Question</CyberButton>
            <CyberButton onClick={() => setStep(2)} disabled={questions.some((q) => !q.question || q.options.some((o) => !o))}>
              Next: Select Users
            </CyberButton>
          </div>
        </div>
      )}

      {/* Step 2: User Selection */}
      {step === 2 && (
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
            <CyberButton variant="outline" onClick={() => setStep(1)}>Back</CyberButton>
            <CyberButton onClick={handleCreate} disabled={selectedUsers.length === 0}>
              <Key className="h-4 w-4" /> Create Exam & Generate Passwords ({selectedUsers.length})
            </CyberButton>
          </div>
        </div>
      )}

      {/* Step 3: Generated Passwords */}
      {step === 3 && (
        <div className="space-y-4 animate-fade-in">
          <div className="cyber-border rounded-xl p-4 bg-primary/5 flex items-start gap-3">
            <Key className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-foreground">Unique Passwords Generated</p>
              <p className="text-xs text-muted-foreground mt-1">Each user has a unique password. These can be sent via SMTP.</p>
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
            <CyberButton variant="outline" onClick={() => { setStep(0); setTitle(""); setQuestions([{ question: "", options: ["", "", "", ""], correct: 0 }]); setSelectedUsers([]); setGeneratedPasswords([]); }}>
              Create Another
            </CyberButton>
            <CyberButton>Send Passwords via SMTP</CyberButton>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExamCreation;
