import json

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import User
from apps.assessments.models import Answer, Assessment, Attempt
from apps.learning.models import AppPreferences, ConceptMastery, LearningEvent, StudyTask
from apps.recovery.models import RecoveryPlan


class PathloomApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def login(self, persona):
        user = User.objects.get(username=persona)
        self.client.force_login(user)
        return {"role": user.role}

    def test_assessment_payload_hides_answer_key(self):
        self.login("sahana")
        response = self.client.get("/api/v1/assessments/assessment-math-diagnostic/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("correct_answer", json.dumps(response.json()))

    def test_student_submission_is_server_graded_and_persists_mastery(self):
        self.login("sahana")
        start = self.client.post("/api/v1/assessments/assessment-math-diagnostic/attempts/", {}, content_type="application/json")
        self.assertEqual(start.status_code, 201)
        attempt_id = start.json()["id"]
        assessment = Assessment.objects.get(id="assessment-math-diagnostic")
        answers = [{"question_id": question.id, "response": question.correct_answer, "confidence": "confident", "correct": False} for question in assessment.questions.all()]
        submit = self.client.post(f"/api/v1/attempts/{attempt_id}/submit/", {"answers": answers}, content_type="application/json")
        self.assertEqual(submit.status_code, 201)
        self.assertEqual(submit.json()["score"], submit.json()["total"])
        self.assertTrue(Answer.objects.filter(attempt_id=attempt_id, is_correct=True).exists())
        self.assertTrue(ConceptMastery.objects.filter(learner__username="sahana", concept_id="MATH-ALG-07").exists())
        repeated = self.client.post(f"/api/v1/attempts/{attempt_id}/submit/", {"answers": []}, content_type="application/json")
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.json()["score"], repeated.json()["total"])

    def test_student_cannot_read_another_students_attempt(self):
        self.login("sahana")
        attempt = Attempt.objects.filter(learner__username="nischal").first()
        response = self.client.get(f"/api/v1/attempts/{attempt.id}/results/")
        self.assertIn(response.status_code, (403, 404))

    def test_teacher_cannot_assign_outside_class(self):
        self.login("rina")
        response = self.client.post("/api/v1/teacher/interventions/", {"concept_id": "MATH-ALG-07", "learner_ids": [User.objects.get(username="aditi").id], "note": "Should be blocked"}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_teacher_cannot_assign_a_concept_outside_assigned_subject(self):
        self.login("rina")
        response = self.client.post("/api/v1/teacher/interventions/", {"concept_id": "SCI-PHY-05", "learner_ids": [User.objects.get(username="sahana").id], "note": "Should be blocked"}, content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_guardian_gets_only_linked_summary(self):
        self.login("guardian_sahana")
        response = self.client.get("/api/v1/dashboard/guardian/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["learner"]["display_name"], "Sahana Shrestha")
        self.assertNotIn("concepts", response.json())
        self.assertNotIn("private_content", response.json())

    def test_student_cannot_create_recovery_plan_for_another_learner(self):
        self.login("sahana")
        other = User.objects.get(username="nischal")
        response = self.client.post("/api/v1/recovery/plans/", {"concept_id": "MATH-ALG-07", "learner_id": other.id}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(RecoveryPlan.objects.filter(learner=other, originating_concept_id="MATH-ALG-07").exists())

    def test_guardian_and_coordinator_cannot_guess_recovery_plan(self):
        plan = RecoveryPlan.objects.filter(learner__username="sahana").first()
        self.login("guardian_sahana")
        guardian_response = self.client.get(f"/api/v1/recovery/plans/{plan.id}/")
        self.assertEqual(guardian_response.status_code, 404)
        self.login("suman")
        coordinator_response = self.client.get(f"/api/v1/recovery/plans/{plan.id}/")
        self.assertEqual(coordinator_response.status_code, 404)

    def test_recovery_and_task_completion_are_idempotent(self):
        self.login("sahana")
        plan = RecoveryPlan.objects.filter(learner__username="sahana", status=RecoveryPlan.Status.ACTIVE).first()
        step = plan.steps.order_by("sequence").first()
        before_recovery = LearningEvent.objects.filter(learner__username="sahana", event_type=LearningEvent.Types.RECOVERY_STEP).count()
        first = self.client.patch(f"/api/v1/recovery/steps/{step.id}/", {"completed": True}, content_type="application/json")
        second = self.client.patch(f"/api/v1/recovery/steps/{step.id}/", {"completed": True}, content_type="application/json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(LearningEvent.objects.filter(learner__username="sahana", event_type=LearningEvent.Types.RECOVERY_STEP).count(), before_recovery + 1)

        task = StudyTask.objects.filter(learner__username="sahana", status=StudyTask.Status.PLANNED).first()
        before_task = LearningEvent.objects.filter(learner__username="sahana", event_type=LearningEvent.Types.TASK_COMPLETED).count()
        self.client.patch(f"/api/v1/study-tasks/{task.id}/", {"status": "DONE"}, content_type="application/json")
        self.client.patch(f"/api/v1/study-tasks/{task.id}/", {"status": "DONE"}, content_type="application/json")
        self.assertEqual(LearningEvent.objects.filter(learner__username="sahana", event_type=LearningEvent.Types.TASK_COMPLETED).count(), before_task + 1)

    def test_concept_actions_and_timeline_are_data_backed(self):
        self.login("sahana")
        concepts = self.client.get("/api/v1/concepts/").json()
        factorisation = next(item for item in concepts if item["id"] == "MATH-ALG-07")
        self.assertIsNotNone(factorisation["actions"]["assessment"])
        timeline = self.client.get("/api/v1/timeline/?window=30d")
        self.assertEqual(timeline.status_code, 200)
        self.assertTrue(timeline.json()["events"])

    def test_fresh_factorisation_assessment_has_a_different_item(self):
        self.login("sahana")
        response = self.client.get("/api/v1/assessments/assessment-math-fresh/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("q-math-02", {question["id"] for question in response.json()["questions"]})
        self.assertIn("q-math-07", {question["id"] for question in response.json()["questions"]})

    def test_numeric_submission_accepts_equivalent_decimal(self):
        self.login("sahana")
        start = self.client.post("/api/v1/assessments/assessment-math-diagnostic/attempts/", {"attempt_key": "numeric-equivalence-test"}, content_type="application/json")
        attempt_id = start.json()["id"]
        submit = self.client.post(f"/api/v1/attempts/{attempt_id}/submit/", {"answers": [{"question_id": "q-math-06", "response": "3.0", "confidence": "confident"}]}, content_type="application/json")
        self.assertEqual(submit.status_code, 201)
        numeric_answer = next(answer for answer in submit.json()["answers"] if answer["question_id"] == "q-math-06")
        self.assertTrue(numeric_answer["is_correct"])

    def test_lab_event_is_idempotent_by_attempt_key(self):
        self.login("sahana")
        payload = {"concept_id": "MATH-ALG-07", "kind": "factorisation_pair", "result": "x² + 7x + 12:3,4", "attempt_key": "lab-idempotence-test"}
        first = self.client.post("/api/v1/practice/lab-events/", payload, content_type="application/json")
        second = self.client.post("/api/v1/practice/lab-events/", payload, content_type="application/json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(LearningEvent.objects.filter(learner__username="sahana", event_type=LearningEvent.Types.LAB_INTERACTION, metadata__attempt_key="lab-idempotence-test").count(), 1)

    def test_teacher_aggregate_excludes_unassessed_learners(self):
        self.login("rina")
        response = self.client.get("/api/v1/dashboard/teacher/")
        self.assertEqual(response.status_code, 200)
        factorisation = next(item for item in response.json()["gaps"] if item["concept_id"] == "MATH-ALG-07")
        self.assertEqual(factorisation["sample_size"], 3)
        self.assertEqual(factorisation["evidence_count"], 6)
        self.assertEqual(factorisation["wrong_count"], 2)

    def test_preferences_validate_and_persist(self):
        self.login("sahana")
        invalid = self.client.patch("/api/v1/preferences/", {"goal_minutes_per_week": 5}, content_type="application/json")
        self.assertEqual(invalid.status_code, 400)
        saved = self.client.patch("/api/v1/preferences/", {"goal_minutes_per_week": 120, "focus_subjects": ["science"]}, content_type="application/json")
        self.assertEqual(saved.status_code, 200)
        preferences = self.client.get("/api/v1/preferences/")
        self.assertEqual(preferences.json()["goal_minutes_per_week"], 120)
        self.assertEqual(preferences.json()["focus_subjects"], ["science"])
        self.assertTrue(AppPreferences.objects.filter(learner__username="sahana", goal_minutes_per_week=120).exists())
