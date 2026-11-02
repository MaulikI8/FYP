import uuid

from django.conf import settings
from django.db import models

from apps.curriculum.models import Concept, Course


class Question(models.Model):
    class Types(models.TextChoices):
        MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple choice"
        NUMERIC = "NUMERIC", "Numeric"

    id = models.CharField(max_length=40, primary_key=True)
    prompt = models.TextField()
    question_type = models.CharField(max_length=30, choices=Types.choices, default=Types.MULTIPLE_CHOICE)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.CharField(max_length=200)
    explanation = models.TextField()
    difficulty = models.CharField(max_length=20, default="developing")
    concepts = models.ManyToManyField(Concept, through="QuestionConcept", related_name="questions")


class QuestionConcept(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)
    weight = models.FloatField(default=1.0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["question", "concept"], name="unique_question_concept")]


class Assessment(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assessments")
    title = models.CharField(max_length=180)
    description = models.TextField()
    max_attempts = models.PositiveSmallIntegerField(default=10)
    questions = models.ManyToManyField(Question, through="AssessmentQuestion", related_name="assessments")


class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["assessment", "question"], name="unique_assessment_question")]


class Attempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assessment_attempts")
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="attempts")
    attempt_key = models.CharField(max_length=80, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["learner", "submitted_at"])]


class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    response = models.CharField(max_length=200, blank=True)
    is_correct = models.BooleanField(default=False)
    confidence = models.CharField(max_length=20, default="unsure")
    time_spent_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["attempt", "question"], name="unique_attempt_answer")]
