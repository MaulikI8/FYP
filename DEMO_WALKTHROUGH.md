# Five-minute Pathloom walkthrough

## Reset and enter

1. Start Django and Vite using the README commands.
2. Open `http://localhost:5173`.
3. If the database has been changed, choose **Settings → Reset demo** as the staff coordinator, or run `python manage.py reset_demo --confirm` locally.
4. Choose **Student · Sahana · Grade 10**.

## 0:00–1:00 — the next useful action

On `/student/dashboard`, point out the indigo **Next best action** card. It explains that factorisation is suggested because recent responses need another look and names the suggested prerequisite. Open **Continue recovery**.

## 1:00–2:00 — evidence and dependencies

Open **My knowledge** at `/student/my-knowledge`. Select the factorisation node, then open its concept page. Point out:

- the estimate and uncertainty band;
- the question-level response evidence;
- the curated link to multiplying binomials;
- the warning that a heuristic is a practice guide, not a diagnosis.

## 2:00–3:00 — recovery then reassessment

Open `/student/recovery`, choose the active factorisation plan, and mark the worked-example and reflection steps complete. Each action saves a `LearningEvent` through Django. Choose **Take fresh practice**, complete the five-question assessment, and submit. Django grades the answers; the results page shows the explanations and returns to the concept evidence.

For a reliable positive retake, answer `5x`, `(x+2)(x+3)`, `x = -2 or -3`, `3`, and `3`. Refreshing the page does not erase the attempt. Use the reset command to restore the original weak signal for another run.

## 3:00–4:00 — shared teacher evidence

Switch persona from the sidebar and choose **Ms. Rina Karki**. On `/teacher/dashboard`, open **Concept insights** and select the factorisation opportunity. Then open **Interventions**, choose factorisation, select Sahana and another Mathematics learner, and assign the support. The backend validates the recipients and creates linked recovery plans for them.

Open the student persona again: the assigned recovery path is now visible in `/student/recovery`. Return to the teacher queue to show the same database-backed intervention.

## 4:00–5:00 — close with the boundary

Briefly show **Study plan** and **Settings**. Explain that activity, assessment evidence and mastery are separate. The tutor is a deterministic local simulation, no camera is requested, and real deployment would need consent, security review and empirical research. The same story is visible in the route names: assess → diagnose → recover → improve.

If a learner has already completed the path, reset the demo and repeat. If the reset button is unavailable for a non-staff persona, run `python manage.py reset_demo --confirm` from the backend directory.
