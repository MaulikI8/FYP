# Redesign progress

Branch: `redesign/premium-learning-experiences`

## Implemented in this phase

- Split the frontend route shell, layouts, shared primitives, design tokens, and feature modules out of the old monolith.
- Rebuilt the student home, My Path, course/library, lesson studio, practice, assessment/results, knowledge map, recovery journey, progress, and contextual coach surfaces.
- Added keyboard-accessible Factorisation and Electricity labs with Django learning-event persistence.
- Connected prerequisite edges from `/knowledge-map/` to an `@xyflow/react` map with an outline view and evidence inspector.
- Added teacher classes, class evidence, concept opportunities, scoped intervention creation, and learner evidence screens.
- Added honest notification/search surfaces, persisted learner preferences, a restricted guardian summary, and explicit deferred screens.
- Added fresh factorisation assessment data and server-side response normalization for supported numeric/text formats.
- Fixed recovery ownership, teacher subject scope, guardian exposure, completion idempotency, and class aggregate sample-size handling.

## Verified

- `backend`: `manage.py check`, `makemigrations --check --dry-run`, and 15 Django tests pass.
- `frontend`: `npm run lint`, `npm run test`, and `npm run build` pass.
- Direct Django client smoke checks pass for student, teacher, coordinator, and guardian read models; the fresh assessment returns `q-math-07` and excludes the original factorisation item.

## Remaining known limits

- Browser pixel screenshots and keyboard walkthroughs were not run because browser/display tooling is unavailable in this session.
- Frontend automated coverage is still narrow; the primary persistence and permission regressions are covered in Django tests.
- Mastery, recommendations, prerequisite links, and coach guidance remain deterministic research-prototype rules rather than validated ML.
- Study-plan polish, achievements, exam readiness, reports, and cohort comparison remain explicitly deferred.

## Next concrete step

Run the local Django and Vite servers, complete the five-minute student assess → recover → fresh assessment flow, then inspect the teacher intervention follow-up at desktop and 360px widths when browser tooling is available.
