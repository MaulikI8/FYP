export type Role = "STUDENT" | "TEACHER" | "COORDINATOR" | "GUARDIAN";
export type Mastery = { value: number; evidence_count: number; uncertainty: number; label: string };
export type User = { id: number; display_name: string; role: Role; avatar_initials: string; school: string | null; classes: Array<{ id: string; name: string; grade: number; section: string }>; destinations: string[] };
export type Concept = { id: string; title: string; description: string; subject: string; subject_slug: string; mastery: Mastery; prerequisites: Array<{ id: string; title: string }>; evidence_count: number };
export type Dashboard = { learner: User; next_action: Gap | null; concepts: Concept[]; tasks: Task[]; events: Array<{ created_at: string; event_type: string; metadata: Record<string, string | number> }>; recent_attempts: Array<{ id: string; title: string; score: number; total: number; submitted_at: string }>; courses: Course[]; recovery_plans: PlanSummary[]; stats: { assessed_concepts: number; total_concepts: number; study_events: number; average_mastery: number } };
export type Gap = { concept_id: string; concept: string; subject: string; mastery: Mastery; prerequisite: { id: string; title: string } | null; reason: string };
export type Course = { id: string; title: string; description: string; subject: string; subject_slug?: string; grade: number; units?: number };
export type Unit = { id: number; title: string; order: number; lessons: Lesson[] };
export type Lesson = { id: string; title: string; duration_minutes: number; summary: string; concepts: Array<{ id: string; title: string }> };
export type CourseDetail = Course & { units: Unit[] };
export type LessonDetail = { id: string; title: string; summary: string; duration_minutes: number; unit: string; course_id: string; concepts: Array<{ id: string; title: string }>; sections: Section[]; resources: Array<{ id: string; title: string; resource_type: string; length_minutes: number }> };
export type Section = { id: number; order: number; title: string; content: string; timestamp_start: number; timestamp_end: number; concepts: Array<{ id: string; title: string }> };
export type Question = { id: string; prompt: string; question_type: string; options: string[]; concepts: Array<{ id: string; title: string }> };
export type Assessment = { id: string; title: string; description: string; course_id: string; questions: Question[] };
export type AssessmentResult = { id: string; assessment: { id: string; title: string }; score: number; total: number; submitted_at: string; answers: Array<{ question_id: string; prompt: string; response: string; is_correct: boolean; confidence: string; correct_answer: string; explanation: string; concepts: Array<{ id: string; title: string }> }> };
export type PlanSummary = { id: string; concept_id: string; concept: string; reason: string; status: string; steps_total: number; steps_done: number };
export type Plan = { id: string; concept_id: string; concept: string; reason: string; evidence_ids: string[]; status: string; assigned_by: string | null; steps: Array<{ id: string; type: string; instruction: string; sequence: number; completed_at: string | null; resource_id: string | null }> };
export type Task = { id: string; title: string; due_date: string; minutes: number; status: string; source: string; concept: string | null; concept_id?: string | null };
export type MapData = { nodes: Array<{ id: string; label: string; subject: string; status: string; value: number; evidence_count: number }>; edges: Array<{ from: string; to: string }>; legend: string[] };
export type ConceptEvidence = { id: string; title: string; description: string; subject: string; mastery: Mastery; prerequisites: Array<{ id: string; title: string }>; dependents: Array<{ id: string; title: string }>; evidence: Array<{ id: string; assessment: string; response: string; is_correct: boolean; confidence: string; submitted_at: string; explanation: string }>; lessons: Array<{ id: string; title: string }> };
export type TeacherDashboard = { teacher: User; classrooms: Array<{ id: string; name: string; grade: number; subject: string; student_count: number }>; students_count: number; gaps: Array<{ concept_id: string; concept: string; subject: string; average: number; evidence_count: number; sample_size: number }>; interventions: Array<{ id: string; concept: string; status: string; recipient_count: number; note: string }>; positive_signal: string };

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

