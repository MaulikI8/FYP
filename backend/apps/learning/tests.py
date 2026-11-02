import json

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import User
from apps.assessments.models import Answer, Assessment, Attempt
from apps.learning.models import ConceptMastery


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

    def test_guardian_gets_only_linked_summary(self):
        self.login("guardian_sahana")
        response = self.client.get("/api/v1/dashboard/guardian/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["learner"]["display_name"], "Sahana Shrestha")
        self.assertFalse(response.json()["private_content"]["tutor_messages"])
