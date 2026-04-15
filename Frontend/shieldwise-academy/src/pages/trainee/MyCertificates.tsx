import { useState, useEffect } from "react";
import { CyberButton } from "@/components/CyberButton";
import { Badge } from "@/components/ui/badge";
import { Award, Download, Calendar, Shield } from "lucide-react";
import { api, type Certificate } from "@/services/api";

const MyCertificates = () => {
  const [certificates, setCertificates] = useState<Certificate[]>([]);

  useEffect(() => {
    api.getCertificates().then(setCertificates);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">My Certificates</h1>
        <p className="text-sm text-muted-foreground mt-1">Earned certifications from passed assessments</p>
      </div>

      {certificates.length === 0 ? (
        <div className="stat-card rounded-xl p-12 text-center animate-fade-in">
          <Award className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No Certificates Yet</h3>
          <p className="text-sm text-muted-foreground">Complete and pass assessments to earn your certificates.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {certificates.map((cert, idx) => (
            <div key={cert.id} className="stat-card rounded-xl p-6 animate-fade-in relative overflow-hidden" style={{ animationDelay: `${idx * 80}ms` }}>
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2" />
              <div className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-primary/10 p-2.5">
                      <Award className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-foreground">{cert.examTitle}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5">Cybersecurity Certification</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="bg-success/20 text-success border-success/30">{cert.status}</Badge>
                </div>

                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-muted/50 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-primary">{cert.score}%</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Score</p>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3 text-center">
                    <p className="text-xs font-semibold text-foreground">{cert.date}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Issued</p>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3 text-center">
                    <p className="text-xs font-semibold text-foreground">{cert.expiresAt}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Expires</p>
                  </div>
                </div>

                <CyberButton variant="outline" size="sm" className="w-full">
                  <Download className="h-3.5 w-3.5" /> Download Certificate (PDF)
                </CyberButton>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyCertificates;
