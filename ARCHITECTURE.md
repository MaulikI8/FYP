# Pathloom architecture

## Request flow

1. The React app calls the typed functions in `frontend/src/lib/api.ts` with `credentials: include`.
2. Vite proxies `/api/` to Django during development.
3. Django session authentication resolves the current fictional user. `demo/login` is the only development-only identity switch.
4. DRF views derive ownership and role from `request.user`; client-supplied student or role identifiers are never used as authorization.
5. Django ORM records are the source of truth. React Query caches read models and invalidates them after mutations.
6. Python services in `apps/learning/services.py` calculate mastery, gap suggestions and recovery plan steps.

## Main entities

```text
School
 ├─ Classroom ── Enrollment ── User(student)
 ├─ Classroom ── TeacherAssignment ── User(teacher)
 └─ GuardianLink ── User(guardian) → User(learner)

Subject → Course → Unit → Lesson → LessonSection
Subject → Concept ↔ ConceptPrerequisite → Concept
Concept ← QuestionConcept → Question ← AssessmentQuestion → Assessment
User(learner) → Attempt → Answer → Question
User(learner) → LearningEvent / ConceptMastery / StudyTask / Note
User(learner) → RecoveryPlan → RecoveryStep
User(teacher) → Intervention → InterventionRecipient → User(learner)
```

Important records use UUIDs where the record can be exposed to a browser. Stable concept/question/assessment slugs make the seeded graph readable. Uniqueness constraints prevent duplicate enrollment, question mappings, attempt answers, plan steps and intervention recipients.

## Permission boundaries

- Students read and mutate only their own attempts, recovery plans, tasks and notes.
- Teachers read only assigned classes and their learners. Intervention recipient IDs are checked against assigned-class membership before creation.
- Coordinators receive school-level aggregates and curriculum coverage.
- Guardians receive only the explicitly linked learner's broad summary; tutor content, notes and rosters are excluded.
- A guessed ID is scoped in the query or returned as inaccessible/not found.
- Demo reset requires `DEBUG=True` and a staff demo account.

## Intelligence rules

`compute_mastery` uses submitted answer correctness with bounded smoothing:

```text
estimate = (correct_answers + 0.5) / (evidence_count + 1)
uncertainty = max(0.12, 0.48 / sqrt(evidence_count))
```

Labels are Not assessed, Emerging, Developing, Proficient or Strong. `gap_analysis` prioritizes low estimates and then checks the curated prerequisite relation for another low-evidence skill. `generate_recovery_plan` chooses an existing concept resource, then creates lesson, reflection and fresh-practice steps. Completing steps records activity but does not change mastery; only server-graded assessment evidence can do that.

This is an explainable demo engine. A future research version could replace individual services with validated models, but would need labeled data, fairness analysis and empirical evaluation.

## Frontend structure

`App.tsx` contains the compact demo shell and route-level views; `styles.css` defines the responsive visual tokens. React Query handles server state. Local React state is used only for drafts, selected filters, assessment responses and UI visibility. Student and teacher pages use the same Django records, so a submitted reassessment is visible in both places after invalidation/refetch.