let csrfToken = "";
async function ensureCsrf() {
  if (csrfToken) return;
  const response = await fetch(`${API_BASE}/auth/csrf/`, { credentials: "include" });
  if (response.ok) {
    const data = (await response.json()) as { csrfToken: string };
    csrfToken = data.csrfToken;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method ?? "GET";
  if (method !== "GET") await ensureCsrf();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (csrfToken && method !== "GET") headers.set("X-CSRFToken", csrfToken);
  const response = await fetch(`${API_BASE}${path}`, { ...options, credentials: "include", headers });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({ detail: "Network request failed." }))) as { detail?: string };
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const loginDemo = (persona_id: string) => api<User>("/demo/login/", { method: "POST", body: JSON.stringify({ persona_id }) });
export const logoutDemo = () => api<{ ok: boolean }>("/auth/logout/", { method: "POST", body: "{}" });
export const getMe = () => api<User>("/me/");
export const getStudentDashboard = () => api<Dashboard>("/dashboard/student/");
export const getTeacherDashboard = () => api<TeacherDashboard>("/dashboard/teacher/");
export const getCoordinatorDashboard = () => api<{ school: string; learner_count: number; class_count: number; subjects: Array<{ subject: string; average_mastery: number; evidence_count: number; learners: number }>; note: string }>("/dashboard/coordinator/");
export const getGuardianDashboard = () => api<Dashboard>("/dashboard/guardian/");
export const getCourses = () => api<Course[]>("/courses/");
export const getCourse = (id: string) => api<CourseDetail>(`/courses/${id}/`);
export const getLesson = (id: string) => api<LessonDetail>(`/lessons/${id}/`);
export const getAssessment = (id: string) => api<Assessment>(`/assessments/${id}/`);
export const startAttempt = (id: string, attempt_key?: string) => api<{ id: string; assessment_id: string }>(`/assessments/${id}/attempts/`, { method: "POST", body: JSON.stringify({ attempt_key }) });
export const submitAttempt = (id: string, answers: Array<{ question_id: string; response: string; confidence: string }>) => api<AssessmentResult>(`/attempts/${id}/submit/`, { method: "POST", body: JSON.stringify({ answers }) });
export const getAttemptResult = (id: string) => api<AssessmentResult>(`/attempts/${id}/results/`);
export const getKnowledgeMap = () => api<MapData>("/knowledge-map/");
export const getConceptEvidence = (id: string) => api<ConceptEvidence>(`/concepts/${id}/evidence/`);
export const getPlans = () => api<Plan[]>("/recovery/plans/");
export const createPlan = (concept_id: string, learner_id?: number) => api<Plan>("/recovery/plans/", { method: "POST", body: JSON.stringify({ concept_id, learner_id }) });
export const getPlan = (id: string) => api<Plan>(`/recovery/plans/${id}/`);
export const completeStep = (id: string) => api<Plan>(`/recovery/steps/${id}/`, { method: "PATCH", body: JSON.stringify({ completed: true }) });
export const getTasks = () => api<Task[]>("/study-tasks/");
export const updateTask = (id: string, update: { status?: string; due_date?: string }) => api<Task>(`/study-tasks/${id}/`, { method: "PATCH", body: JSON.stringify(update) });
export const saveNote = (lesson_id: string, body: string, timestamp_seconds: number) => api<{ id: string }>("/notes/", { method: "POST", body: JSON.stringify({ lesson_id, body, timestamp_seconds }) });
export const getTeacherClasses = () => api<TeacherDashboard["classrooms"]>("/teacher/classes/");
export const getClassInsights = (id: string) => api<{ class: { id: string; name: string; grade: number; subject: string }; students: Array<{ id: number; name: string; evidence_count: number }>; concepts: Array<{ id: string; title: string; evidence_count: number; average: number }> }>(`/teacher/classes/${id}/insights/`);
export const getInterventions = () => api<Array<{ id: string; concept_id: string; concept: string; note: string; status: string; due_date: string | null; recipients: Array<{ id: number; name: string; completed_at: string | null }> }>>("/teacher/interventions/");
export const createIntervention = (concept_id: string, learner_ids: number[], note: string) => api<{ id: string; concept: string; status: string; recipient_count: number }>("/teacher/interventions/", { method: "POST", body: JSON.stringify({ concept_id, learner_ids, note }) });
export const resetDemo = () => api<{ ok: boolean }>("/demo/reset/", { method: "POST", body: "{}" });
