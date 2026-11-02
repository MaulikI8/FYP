# Pathloom API notes

All private endpoints are under `/api/v1/`, use Django session cookies and require the current authenticated demo persona. The frontend calls `/auth/csrf/` before mutations and sends `X-CSRFToken`.

## Health and identity

```http
GET /api/v1/health/
→ {"status":"ready","api_version":"v1"}

POST /api/v1/demo/login/
{"persona_id":"sahana"}
→ authenticated persona payload

GET /api/v1/me/
POST /api/v1/auth/logout/
```

`demo/login` accepts only seeded fictional usernames and is disabled with `DJANGO_DEBUG=False`.

## Assessment flow

```http
GET /api/v1/assessments/assessment-math-diagnostic/
```

The response contains prompts, options and concept labels, but never `correct_answer`.

```http
POST /api/v1/assessments/assessment-math-diagnostic/attempts/
{}
→ {"id":"<attempt uuid>","created":true,"assessment_id":"assessment-math-diagnostic"}

POST /api/v1/attempts/<attempt uuid>/submit/
{
  "answers": [
    {"question_id":"q-math-02","response":"(x+2)(x+3)","confidence":"confident"}
  ]
}
```

Django compares responses against its own answer key, stores `Answer` rows, appends a `LearningEvent`, refreshes `ConceptMastery`, and returns question-level explanations. Repeating submission for a submitted attempt returns the saved result without creating duplicate answers.

## Recovery flow

```http
POST /api/v1/recovery/plans/
{"concept_id":"MATH-ALG-07"}

GET /api/v1/recovery/plans/
PATCH /api/v1/recovery/steps/<step uuid>/
{"completed":true}
```

Teacher assignment adds `learner_id` and validates that every recipient belongs to an assigned class. The response includes the evidence IDs, origin, status and ordered steps.

## Core read endpoints

| Screen | Endpoint |
| --- | --- |
| Student dashboard | `GET /dashboard/student/` |
| Teacher dashboard | `GET /dashboard/teacher/` |
| Coordinator dashboard | `GET /dashboard/coordinator/` |
| Linked guardian | `GET /dashboard/guardian/` |
| Courses / detail | `GET /courses/`, `GET /courses/{uuid}/` |
| Lesson | `GET /lessons/{uuid}/` |
| Digital Twin | `GET /knowledge-map/` |
| Concept evidence | `GET /concepts/{id}/evidence/` |
| Student tasks | `GET/PATCH /study-tasks/{uuid}/` |
| Teacher classes | `GET /teacher/classes/` |
| Class insight | `GET /teacher/classes/{uuid}/insights/` |
| Teacher learner evidence | `GET /teacher/students/{id}/evidence/` |
| Teacher interventions | `GET/POST /teacher/interventions/` |

Unauthorized access is rejected by DRF authentication/permissions; ownership and assigned-class validation happen inside the views.
