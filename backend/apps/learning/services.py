from decimal import Decimal, InvalidOperation

from apps.assessments.models import Answer, Assessment, Question
from apps.curriculum.models import Concept


def mastery_label(value, evidence_count):
    if evidence_count == 0:
        return "Not assessed"
    if value < 0.45:
        return "Emerging"
    if value < 0.65:
        return "Developing"
    if value < 0.82:
        return "Proficient"
    return "Strong"


def compute_mastery(learner, concept):
    answers = Answer.objects.filter(attempt__learner=learner, attempt__submitted_at__isnull=False, question__concepts=concept).order_by("attempt__submitted_at")
    total = answers.count()
    if not total:
        return {"value": 0, "evidence_count": 0, "uncertainty": 1, "label": "Not assessed"}
    weighted = list(answers.values_list("is_correct", flat=True))
    value = round((sum(1 for correct in weighted if correct) + 0.5) / (total + 1), 2)
    uncertainty = round(max(0.12, 0.48 / (total ** 0.5)), 2)
    return {"value": value, "evidence_count": total, "uncertainty": uncertainty, "label": mastery_label(value, total)}


def response_matches(question, response):
    """Compare supported formats without exposing answer keys to clients."""
    submitted = str(response or "").strip()
    expected = question.correct_answer.strip()
    if question.question_type == Question.Types.NUMERIC:
        try:
            return Decimal(submitted) == Decimal(expected)
        except (InvalidOperation, ValueError):
            return False
    return "".join(submitted.casefold().split()) == "".join(expected.casefold().split())


def assessment_for_concept(concept):
    """Prefer a seeded fresh practice set when one exists for this concept."""
    assessments = Assessment.objects.filter(questions__concepts=concept).distinct().order_by("id")
    return assessments.filter(id="assessment-math-fresh").first() or assessments.first()


def refresh_mastery(learner, concepts):
    from .models import ConceptMastery

    rows = []
    for concept in concepts:
        result = compute_mastery(learner, concept)
        row, _ = ConceptMastery.objects.update_or_create(learner=learner, concept=concept, defaults={key: value for key, value in result.items() if key != "label"})
        rows.append(row)
    return rows


def gap_analysis(learner):
    gaps = []
    for concept in Concept.objects.select_related("subject").prefetch_related("prerequisites__prerequisite"):
        result = compute_mastery(learner, concept)
        if result["evidence_count"] and result["value"] < 0.65:
            prerequisite = next((link.prerequisite for link in concept.prerequisites.all() if compute_mastery(learner, link.prerequisite)["value"] < 0.65), None)
            assessment = assessment_for_concept(concept)
            gaps.append({
                "concept_id": concept.id,
                "concept": concept.title,
                "subject": concept.subject.display_name,
                "mastery": result,
                "prerequisite": {"id": prerequisite.id, "title": prerequisite.title} if prerequisite else None,
                "reason": "Recent answers suggest this skill needs another worked example.",
                "recommended_lesson_id": str(concept.lessons.order_by("unit__order", "id").first().id) if concept.lessons.exists() else None,
                "recommended_assessment_id": assessment.id if assessment else None,
            })
    return sorted(gaps, key=lambda item: (item["mastery"]["value"], -item["mastery"]["evidence_count"]))


def generate_recovery_plan(learner, concept, assigned_by=None):
    from apps.curriculum.models import LearningResource
    from apps.recovery.models import RecoveryPlan, RecoveryStep

    existing = RecoveryPlan.objects.filter(learner=learner, originating_concept=concept, status=RecoveryPlan.Status.ACTIVE).first()
    if existing:
        if assigned_by and existing.assigned_by_id != assigned_by.id:
            existing.assigned_by = assigned_by
            existing.save(update_fields=["assigned_by", "updated_at"])
        return existing
    prerequisites = [link.prerequisite for link in concept.prerequisites.select_related("prerequisite")[:2]]
    resources = list(LearningResource.objects.filter(concepts=concept).distinct()[:2])
    plan = RecoveryPlan.objects.create(
        learner=learner,
        originating_concept=concept,
        reason=f"A targeted path for {concept.title}, based on {compute_mastery(learner, concept)['evidence_count']} question-level evidence items and its curated prerequisite path.",
        evidence_ids=[str(answer.id) for answer in Answer.objects.filter(attempt__learner=learner, question__concepts=concept, is_correct=False)[:4]],
        assigned_by=assigned_by,
    )
    primary_resource = resources[0] if resources else None
    RecoveryStep.objects.create(plan=plan, step_type=RecoveryStep.Types.LESSON, resource=primary_resource, sequence=1, instruction=f"Review the worked example for {concept.title} and write down the transformation that felt least clear.")
    RecoveryStep.objects.create(plan=plan, step_type=RecoveryStep.Types.REFLECTION, resource=primary_resource, sequence=2, instruction="Rate your confidence, then explain the idea in one sentence without looking at the example.")
    RecoveryStep.objects.create(plan=plan, step_type=RecoveryStep.Types.PRACTICE, resource=primary_resource, sequence=3, instruction="Complete a fresh practice item. A checked step is progress, not proof of mastery.")
    return plan
