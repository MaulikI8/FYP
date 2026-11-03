# Pathloom

**Learn with direction. Grow with evidence.**

Pathloom is a locally runnable full-stack FYP prototype for a learning intelligence layer. It connects a student's submitted answer evidence to a transparent concept map, a practical recovery path, and a teacher intervention workflow. All people, school names, curriculum mappings, attempts and metrics are fictional.

## What is implemented

- Django 5.2 + Django REST Framework under `/api/v1/`.
- Session-authenticated demo personas with backend role and ownership checks.
- SQLite by default, with a documented PostgreSQL switch point in `backend/config/settings.py`.
- Seeded Horizon Valley Secondary School with Grade 9/10 Mathematics and Science content, prerequisite links, questions, attempts, learning events, recovery plans and interventions.
- Student journey: dashboard → factorisation evidence → prerequisite map → guided recovery lab → fresh server-graded assessment → updated evidence.
- Research investigation slice: Concept Surgery performs persisted SymPy-backed factorisation experiments; Diagnostic Duel performs persisted Bayesian belief updates with information-gain question selection.
- Teacher journey: class patterns → concept opportunities → recipient-validated intervention → student recovery plan.
- Coordinator aggregate view and a linked guardian view.
- Responsive React + TypeScript shell with React Router, TanStack Query, Lucide icons, Recharts and an `@xyflow/react` prerequisite map.
- Modular frontend features under `frontend/src/features/`, shared shell/layouts under `frontend/src/layouts/`, and design tokens under `frontend/src/styles/`.
- Honest simulation boundary: scoring, mastery, gap analysis and recovery generation are deterministic Python services, not a live ML or paid AI service.
- Research boundary: Diagnostic Duel likelihoods are authored prototype assumptions and require labelled evaluation; Concept Surgery validates supported symbolic transformations but does not infer comprehension from manipulation alone.

## Run locally

### Backend

Python 3.12+ is the preferred runtime. The included project is also compatible with the available Python 3.11 runtime.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

### Frontend

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open <http://localhost:5173>. Both processes are needed for the full experience.

### Demo personas

Choose a persona on the landing page. The role picker calls Django's development-only `/api/v1/demo/login/`; it is not a client-only role toggle.

| Persona | Demo username | Primary route |
| --- | --- | --- |
| Sahana Shrestha | `sahana` | `/student/dashboard` |
| Nischal Rai | `nischal` | `/student/dashboard` |
| Aditi Gurung | `aditi` | `/student/dashboard` |
| Ms. Rina Karki | `rina` | `/teacher/dashboard` |
| Mr. Bibek Shahi | `bibek` | `/teacher/dashboard` |
| Mr. Suman Thapa | `suman` | `/coordinator/dashboard` |
| Sahana's linked guardian | `guardian_sahana` | `/guardian/dashboard` |

The demo usernames are selected through the UI; no password is required in local demo mode. The `demo_admin` account is only for local admin inspection and reset authorization.

## Checks

```bash
cd backend
source .venv/bin/activate
python manage.py check
python manage.py test apps.learning
python manage.py seed_demo        # idempotent
python manage.py reset_demo --confirm

cd ../frontend
npm run lint
npm run build
npm run test
```

`npm run test` currently covers the API client contract; the meaningful persistence, authorization, idempotency and server-grading behavior is covered in Django tests.

## Production configuration direction

Set `DJANGO_DEBUG=False`, provide a real `DJANGO_SECRET_KEY`, restrict `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`, and replace the SQLite `DATABASES` entry with PostgreSQL configuration from environment variables before deployment. Demo login and reset are disabled when debug is false.

## Prototype boundary

Mastery is a bounded heuristic based on server-graded correctness with a small-sample uncertainty band. Prerequisites are curated sample links. The tutor is a deterministic local response service. No camera permission is requested and no learner diagnosis, official readiness forecast, curriculum endorsement, causal learning claim or paid external integration is implied. Real deployment would require consent, school approval, child-data safeguards, security review and empirical evaluation.

See [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md) and [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md).
