import uuid
from datetime import date, timedelta

from django.contrib.auth import login, logout
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.assessments.models import Answer, Assessment, Attempt, Question
from apps.curriculum.models import Concept, Course, Lesson, LearningResource
from apps.learning.models import ConceptMastery, LearningEvent, Note, StudyTask
from apps.recovery.models import Intervention, InterventionRecipient, RecoveryPlan
from apps.schools.models import Classroom, Enrollment, GuardianLink, TeacherAssignment
from .services import compute_mastery, generate_recovery_plan, gap_analysis, mastery_label, refresh_mastery


def user_payload(user):
    classes = list(user.enrolled_classes.values("id", "name", "grade", "section")) if user.role == User.Roles.STUDENT else list(user.teaching_classes.values("id", "name", "grade", "section"))
    return {"id": user.id, "display_name": user.display_name, "role": user.role, "avatar_initials": user.avatar_initials, "school": user.school.name if user.school else None, "classes": [{**item, "id": str(item["id"])} for item in classes], "destinations": destination_map(user.role)}


def destination_map(role):
    if role == User.Roles.STUDENT:
        return ["/student/dashboard", "/student/learn", "/student/my-knowledge", "/student/recovery", "/student/study-plan", "/student/progress"]
    if role == User.Roles.TEACHER:
        return ["/teacher/dashboard", "/teacher/classes", "/teacher/concept-insights", "/teacher/interventions", "/teacher/assignments"]
    if role == User.Roles.COORDINATOR:
        return ["/coordinator/dashboard", "/coordinator/cohorts", "/coordinator/content"]
    return ["/guardian/dashboard"]


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ready", "api_version": "v1"})


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def demo_login(request):
    if not __import__("django.conf").conf.settings.DEBUG:
        return Response({"detail": "Demo login is disabled outside development."}, status=403)
    username = request.data.get("persona_id")
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "Choose one of the seeded demo personas."}, status=400)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return Response(user_payload(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    logout(request)
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(user_payload(request.user))


def concepts_payload(learner):
    mastery = {row.concept_id: row for row in ConceptMastery.objects.filter(learner=learner)}
    payload = []
    for concept in Concept.objects.select_related("subject").prefetch_related("prerequisites__prerequisite"):
        result = compute_mastery(learner, concept)
        row = mastery.get(concept.id)
        payload.append({"id": concept.id, "title": concept.title, "description": concept.description, "subject": concept.subject.display_name, "subject_slug": concept.subject.slug, "mastery": result, "prerequisites": [{"id": link.prerequisite_id, "title": link.prerequisite.title} for link in concept.prerequisites.all()], "evidence_count": result["evidence_count"]})
    return payload


def student_dashboard_data(user):
    concepts = concepts_payload(user)
    gaps = gap_analysis(user)
    tasks = list(StudyTask.objects.filter(learner=user).select_related("concept").order_by("due_date", "status")[:8])
    events = list(LearningEvent.objects.filter(learner=user, created_at__gte=timezone.now() - timedelta(days=7)).values("created_at", "event_type", "metadata"))
    attempts = list(Attempt.objects.filter(learner=user, submitted_at__isnull=False).select_related("assessment").order_by("-submitted_at")[:5])
    courses = list(Course.objects.select_related("subject").filter(grade=user.enrolled_classes.first().grade if user.enrolled_classes.exists() else 10))
    top_gap = gaps[0] if gaps else None
    plans = list(RecoveryPlan.objects.filter(learner=user, status=RecoveryPlan.Status.ACTIVE).select_related("originating_concept")[:3])
    return {"learner": user_payload(user), "next_action": top_gap, "concepts": concepts, "tasks": [{"id": str(t.id), "title": t.title, "due_date": t.due_date, "minutes": t.minutes, "status": t.status, "source": t.source, "concept": t.concept.title if t.concept else None} for t in tasks], "events": events, "recent_attempts": [{"id": str(a.id), "title": a.assessment.title, "score": a.score, "total": a.total, "submitted_at": a.submitted_at} for a in attempts], "courses": [{"id": str(c.id), "title": c.title, "description": c.description, "subject": c.subject.display_name, "subject_slug": c.subject.slug, "grade": c.grade} for c in courses], "recovery_plans": [{"id": str(p.id), "concept_id": p.originating_concept_id, "concept": p.originating_concept.title, "reason": p.reason, "status": p.status, "steps_total": p.steps.count(), "steps_done": p.steps.filter(completed_at__isnull=False).count()} for p in plans], "stats": {"assessed_concepts": sum(1 for c in concepts if c["evidence_count"]), "total_concepts": len(concepts), "study_events": len(events), "average_mastery": round(sum(c["mastery"]["value"] for c in concepts) / max(1, sum(1 for c in concepts if c["evidence_count"])), 2)}}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    if request.user.role != User.Roles.STUDENT:
        return Response({"detail": "Student dashboard access required."}, status=403)
    return Response(student_dashboard_data(request.user))


def teacher_students(teacher):
    return User.objects.filter(enrolled_classes__teacher_assignments__teacher=teacher, role=User.Roles.STUDENT).distinct()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    if request.user.role != User.Roles.TEACHER:
        return Response({"detail": "Teacher dashboard access required."}, status=403)
    learners = teacher_students(request.user)
    gaps = []
    for concept in Concept.objects.select_related("subject"):
        results = [compute_mastery(student, concept) for student in learners]
        assessed = [result for result in results if result["evidence_count"]]
        if assessed and sum(result["value"] for result in assessed) / len(assessed) < 0.66:
            gaps.append({"concept_id": concept.id, "concept": concept.title, "subject": concept.subject.display_name, "average": round(sum(result["value"] for result in assessed) / len(assessed), 2), "evidence_count": sum(result["evidence_count"] for result in assessed), "sample_size": len(assessed)})
    interventions = Intervention.objects.filter(teacher=request.user).select_related("concept").order_by("-created_at")[:6]
    return Response({"teacher": user_payload(request.user), "classrooms": [{"id": str(c.id), "name": c.name, "grade": c.grade, "subject": c.subject.display_name if c.subject else None, "student_count": c.enrollments.count()} for c in request.user.teaching_classes.select_related("subject")], "students_count": learners.count(), "gaps": sorted(gaps, key=lambda item: item["average"])[:6], "interventions": [{"id": str(i.id), "concept": i.concept.title, "status": i.status, "recipient_count": i.recipients.count(), "note": i.note} for i in interventions], "positive_signal": "Sahana's latest science evidence shows a clear improvement after targeted practice."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def coordinator_dashboard(request):
    if request.user.role != User.Roles.COORDINATOR:
        return Response({"detail": "Coordinator dashboard access required."}, status=403)
    school = request.user.school
    learners = User.objects.filter(school=school, role=User.Roles.STUDENT)
    subjects = []
    from apps.curriculum.models import Subject
    for subject in Subject.objects.all():
        rows = [compute_mastery(student, concept) for student in learners for concept in subject.concepts.all()]
        assessed = [row for row in rows if row["evidence_count"]]
        subjects.append({"subject": subject.display_name, "average_mastery": round(sum(row["value"] for row in assessed) / max(1, len(assessed)), 2), "evidence_count": len(assessed), "learners": learners.count()})
    return Response({"school": school.name if school else "Demo School", "learner_count": learners.count(), "class_count": school.classrooms.count() if school else 0, "subjects": subjects, "note": "Aggregates use fictional demo evidence; comparisons include sample sizes and are not school ratings."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def guardian_dashboard(request):
    if request.user.role != User.Roles.GUARDIAN:
        return Response({"detail": "Guardian dashboard access required."}, status=403)
    link = GuardianLink.objects.filter(guardian=request.user).select_related("learner").first()
    if not link:
        return Response({"detail": "No linked learner is available."}, status=404)
    data = student_dashboard_data(link.learner)
    data["private_content"] = {"tutor_messages": False, "notes": False, "class_roster": False}
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def courses(request):
    qs = Course.objects.select_related("subject").all()
    if request.user.role == User.Roles.STUDENT:
        grade = request.user.enrolled_classes.first().grade if request.user.enrolled_classes.exists() else 10
        qs = qs.filter(grade__lte=grade)
    return Response([{"id": str(c.id), "title": c.title, "description": c.description, "subject": c.subject.display_name, "subject_slug": c.subject.slug, "grade": c.grade, "units": c.units.count()} for c in qs])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_detail(request, course_id):
    try:
        course = Course.objects.select_related("subject").prefetch_related("units__lessons__concepts").get(id=course_id)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found."}, status=404)
    return Response({"id": str(course.id), "title": course.title, "description": course.description, "subject": course.subject.display_name, "grade": course.grade, "units": [{"id": unit.id, "title": unit.title, "order": unit.order, "lessons": [{"id": str(lesson.id), "title": lesson.title, "duration_minutes": lesson.duration_minutes, "summary": lesson.summary, "concepts": [{"id": c.id, "title": c.title} for c in lesson.concepts.all()]} for lesson in unit.lessons.all()]} for unit in course.units.all()]})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def lesson_detail(request, lesson_id):
    try:
        lesson = Lesson.objects.prefetch_related("sections__concepts", "concepts", "resources").get(id=lesson_id)
    except Lesson.DoesNotExist:
        return Response({"detail": "Lesson not found."}, status=404)
    return Response({"id": str(lesson.id), "title": lesson.title, "summary": lesson.summary, "duration_minutes": lesson.duration_minutes, "unit": lesson.unit.title, "course_id": str(lesson.unit.course_id), "concepts": [{"id": c.id, "title": c.title} for c in lesson.concepts.all()], "sections": [{"id": section.id, "order": section.order, "title": section.title, "content": section.content, "timestamp_start": section.timestamp_start, "timestamp_end": section.timestamp_end, "concepts": [{"id": c.id, "title": c.title} for c in section.concepts.all()]} for section in lesson.sections.all()], "resources": [{"id": str(r.id), "title": r.title, "resource_type": r.resource_type, "length_minutes": r.length_minutes} for r in lesson.resources.all()]})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def concept_list(request):
    learner = request.user if request.user.role == User.Roles.STUDENT else None
    data = concepts_payload(learner) if learner else [{"id": c.id, "title": c.title, "description": c.description, "subject": c.subject.display_name, "prerequisites": [{"id": link.prerequisite_id, "title": link.prerequisite.title} for link in c.prerequisites.all()]} for c in Concept.objects.select_related("subject").prefetch_related("prerequisites__prerequisite")]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def knowledge_map(request):
    if request.user.role != User.Roles.STUDENT:
        return Response({"detail": "Student knowledge map access required."}, status=403)
    data = concepts_payload(request.user)
    nodes = [{"id": c["id"], "label": c["title"], "subject": c["subject"], "status": c["mastery"]["label"], "value": c["mastery"]["value"], "evidence_count": c["evidence_count"]} for c in data]
    edges = [{"from": p["id"], "to": c["id"]} for c in data for p in c["prerequisites"]]
    return Response({"nodes": nodes, "edges": edges, "legend": ["Not assessed", "Emerging", "Developing", "Proficient", "Strong"]})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def concept_evidence(request, concept_id):
    if request.user.role != User.Roles.STUDENT:
        return Response({"detail": "Student concept evidence access required."}, status=403)
    try:
        concept = Concept.objects.select_related("subject").prefetch_related("prerequisites__prerequisite", "dependents__concept").get(id=concept_id)
    except Concept.DoesNotExist:
        return Response({"detail": "Concept not found."}, status=404)
    answers = Answer.objects.filter(attempt__learner=request.user, question__concepts=concept, attempt__submitted_at__isnull=False).select_related("question", "attempt__assessment").order_by("-attempt__submitted_at")[:10]
    result = compute_mastery(request.user, concept)
    return Response({"id": concept.id, "title": concept.title, "description": concept.description, "subject": concept.subject.display_name, "mastery": result, "prerequisites": [{"id": link.prerequisite_id, "title": link.prerequisite.title} for link in concept.prerequisites.all()], "dependents": [{"id": link.concept_id, "title": link.concept.title} for link in concept.dependents.all()], "evidence": [{"id": str(answer.id), "assessment": answer.attempt.assessment.title, "response": answer.response, "is_correct": answer.is_correct, "confidence": answer.confidence, "submitted_at": answer.attempt.submitted_at, "explanation": answer.question.explanation} for answer in answers], "lessons": [{"id": str(lesson.id), "title": lesson.title} for lesson in concept.lessons.all()]})


def safe_assessment(assessment):
    return {"id": assessment.id, "title": assessment.title, "description": assessment.description, "course_id": str(assessment.course_id), "questions": [{"id": q.id, "prompt": q.prompt, "question_type": q.question_type, "options": q.options, "concepts": [{"id": c.id, "title": c.title} for c in q.concepts.all()]} for q in assessment.questions.prefetch_related("concepts").all()]}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assessment_detail(request, assessment_id):
    try:
        assessment = Assessment.objects.get(id=assessment_id)
    except Assessment.DoesNotExist:
        return Response({"detail": "Assessment not found."}, status=404)
    return Response(safe_assessment(assessment))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attempt_create(request, assessment_id):
    if request.user.role != User.Roles.STUDENT:
        return Response({"detail": "Only learners can start attempts."}, status=403)
    try:
        assessment = Assessment.objects.get(id=assessment_id)
    except Assessment.DoesNotExist:
        return Response({"detail": "Assessment not found."}, status=404)
    attempt_key = request.data.get("attempt_key") or str(uuid.uuid4())
    attempt, created = Attempt.objects.get_or_create(learner=request.user, assessment=assessment, attempt_key=attempt_key, defaults={"total": assessment.questions.count()})
    return Response({"id": str(attempt.id), "created": created, "assessment_id": assessment.id}, status=201 if created else 200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attempt_submit(request, attempt_id):
    if request.user.role != User.Roles.STUDENT:
        return Response({"detail": "Only learners can submit attempts."}, status=403)
    try:
        attempt = Attempt.objects.select_related("assessment").get(id=attempt_id, learner=request.user)
    except Attempt.DoesNotExist:
        return Response({"detail": "Attempt not found."}, status=404)
    if attempt.submitted_at:
        return Response(attempt_result(attempt))
    answers = request.data.get("answers", [])
    by_question = {str(item.get("question_id")): item for item in answers}
    with transaction.atomic():
        score = 0
        for question in attempt.assessment.questions.all():
            payload = by_question.get(question.id, {})
            response = str(payload.get("response", "")).strip()
            is_correct = response.casefold() == question.correct_answer.strip().casefold()
            if is_correct:
                score += 1
            Answer.objects.create(attempt=attempt, question=question, response=response, is_correct=is_correct, confidence=payload.get("confidence", "unsure"), time_spent_seconds=int(payload.get("time_spent_seconds", 0)))
        attempt.score = score
        attempt.total = attempt.assessment.questions.count()
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["score", "total", "submitted_at"])
        concepts = list(Concept.objects.filter(questions__assessments=attempt.assessment).distinct())
        refresh_mastery(request.user, concepts)
        event = LearningEvent.objects.create(learner=request.user, event_type=LearningEvent.Types.ASSESSMENT_SUBMITTED, metadata={"attempt_id": str(attempt.id), "score": score, "total": attempt.total})
        event.concepts.set(concepts)
    return Response(attempt_result(attempt), status=201)


def attempt_result(attempt):
    return {"id": str(attempt.id), "assessment": {"id": attempt.assessment.id, "title": attempt.assessment.title}, "score": attempt.score, "total": attempt.total, "submitted_at": attempt.submitted_at, "answers": [{"question_id": a.question_id, "prompt": a.question.prompt, "response": a.response, "is_correct": a.is_correct, "confidence": a.confidence, "correct_answer": a.question.correct_answer, "explanation": a.question.explanation, "concepts": [{"id": c.id, "title": c.title} for c in a.question.concepts.all()]} for a in attempt.answers.select_related("question").prefetch_related("question__concepts").all()]}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def attempt_results(request, attempt_id):
    try:
        attempt = Attempt.objects.get(id=attempt_id, learner=request.user)
    except Attempt.DoesNotExist:
        return Response({"detail": "Attempt not found."}, status=404)
    if not attempt.submitted_at:
        return Response({"detail": "This attempt has not been submitted."}, status=400)
    return Response(attempt_result(attempt))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommendations(request):
    if request.user.role != User.Roles.STUDENT:
        return Response([])
    return Response(gap_analysis(request.user)[:5])


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def recovery_plans(request):
    if request.method == "GET":
        if request.user.role != User.Roles.STUDENT:
            return Response([])
        plans = RecoveryPlan.objects.filter(learner=request.user).select_related("originating_concept", "assigned_by")
        return Response([plan_payload(p) for p in plans])
    if request.user.role not in [User.Roles.STUDENT, User.Roles.TEACHER]:
        return Response({"detail": "This role cannot create recovery plans."}, status=403)
    concept_id = request.data.get("concept_id")
    learner_id = request.data.get("learner_id", request.user.id)
    try:
        concept = Concept.objects.get(id=concept_id)
        learner = User.objects.get(id=learner_id, role=User.Roles.STUDENT)
    except (Concept.DoesNotExist, User.DoesNotExist):
        return Response({"detail": "Concept or learner not found."}, status=400)
    if request.user.role == User.Roles.TEACHER and not teacher_students(request.user).filter(id=learner.id).exists():
        return Response({"detail": "You can only assign support to learners in your classes."}, status=403)
    plan = generate_recovery_plan(learner, concept, request.user if request.user.role == User.Roles.TEACHER else None)
    return Response(plan_payload(plan), status=201)


def plan_payload(plan):
    return {"id": str(plan.id), "concept_id": plan.originating_concept_id, "concept": plan.originating_concept.title, "reason": plan.reason, "evidence_ids": plan.evidence_ids, "status": plan.status, "assigned_by": plan.assigned_by.display_name if plan.assigned_by else None, "steps": [{"id": str(step.id), "type": step.step_type, "instruction": step.instruction, "sequence": step.sequence, "completed_at": step.completed_at, "resource_id": str(step.resource_id) if step.resource_id else None} for step in plan.steps.all()]}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recovery_plan_detail(request, plan_id):
    try:
        plan = RecoveryPlan.objects.select_related("learner", "originating_concept", "assigned_by").get(id=plan_id)
    except RecoveryPlan.DoesNotExist:
        return Response({"detail": "Recovery plan not found."}, status=404)
    if request.user.role == User.Roles.STUDENT and plan.learner_id != request.user.id:
        return Response({"detail": "Recovery plan not found."}, status=404)
    if request.user.role == User.Roles.TEACHER and not teacher_students(request.user).filter(id=plan.learner_id).exists():
        return Response({"detail": "Recovery plan not found."}, status=404)
    return Response(plan_payload(plan))


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def recovery_step_update(request, step_id):
    from apps.recovery.models import RecoveryStep
    try:
        step = RecoveryStep.objects.select_related("plan").get(id=step_id, plan__learner=request.user)
    except RecoveryStep.DoesNotExist:
        return Response({"detail": "Recovery step not found."}, status=404)
    if request.data.get("completed"):
        step.completed_at = timezone.now()
        step.save(update_fields=["completed_at"])
        LearningEvent.objects.create(learner=request.user, event_type=LearningEvent.Types.RECOVERY_STEP, metadata={"step_id": str(step.id), "plan_id": str(step.plan_id)})
        if not step.plan.steps.filter(completed_at__isnull=True).exists():
            step.plan.status = RecoveryPlan.Status.COMPLETED
            step.plan.save(update_fields=["status", "updated_at"])
    return Response(plan_payload(step.plan))


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def study_tasks(request, task_id=None):
    if request.method == "GET":
        tasks = StudyTask.objects.filter(learner=request.user).select_related("concept")
        return Response([{"id": str(t.id), "title": t.title, "due_date": t.due_date, "minutes": t.minutes, "status": t.status, "source": t.source, "concept": t.concept.title if t.concept else None, "concept_id": t.concept_id} for t in tasks])
    try:
        task = StudyTask.objects.get(id=task_id, learner=request.user)
    except StudyTask.DoesNotExist:
        return Response({"detail": "Study task not found."}, status=404)
    if "status" in request.data and request.data["status"] in StudyTask.Status.values:
        task.status = request.data["status"]
        if task.status == StudyTask.Status.DONE:
            LearningEvent.objects.create(learner=request.user, event_type=LearningEvent.Types.TASK_COMPLETED, metadata={"task_id": str(task.id), "minutes": task.minutes})
    if "due_date" in request.data:
        task.due_date = request.data["due_date"]
    task.save()
    return Response({"id": str(task.id), "title": task.title, "due_date": task.due_date, "minutes": task.minutes, "status": task.status, "source": task.source, "concept": task.concept.title if task.concept else None})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def notes(request):
    if request.method == "GET":
        return Response([{"id": str(note.id), "lesson_id": str(note.lesson_id), "body": note.body, "timestamp_seconds": note.timestamp_seconds, "created_at": note.created_at} for note in Note.objects.filter(learner=request.user)])
    try:
        lesson = Lesson.objects.get(id=request.data.get("lesson_id"))
    except Lesson.DoesNotExist:
        return Response({"detail": "Lesson not found."}, status=400)
    note = Note.objects.create(learner=request.user, lesson=lesson, body=request.data.get("body", "").strip(), timestamp_seconds=int(request.data.get("timestamp_seconds", 0)))
    LearningEvent.objects.create(learner=request.user, event_type=LearningEvent.Types.NOTE_ADDED, lesson=lesson, metadata={"note_id": str(note.id)})
    return Response({"id": str(note.id), "lesson_id": str(note.lesson_id), "body": note.body, "timestamp_seconds": note.timestamp_seconds}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_classes(request):
    if request.user.role != User.Roles.TEACHER:
        return Response({"detail": "Teacher access required."}, status=403)
    return Response([{"id": str(c.id), "name": c.name, "grade": c.grade, "subject": c.subject.display_name if c.subject else None, "student_count": c.enrollments.count()} for c in request.user.teaching_classes.select_related("subject")])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_class_insights(request, class_id):
    if request.user.role != User.Roles.TEACHER or not request.user.teaching_classes.filter(id=class_id).exists():
        return Response({"detail": "Class not found."}, status=404)
    classroom = Classroom.objects.select_related("subject").get(id=class_id)
    learners = User.objects.filter(enrolled_classes=classroom)
    concepts = Concept.objects.filter(subject=classroom.subject)
    return Response({"class": {"id": str(classroom.id), "name": classroom.name, "grade": classroom.grade, "subject": classroom.subject.display_name if classroom.subject else None}, "students": [{"id": student.id, "name": student.display_name, "evidence_count": Answer.objects.filter(attempt__learner=student).count()} for student in learners], "concepts": [{"id": c.id, "title": c.title, "evidence_count": sum(compute_mastery(student, c)["evidence_count"] for student in learners), "average": round(sum(compute_mastery(student, c)["value"] for student in learners) / max(1, learners.count()), 2)} for c in concepts]})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_student_evidence(request, student_id):
    if request.user.role != User.Roles.TEACHER or not teacher_students(request.user).filter(id=student_id).exists():
        return Response({"detail": "Learner not found."}, status=404)
    student = User.objects.get(id=student_id)
    data = concepts_payload(student)
    return Response({"student": user_payload(student), "concepts": data, "attempts": [attempt_result(attempt) for attempt in Attempt.objects.filter(learner=student, submitted_at__isnull=False).select_related("assessment").order_by("-submitted_at")[:5]], "recovery_plans": [plan_payload(plan) for plan in RecoveryPlan.objects.filter(learner=student).select_related("originating_concept")]})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def teacher_interventions(request):
    if request.user.role != User.Roles.TEACHER:
        return Response({"detail": "Teacher access required."}, status=403)
    if request.method == "GET":
        interventions = Intervention.objects.filter(teacher=request.user).select_related("concept").prefetch_related("recipients__learner")
        return Response([{"id": str(i.id), "concept_id": i.concept_id, "concept": i.concept.title, "note": i.note, "status": i.status, "due_date": i.due_date, "recipients": [{"id": r.learner_id, "name": r.learner.display_name, "completed_at": r.completed_at} for r in i.recipients.all()]} for i in interventions])
    concept_id = request.data.get("concept_id")
    recipient_ids = request.data.get("learner_ids", [])
    allowed = teacher_students(request.user).filter(id__in=recipient_ids)
    if len(recipient_ids) != allowed.count() or not concept_id:
        return Response({"detail": "Select learners from your assigned classes."}, status=400)
    try:
        concept = Concept.objects.get(id=concept_id)
    except Concept.DoesNotExist:
        return Response({"detail": "Concept not found."}, status=400)
    intervention = Intervention.objects.create(teacher=request.user, concept=concept, note=request.data.get("note", "Targeted practice based on class evidence."), due_date=request.data.get("due_date"), status=Intervention.Status.ASSIGNED)
    for learner in allowed:
        InterventionRecipient.objects.create(intervention=intervention, learner=learner)
        generate_recovery_plan(learner, concept, request.user)
    return Response({"id": str(intervention.id), "concept": concept.title, "status": intervention.status, "recipient_count": len(recipient_ids)}, status=201)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def notifications(request, notification_id=None):
    from apps.notifications.models import Notification
    if request.method == "GET":
        return Response([{"id": str(n.id), "title": n.title, "body": n.body, "destination": n.destination, "read": bool(n.read_at), "created_at": n.created_at} for n in Notification.objects.filter(recipient=request.user)])
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
    except Notification.DoesNotExist:
        return Response({"detail": "Notification not found."}, status=404)
    notification.read_at = timezone.now()
    notification.save(update_fields=["read_at"])
    return Response({"id": str(notification.id), "read": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response({"courses": [], "concepts": [], "learners": []})
    concepts = Concept.objects.filter(title__icontains=query)[:10]
    course_rows = Course.objects.filter(title__icontains=query)[:10]
    learner_rows = teacher_students(request.user).filter(display_name__icontains=query)[:10] if request.user.role in [User.Roles.TEACHER, User.Roles.COORDINATOR] else []
    return Response({"courses": [{"id": str(c.id), "title": c.title} for c in course_rows], "concepts": [{"id": c.id, "title": c.title} for c in concepts], "learners": [{"id": s.id, "name": s.display_name} for s in learner_rows]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def demo_reset(request):
    if not __import__("django.conf").conf.settings.DEBUG or not request.user.is_staff:
        return Response({"detail": "Only a local demo admin can reset data."}, status=403)
    from django.core.management import call_command
    call_command("seed_demo", reset=True, verbosity=0)
    return Response({"ok": True})
