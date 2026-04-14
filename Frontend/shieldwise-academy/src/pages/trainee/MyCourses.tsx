import { useState } from "react";
import { CyberButton } from "@/components/CyberButton";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Clock, PlayCircle, CheckCircle2, BookOpen, ChevronRight } from "lucide-react";
import { mockCourses } from "@/services/api";
import { useNavigate } from "react-router-dom";

const MyCourses = () => {
  const navigate = useNavigate();
  const [courses, setCourses] = useState(mockCourses);
  const [viewingCourse, setViewingCourse] = useState<typeof mockCourses[0] | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);

  const handleViewContent = (course: typeof mockCourses[0]) => {
    setViewingCourse(course);
    setCurrentSlide(course.viewedSlides);
  };

  const handleNextSlide = () => {
    if (!viewingCourse) return;
    const next = Math.min(currentSlide + 1, viewingCourse.totalSlides);
    setCurrentSlide(next);
    setCourses((prev) =>
      prev.map((c) =>
        c.id === viewingCourse.id
          ? { ...c, viewedSlides: Math.max(c.viewedSlides, next), progress: Math.round((Math.max(c.viewedSlides, next) / c.totalSlides) * 100) }
          : c
      )
    );
    setViewingCourse((prev) => prev ? { ...prev, viewedSlides: Math.max(prev.viewedSlides, next), progress: Math.round((Math.max(prev.viewedSlides, next) / prev.totalSlides) * 100) } : null);
  };

  const canTakeExam = (course: typeof mockCourses[0]) => course.viewedSlides >= course.totalSlides && course.examId;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">My Courses</h1>
        <p className="text-sm text-muted-foreground mt-1">Complete all content before taking the assessment</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {courses.map((course, idx) => (
          <div key={course.id} className="stat-card rounded-xl p-5 flex flex-col gap-4 animate-fade-in" style={{ animationDelay: `${idx * 80}ms` }}>
            <div className="flex items-start justify-between">
              <Badge variant="outline" className={course.progress === 100 ? "bg-success/20 text-success border-success/30" : "bg-primary/20 text-primary border-primary/30"}>
                {course.progress === 100 ? "Completed" : `${course.progress}%`}
              </Badge>
              <span className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground">{course.category}</span>
            </div>

            <div className="flex-1">
              <h3 className="text-base font-semibold text-foreground mb-1.5">{course.title}</h3>
              <div className="flex items-center gap-3 text-xs text-muted-foreground mt-2">
                <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> {course.duration}</span>
                <span className="flex items-center gap-1"><BookOpen className="h-3.5 w-3.5" /> {course.modules} modules</span>
                <span>{course.viewedSlides}/{course.totalSlides} slides</span>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Content Progress</span>
                <span className="font-semibold text-foreground">{course.viewedSlides}/{course.totalSlides}</span>
              </div>
              <Progress value={(course.viewedSlides / course.totalSlides) * 100} className="h-1.5 bg-muted" />
            </div>

            <div className="flex gap-2">
              <CyberButton size="sm" className="flex-1" onClick={() => handleViewContent(course)}>
                <PlayCircle className="h-3.5 w-3.5" /> {course.progress > 0 && course.progress < 100 ? "Continue" : course.progress === 100 ? "Review" : "Start"}
              </CyberButton>
              <CyberButton
                size="sm"
                variant={canTakeExam(course) ? "default" : "ghost"}
                disabled={!canTakeExam(course)}
                onClick={() => navigate(`/exam/${course.examId}`)}
              >
                {canTakeExam(course) ? <><CheckCircle2 className="h-3.5 w-3.5" /> Start Assessment</> : "Complete content first"}
              </CyberButton>
            </div>
          </div>
        ))}
      </div>

      {/* Content Viewer Dialog */}
      <Dialog open={!!viewingCourse} onOpenChange={() => setViewingCourse(null)}>
        <DialogContent className="max-w-2xl bg-card border-border">
          <DialogHeader>
            <DialogTitle className="text-foreground">{viewingCourse?.title}</DialogTitle>
            <DialogDescription>Slide {currentSlide} of {viewingCourse?.totalSlides}</DialogDescription>
          </DialogHeader>
          <div className="rounded-lg bg-muted p-8 min-h-[250px] flex flex-col items-center justify-center text-center">
            <BookOpen className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">Module Content — Slide {currentSlide + 1}</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              This is simulated training content. In production, this would display interactive slides, videos, or embedded documents.
            </p>
          </div>
          <div className="flex items-center justify-between">
            <Progress value={((currentSlide) / (viewingCourse?.totalSlides || 1)) * 100} className="flex-1 h-2 bg-muted mr-4" />
            <CyberButton size="sm" onClick={handleNextSlide} disabled={currentSlide >= (viewingCourse?.totalSlides || 0)}>
              {currentSlide >= (viewingCourse?.totalSlides || 0) ? "Done" : <>Next <ChevronRight className="h-3.5 w-3.5" /></>}
            </CyberButton>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MyCourses;
