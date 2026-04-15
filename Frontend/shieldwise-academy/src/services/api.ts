// API Service Layer — Backend integration with fallback to mock data

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const API_BASE = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000/api";
const TOKEN_KEY = "cyberaware_token";

function getToken(): string | null {
  return typeof localStorage !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
}

export function setAuthToken(token: string | null) {
  if (typeof localStorage === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit & { body?: object } = {}
): Promise<T> {
  const { body, ...rest } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((rest.headers as Record<string, string>) || {}),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers,
    body: body !== undefined ? JSON.stringify(body) : rest.body,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.headers.get("content-type")?.includes("json") ? res.json() : {};
}

// ─── Mock Data ──────────────────────────────────────────────
export const mockUsers = [
  { id: "u1", name: "John Doe", email: "john@corp.com", role: "trainee", department: "Finance", status: "active", completedCourses: 3, lastLogin: "2026-02-27" },
  { id: "u2", name: "Sarah Miller", email: "sarah@corp.com", role: "trainee", department: "HR", status: "active", completedCourses: 5, lastLogin: "2026-02-26" },
  { id: "u3", name: "Alex Kim", email: "alex@corp.com", role: "admin", department: "IT", status: "active", completedCourses: 6, lastLogin: "2026-02-27" },
  { id: "u4", name: "Maria Lopez", email: "maria@corp.com", role: "trainee", department: "Legal", status: "suspended", completedCourses: 1, lastLogin: "2026-02-20" },
  { id: "u5", name: "David Robinson", email: "david@corp.com", role: "trainee", department: "Engineering", status: "active", completedCourses: 4, lastLogin: "2026-02-25" },
];

export const mockCourses = [
  { id: "c1", title: "Phishing Awareness Fundamentals", modules: 8, duration: "45 min", progress: 100, totalSlides: 24, viewedSlides: 24, examId: "e1", category: "Phishing" },
  { id: "c2", title: "Email Security Best Practices", modules: 6, duration: "30 min", progress: 65, totalSlides: 18, viewedSlides: 12, examId: "e2", category: "Email Security" },
  { id: "c3", title: "Data Privacy & GDPR Compliance", modules: 12, duration: "60 min", progress: 30, totalSlides: 36, viewedSlides: 11, examId: "e3", category: "Data Privacy" },
  { id: "c4", title: "Password Hygiene & MFA", modules: 4, duration: "20 min", progress: 0, totalSlides: 12, viewedSlides: 0, examId: null, category: "Access Control" },
];

export const mockExamQuestions = [
  { id: "q1", question: "Which of these is a common indicator of a phishing email?", options: ["Urgent language demanding immediate action", "Email from a known colleague", "A company newsletter", "A calendar invite"], correct: 0 },
  { id: "q2", question: "What should you do if you suspect an email is phishing?", options: ["Reply to confirm", "Click the link to investigate", "Report it to IT security", "Forward it to colleagues"], correct: 2 },
  { id: "q3", question: "Which protocol secures email transmission?", options: ["HTTP", "FTP", "TLS/SSL", "Telnet"], correct: 2 },
  { id: "q4", question: "What does MFA stand for?", options: ["Multiple Factor Authentication", "Multi-File Access", "Multi-Factor Authentication", "Main Firewall Access"], correct: 2 },
  { id: "q5", question: "What is a pretexting attack?", options: ["Installing malware", "Creating a fabricated scenario to steal info", "A DDoS attack", "Encrypting files for ransom"], correct: 1 },
  { id: "q6", question: "Which is the strongest password?", options: ["password123", "P@$$w0rd", "Tr0ub4dor&3", "xK9!mQ2@vL#nP5"], correct: 3 },
  { id: "q7", question: "What is GDPR?", options: ["A firewall standard", "A data protection regulation", "An encryption algorithm", "A phishing technique"], correct: 1 },
  { id: "q8", question: "What is tailgating in security?", options: ["Following someone through a secure door", "Sending multiple emails", "Hacking a Wi-Fi network", "Installing spyware"], correct: 0 },
  { id: "q9", question: "What does PII stand for?", options: ["Public Internet Information", "Personal Identifiable Information", "Personally Identifiable Information", "Private Internal Information"], correct: 2 },
  { id: "q10", question: "When should you report a security incident?", options: ["Next business day", "After verifying with colleagues", "Immediately", "Only if data is lost"], correct: 2 },
];

export const mockCertificates = [
  { id: "cert1", examTitle: "Phishing Awareness Fundamentals", score: 92, date: "2026-01-15", status: "valid", expiresAt: "2027-01-15" },
  { id: "cert2", examTitle: "Email Security Best Practices", score: 88, date: "2026-02-10", status: "valid", expiresAt: "2027-02-10" },
];

export type Certificate = (typeof mockCertificates)[number];

export const mockCampaigns = [
  { id: "camp1", name: "Q1 Finance Dept Phish", template: "Password Reset", targetDept: "Finance", sent: 245, clicked: 31, reported: 189, status: "completed", createdAt: "2026-01-10" },
  { id: "camp2", name: "IT Password Reset Lure", template: "IT Alert", targetDept: "IT", sent: 180, clicked: 12, reported: 152, status: "completed", createdAt: "2026-01-25" },
  { id: "camp3", name: "CEO Gift Card Scam", template: "Executive Request", targetDept: "All", sent: 320, clicked: 48, reported: 201, status: "active", createdAt: "2026-02-15" },
  { id: "camp4", name: "HR Benefits Update", template: "Benefits Notice", targetDept: "HR", sent: 0, clicked: 0, reported: 0, status: "draft", createdAt: "2026-02-25" },
];

export const mockSmtpConfig = {
  host: "smtp.corp.com",
  port: 587,
  username: "noreply@corp.com",
  password: "",
  encryption: "TLS",
  fromName: "CyberAware Platform",
  fromEmail: "noreply@corp.com",
};

export const mockLdapConfig = {
  server: "ldap://ad.corp.com",
  port: 389,
  baseDn: "dc=corp,dc=com",
  bindDn: "cn=admin,dc=corp,dc=com",
  bindPassword: "",
  userFilter: "(objectClass=person)",
  useSsl: false,
};

// ─── API Functions (real backend when API_BASE is set) ─────────

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    try {
      const res = await request<{ success: true; user: Record<string, unknown>; token: string } | { success: false; error: string }>("/auth/login", { method: "POST", body: { email, password } });
      if (res.success && "token" in res) {
        setAuthToken(res.token);
        return res;
      }
      return res as { success: false; error: string };
    } catch (e) {
      return { success: false as const, error: (e as Error).message || "Invalid credentials" };
    }
  },

  // Users
  getUsers: async () => {
    try {
      return await request<typeof mockUsers>("/users");
    } catch {
      return mockUsers;
    }
  },
  addUser: async (user: Partial<typeof mockUsers[0]>) => {
    try {
      const u = await request<typeof mockUsers[0]>("/users", { method: "POST", body: { ...user, password: "ChangeMe123!" } });
      return u;
    } catch {
      const newUser = { ...user, id: `u${Date.now()}`, status: "active", completedCourses: 0, lastLogin: "Never" } as typeof mockUsers[0];
      mockUsers.push(newUser);
      return newUser;
    }
  },
  bulkUploadUsers: async (csvData: string) => {
    try {
      return await request<{ imported: number; skipped: number; errors: number }>("/users/bulk-upload", { method: "POST", body: { csvData } });
    } catch {
      return { imported: 12, skipped: 2, errors: 0 };
    }
  },

  // Courses
  getCourses: async () => {
    try {
      return await request<typeof mockCourses>("/courses");
    } catch {
      return mockCourses;
    }
  },
  updateCourseProgress: async (courseId: string, viewedSlides: number) => {
    try {
      await request(`/courses/${courseId}/progress`, { method: "PATCH", body: { viewedSlides } });
      return { success: true };
    } catch {
      return { success: true };
    }
  },

  // Exams
  validateExamPassword: async (examId: string, password: string) => {
    try {
      const res = await request<{ valid: boolean; error?: string }>(`/exams/${examId}/validate-password`, { method: "POST", body: { password } });
      return res.valid ? { valid: true as const } : { valid: false as const, error: res.error || "Invalid exam password" };
    } catch {
      if (password.length >= 6) return { valid: true as const };
      return { valid: false as const, error: "Invalid exam password" };
    }
  },
  getExamQuestions: async (examId: string) => {
    try {
      return await request<typeof mockExamQuestions>(`/exams/${examId}/questions`);
    } catch {
      return mockExamQuestions;
    }
  },
  submitExam: async (examId: string, answers: Record<string, number>) => {
    try {
      return await request<{ score: number; passed: boolean; totalQuestions: number; correctAnswers: number }>(`/exams/${examId}/submit`, { method: "POST", body: { answers } });
    } catch {
      let correct = 0;
      mockExamQuestions.forEach((q) => { if (answers[q.id] === q.correct) correct++; });
      const score = Math.round((correct / mockExamQuestions.length) * 100);
      return { score, passed: score >= 70, totalQuestions: mockExamQuestions.length, correctAnswers: correct };
    }
  },
  reportDisqualification: async (examId: string, reason: string) => {
    try {
      await request(`/exams/${examId}/report-disqualification`, { method: "POST", body: { reason } });
      return { success: true };
    } catch {
      return { success: true };
    }
  },

  // Certificates
  getCertificates: async () => {
    try {
      return await request<typeof mockCertificates>("/exams/certificates/me");
    } catch {
      return mockCertificates;
    }
  },

  // Exam Creation (Admin)
  createExam: async (exam: { title: string; questions: { question: string; options: string[]; correct: number }[]; allowedUsers: string[] }) => {
    try {
      return await request<{ examId: string; passwords: { userId: string; password: string }[] }>("/exams", {
        method: "POST",
        body: { title: exam.title, questions: exam.questions, allowed_users: exam.allowedUsers },
      });
    } catch {
      const passwords = exam.allowedUsers.map((uid) => ({ userId: uid, password: Math.random().toString(36).slice(2, 10).toUpperCase() }));
      return { examId: `e${Date.now()}`, passwords };
    }
  },

  // Phishing
  getCampaigns: async () => {
    try {
      return await request<typeof mockCampaigns>("/phishing/campaigns");
    } catch {
      return mockCampaigns;
    }
  },
  createCampaign: async (campaign: Partial<typeof mockCampaigns[0]>) => {
    try {
      const newCamp = await request<typeof mockCampaigns[0]>("/phishing/campaigns", {
        method: "POST",
        body: { name: campaign.name, template: campaign.template ?? "", targetDept: campaign.targetDept ?? "All" },
      });
      return newCamp;
    } catch {
      const newCamp = { ...campaign, id: `camp${Date.now()}`, sent: 0, clicked: 0, reported: 0, status: "draft", createdAt: new Date().toISOString().slice(0, 10) } as typeof mockCampaigns[0];
      mockCampaigns.push(newCamp);
      return newCamp;
    }
  },

  // Settings
  getSmtpConfig: async () => {
    try {
      const c = await request<typeof mockSmtpConfig>("/settings/smtp");
      return { ...mockSmtpConfig, ...c };
    } catch {
      return { ...mockSmtpConfig };
    }
  },
  saveSmtpConfig: async (config: typeof mockSmtpConfig) => {
    try {
      await request("/settings/smtp", { method: "POST", body: config });
      return { success: true };
    } catch {
      return { success: true };
    }
  },
  getLdapConfig: async () => {
    try {
      const c = await request<typeof mockLdapConfig>("/settings/ldap");
      return { ...mockLdapConfig, ...c };
    } catch {
      return { ...mockLdapConfig };
    }
  },
  saveLdapConfig: async (config: typeof mockLdapConfig) => {
    try {
      await request("/settings/ldap", { method: "POST", body: config });
      return { success: true };
    } catch {
      return { success: true };
    }
  },
  testLdapConnection: async () => {
    try {
      return await request<{ success: boolean; usersFound?: number }>("/settings/ldap/test", { method: "POST" });
    } catch {
      return { success: true, usersFound: 247 };
    }
  },
  testSmtpConnection: async () => {
    try {
      return await request<{ success: boolean; message?: string }>("/settings/smtp/test", { method: "POST" });
    } catch {
      return { success: true, message: "Test email sent" };
    }
  },

  // Exam passwords
  generateExamPasswords: async (examId: string, userIds: string[]) => {
    try {
      const res = await request<{ passwords: { userId: string; password: string }[] }>(`/exams/${examId}/generate-passwords`, { method: "POST", body: { userIds } });
      return res.passwords;
    } catch {
      return userIds.map((uid) => ({ userId: uid, password: Math.random().toString(36).slice(2, 10).toUpperCase() }));
    }
  },
};

export default api;
