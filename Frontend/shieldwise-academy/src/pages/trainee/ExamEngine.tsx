import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { CyberButton } from "@/components/CyberButton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ShieldAlert, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";
import { api, mockExamQuestions } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

type ExamPhase = "password" | "active" | "submitted" | "disqualified";

const ExamEngine = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [phase, setPhase] = useState<ExamPhase>("password");
  const [password, setPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [questions, setQuestions] = useState(mockExamQuestions);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [warnings, setWarnings] = useState(0);
  const [timeLeft, setTimeLeft] = useState(30 * 60); // 30 min
  const [result, setResult] = useState<{ score: number; passed: boolean; correctAnswers: number; totalQuestions: number } | null>(null);
  const warningsRef = useRef(0);

  // ─── Anti-Cheating: disable right-click, copy, paste, select ───
  useEffect(() => {
    if (phase !== "active") return;

    const prevent = (e: Event) => { e.preventDefault(); return false; };
    const preventKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "c" || e.key === "v" || e.key === "a" || e.key === "x")) {
        e.preventDefault();
        toast({ title: "Action Blocked", description: "Copy/Paste is disabled during the exam.", variant: "destructive" });
      }
    };

    document.addEventListener("contextmenu", prevent);
    document.addEventListener("copy", prevent);
    document.addEventListener("paste", prevent);
    document.addEventListener("selectstart", prevent);
    document.addEventListener("keydown", preventKey);

    return () => {
      document.removeEventListener("contextmenu", prevent);
      document.removeEventListener("copy", prevent);
      document.removeEventListener("paste", prevent);
      document.removeEventListener("selectstart", prevent);
      document.removeEventListener("keydown", preventKey);
    };
  }, [phase, toast]);

  // ─── Tab Switch Detection ───
  useEffect(() => {
    if (phase !== "active") return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        warningsRef.current += 1;
        setWarnings(warningsRef.current);

        if (warningsRef.current >= 3) {
          setPhase("disqualified");
          api.reportDisqualification(examId || "", "3 tab-switch violations");
        } else {
          toast({
            title: `⚠️ Warning ${warningsRef.current}/3`,
            description: "Tab switching detected. 3 violations will disqualify you.",
            variant: "destructive",
          });
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [phase, examId, toast]);

  const handlePasswordSubmit = async () => {
    const res = await api.validateExamPassword(examId || "", password);
    if (res.valid) {
      setPhase("active");
      const q = await api.getExamQuestions(examId || "");
      setQuestions(q);
    } else {
      setPasswordError(res.error || "Invalid password");
    }
  };

  const handleAnswer = (questionId: string, optionIndex: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
  };

  const handleSubmit = useCallback(async () => {
    const res = await api.submitExam(examId || "", answers);
    setResult(res);
    setPhase("submitted");
  }, [examId, answers]);

  // ─── Timer ───
  useEffect(() => {
    if (phase !== "active") return;
    const id = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 0) return 0;
        if (prev === 1) {
          void handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [phase, handleSubmit]);

  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  // ─── Disqualified ───
  if (phase === "disqualified") {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="stat-card rounded-xl p-10 text-center max-w-md animate-fade-in">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-destructive/20">
            <AlertTriangle className="h-10 w-10 text-destructive" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">Exam Disqualified</h1>
          <p className="text-sm text-muted-foreground mb-6">
            You have been disqualified due to 3 tab-switch violations. This attempt has been recorded.
          </p>
          <CyberButton onClick={() => navigate("/my-courses")}>Return to Courses</CyberButton>
        </div>
      </div>
    );
  }

  // ─── Result ───
  if (phase === "submitted" && result) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="stat-card rounded-xl p-10 text-center max-w-md animate-fade-in">
          <div className={`mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full ${result.passed ? "bg-success/20" : "bg-destructive/20"}`}>
            {result.passed ? <CheckCircle2 className="h-10 w-10 text-success" /> : <AlertTriangle className="h-10 w-10 text-destructive" />}
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">{result.passed ? "Exam Passed!" : "Exam Failed"}</h1>
          <p className="text-4xl font-bold text-primary mb-2">{result.score}%</p>
          <p className="text-sm text-muted-foreground mb-6">
            {result.correctAnswers}/{result.totalQuestions} correct answers. {result.passed ? "Your certificate has been generated." : "70% required to pass."}
          </p>
          <div className="flex gap-3 justify-center">
            <CyberButton onClick={() => navigate("/my-courses")}>Back to Courses</CyberButton>
            {result.passed && <CyberButton variant="secondary" onClick={() => navigate("/certificates")}>View Certificate</CyberButton>}
          </div>
        </div>
      </div>
    );
  }

  // ─── Password Entry ───
  if (phase === "password") {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="stat-card rounded-xl p-8 max-w-md w-full animate-fade-in">
          <div className="text-center mb-6">
            <ShieldAlert className="h-10 w-10 text-primary mx-auto mb-3" />
            <h1 className="text-xl font-bold text-foreground">Secure Exam Access</h1>
            <p className="text-sm text-muted-foreground mt-1">Enter your unique exam password provided by the administrator</p>
          </div>
          <div className="space-y-4">
            <Input
              type="password"
              placeholder="Enter exam password..."
              value={password}
              onChange={(e) => { setPassword(e.target.value); setPasswordError(""); }}
              className="bg-muted border-border text-foreground"
            />
            {passwordError && <p className="text-xs text-destructive">{passwordError}</p>}
            <CyberButton className="w-full" onClick={handlePasswordSubmit} disabled={!password}>
              Enter Exam
            </CyberButton>
          </div>
          <div className="mt-4 cyber-border rounded-lg p-3 bg-primary/5">
            <p className="text-xs text-muted-foreground"><strong className="text-foreground">⚠ Proctored Exam:</strong> Copy/paste disabled. 3 tab switches = disqualification.</p>
          </div>
        </div>
      </div>
    );
  }

  // ─── Active Exam ───
  const q = questions[currentQ];

  return (
    <div className="max-w-3xl mx-auto space-y-6 select-none" style={{ userSelect: "none", WebkitUserSelect: "none" }}>
      {/* Header */}
      <div className="stat-card rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-primary" />
          <span className="text-sm font-semibold text-foreground">Proctored Exam</span>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className={warnings > 0 ? "bg-destructive/20 text-destructive border-destructive/30" : "bg-muted text-muted-foreground border-border"}>
            Warnings: {warnings}/3
          </Badge>
          <div className="flex items-center gap-1.5 text-sm font-mono">
            <Clock className="h-4 w-4 text-primary" />
            <span className={timeLeft < 300 ? "text-destructive font-bold" : "text-foreground"}>{formatTime(timeLeft)}</span>
          </div>
        </div>
      </div>

      {/* Progress */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Question {currentQ + 1} of {questions.length}</span>
          <span>{Object.keys(answers).length} answered</span>
        </div>
        <Progress value={((currentQ + 1) / questions.length) * 100} className="h-1.5 bg-muted" />
      </div>

      {/* Question */}
      <div className="stat-card rounded-xl p-6 space-y-5">
        <h2 className="text-lg font-semibold text-foreground">{q.question}</h2>
        <div className="space-y-3">
          {q.options.map((opt, idx) => (
            <button
              key={idx}
              onClick={() => handleAnswer(q.id, idx)}
              className={`w-full text-left rounded-lg px-4 py-3 text-sm transition-all border ${
                answers[q.id] === idx
                  ? "border-primary bg-primary/10 text-foreground cyber-glow"
                  : "border-border bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="font-mono text-xs text-muted-foreground mr-2">{String.fromCharCode(65 + idx)}.</span>
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <CyberButton variant="outline" disabled={currentQ === 0} onClick={() => setCurrentQ((p) => p - 1)}>Previous</CyberButton>
        {currentQ < questions.length - 1 ? (
          <CyberButton onClick={() => setCurrentQ((p) => p + 1)}>Next</CyberButton>
        ) : (
          <CyberButton onClick={handleSubmit} disabled={Object.keys(answers).length < questions.length}>
            Submit Exam ({Object.keys(answers).length}/{questions.length})
          </CyberButton>
        )}
      </div>
    </div>
  );
};

export default ExamEngine;
