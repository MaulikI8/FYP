import { Navigate, Outlet, Route, Routes, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Compass } from "lucide-react";
import { getMe, type Role, type User } from "../lib/api";
import { AppShell, homeFor } from "../layouts/AppShell";
import { LoadingState } from "../components/ui/Primitives";
import { LandingPage } from "../features/auth/LandingPage";
import { StudentDashboardPage, MyPathPage, LearnLibraryPage, CoursePage, PracticePage } from "../features/dashboard/StudentPages";
import { LessonStudioPage } from "../features/lessons/LessonStudioPage";
import { ConceptEvidencePage, KnowledgeMapPage } from "../features/knowledge/KnowledgeMapPage";
import { RecoveryHubPage, RecoveryJourneyPage } from "../features/recovery/RecoveryPages";
import { AssessmentPlayerPage, AssessmentResultsPage } from "../features/assessments/AssessmentPages";
import { ProgressPage } from "../features/progress/ProgressPage";
import { TeacherHomePage, TeacherClassesPage, ClassInsightsPage, TeacherConceptInsightsPage, TeacherInterventionsPage, TeacherStudentPage } from "../features/teacher/TeacherPages";
import { CoachPage, ContentMapPage, CoordinatorPage, DeferredPage, GuardianPage, ProfilePage, SettingsPage } from "../features/secondary/SecondaryPages";

export default function AppRouter() {
  const me = useQuery({ queryKey: ["me"], queryFn: getMe, retry: false });
  if (me.isLoading) return <LoadingState />;
  return <Routes>
    <Route path="/" element={me.data ? <Navigate to={homeFor(me.data.role)} replace /> : <LandingPage />} />
    <Route element={<AuthBoundary user={me.data} />}>
      <Route element={<AppShellBoundary user={me.data} />}>
        <Route element={<RoleBoundary user={me.data} roles={["STUDENT"]} />}>
          <Route path="/student/dashboard" element={<StudentDashboardPage />} />
          <Route path="/student/my-path" element={<MyPathPage />} />
          <Route path="/student/learn" element={<LearnLibraryPage />} />
          <Route path="/student/learn/:courseId" element={<CoursePage />} />
          <Route path="/student/lesson/:lessonId" element={<LessonStudioPage />} />
          <Route path="/student/practice" element={<PracticePage />} />
          <Route path="/student/assessment/:assessmentId" element={<AssessmentPlayerPage />} />
          <Route path="/student/assessment/:assessmentId/results" element={<AssessmentResultsPage />} />
          <Route path="/student/my-knowledge" element={<KnowledgeMapPage />} />
          <Route path="/student/concepts/:conceptId" element={<ConceptEvidencePage />} />
          <Route path="/student/recovery" element={<RecoveryHubPage />} />
          <Route path="/student/recovery/:planId" element={<RecoveryJourneyPage />} />
          <Route path="/student/progress" element={<ProgressPage />} />
          <Route path="/student/tutor" element={<CoachPage />} />
          <Route path="/student/profile" element={<ProfilePage />} />
          <Route path="/student/study-plan" element={<DeferredPage title="Study plan polish" reason="The persisted task endpoint remains available. The redesigned core keeps the deeper concept journey ahead of a calendar surface." />} />
          <Route path="/student/exam-readiness" element={<DeferredPage title="Exam readiness" reason="Readiness remains P2 until the assessment bank has enough varied evidence to support an honest coverage view." />} />
          <Route path="/student/achievements" element={<DeferredPage title="Learning portfolio" reason="No certificate issuance model exists yet, so Pathloom does not fabricate achievements." />} />
        </Route>
        <Route element={<RoleBoundary user={me.data} roles={["TEACHER"]} />}>
          <Route path="/teacher/dashboard" element={<TeacherHomePage />} />
          <Route path="/teacher/classes" element={<TeacherClassesPage />} />
          <Route path="/teacher/classes/:classId" element={<ClassInsightsPage />} />
          <Route path="/teacher/concept-insights" element={<TeacherConceptInsightsPage />} />
          <Route path="/teacher/interventions" element={<TeacherInterventionsPage />} />
          <Route path="/teacher/students/:studentId" element={<TeacherStudentPage />} />
          <Route path="/teacher/assignments" element={<DeferredPage title="Practice assignments" reason="Assignments are intentionally hidden from the primary navigation until their persisted assignment model is distinct from recovery interventions." />} />
          <Route path="/teacher/reports" element={<DeferredPage title="Evidence reports" reason="Reports remain deferred until the backend exposes a print-safe, time-windowed report contract." />} />
        </Route>
        <Route element={<RoleBoundary user={me.data} roles={["COORDINATOR"]} />}>
          <Route path="/coordinator/dashboard" element={<CoordinatorPage />} />
          <Route path="/coordinator/content" element={<ContentMapPage />} />
          <Route path="/coordinator/cohorts" element={<DeferredPage title="Cohort comparison" reason="Aggregate comparison remains P2 until sample-size-aware cohort endpoints are implemented." />} />
        </Route>
        <Route element={<RoleBoundary user={me.data} roles={["GUARDIAN"]} />}><Route path="/guardian/dashboard" element={<GuardianPage />} /></Route>
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Route>
  </Routes>;
}

function AuthBoundary({ user }: { user: User | undefined }) { if (!user) return <Navigate to="/" replace />; return <Outlet />; }
function AppShellBoundary({ user }: { user: User | undefined }) { if (!user) return <Navigate to="/" replace />; return <AppShell user={user}><Outlet /></AppShell>; }
function RoleBoundary({ user, roles }: { user: User | undefined; roles: Role[] }) { if (!user || !roles.includes(user.role)) return <Navigate to={user ? homeFor(user.role) : "/"} replace />; return <Outlet />; }
function NotFound() { return <div className="not-found-v2"><div className="deferred-mark"><Compass size={24} /></div><h1>That path is not in this map.</h1><p>Return to your workspace and keep learning.</p><Link className="button button-primary" to="/">Back to Pathloom <ArrowRight size={15} /></Link></div>; }
