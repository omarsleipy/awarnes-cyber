import { CyberButton } from "@/components/CyberButton";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Clock, PlayCircle, CheckCircle2, Lock, Users } from "lucide-react";

const courses = [
  {
    id: 1,
    title: "Phishing Awareness Fundamentals",
    description: "Learn to identify and report phishing attempts across email, SMS, and social engineering.",
    duration: "45 min",
    enrolled: 892,
    progress: 100,
    status: "completed" as const,
    modules: 8,
    category: "Phishing",
  },
  {
    id: 2,
    title: "Email Security Best Practices",
    description: "Secure email communication, attachment handling, and recognizing spoofed senders.",
    duration: "30 min",
    enrolled: 756,
    progress: 65,
    status: "in-progress" as const,
    modules: 6,
    category: "Email Security",
  },
  {
    id: 3,
    title: "Data Privacy & GDPR Compliance",
    description: "Understanding data classification, handling PII, and regulatory compliance requirements.",
    duration: "60 min",
    enrolled: 1024,
    progress: 0,
    status: "mandatory" as const,
    modules: 12,
    category: "Data Privacy",
  },
  {
    id: 4,
    title: "Password Hygiene & MFA",
    description: "Creating strong passwords, managing credentials, and multi-factor authentication setup.",
    duration: "20 min",
    enrolled: 645,
    progress: 30,
    status: "in-progress" as const,
    modules: 4,
    category: "Access Control",
  },
  {
    id: 5,
    title: "Incident Response Protocol",
    description: "Steps to follow when a security incident is detected. Report chains and containment procedures.",
    duration: "40 min",
    enrolled: 412,
    progress: 0,
    status: "locked" as const,
    modules: 7,
    category: "Incident Response",
  },
  {
    id: 6,
    title: "Social Engineering Defense",
    description: "Recognize manipulation tactics including pretexting, baiting, and tailgating attacks.",
    duration: "35 min",
    enrolled: 533,
    progress: 0,
    status: "available" as const,
    modules: 5,
    category: "Social Engineering",
  },
];

const statusConfig = {
  completed: { label: "Completed", className: "bg-success/20 text-success border-success/30" },
  "in-progress": { label: "In Progress", className: "bg-primary/20 text-primary border-primary/30" },
  mandatory: { label: "Mandatory", className: "bg-destructive/20 text-destructive border-destructive/30" },
  locked: { label: "Locked", className: "bg-muted text-muted-foreground border-border" },
  available: { label: "Available", className: "bg-secondary text-secondary-foreground border-border" },
};

const Training = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Training Courses</h1>
          <p className="text-sm text-muted-foreground mt-1">Mandatory and optional cybersecurity modules</p>
        </div>
        <CyberButton>Upload Course</CyberButton>
      </div>

      {/* Course Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {courses.map((course, idx) => {
          const status = statusConfig[course.status];
          return (
            <div
              key={course.id}
              className="stat-card rounded-xl p-5 flex flex-col gap-4 animate-fade-in"
              style={{ animationDelay: `${idx * 80}ms` }}
            >
              <div className="flex items-start justify-between">
                <Badge variant="outline" className={status.className}>
                  {status.label}
                </Badge>
                <span className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground">
                  {course.category}
                </span>
              </div>

              <div className="flex-1">
                <h3 className="text-base font-semibold text-foreground mb-1.5">{course.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{course.description}</p>
              </div>

              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" /> {course.duration}
                </span>
                <span className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" /> {course.enrolled}
                </span>
                <span>{course.modules} modules</span>
              </div>

              {course.progress > 0 && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-semibold text-foreground">{course.progress}%</span>
                  </div>
                  <Progress value={course.progress} className="h-1.5 bg-muted" />
                </div>
              )}

              <CyberButton
                variant={course.status === "locked" ? "ghost" : course.status === "completed" ? "secondary" : "default"}
                size="sm"
                className="w-full"
                disabled={course.status === "locked"}
              >
                {course.status === "completed" && <><CheckCircle2 className="h-3.5 w-3.5" /> Review</>}
                {course.status === "in-progress" && <><PlayCircle className="h-3.5 w-3.5" /> Continue</>}
                {course.status === "mandatory" && <><PlayCircle className="h-3.5 w-3.5" /> Start Now</>}
                {course.status === "locked" && <><Lock className="h-3.5 w-3.5" /> Prerequisites Required</>}
                {course.status === "available" && <><PlayCircle className="h-3.5 w-3.5" /> Enroll</>}
              </CyberButton>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Training;
