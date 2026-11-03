import uuid

from django.conf import settings
from django.db import models

from apps.curriculum.models import Concept, Lesson, LearningResource


class LearningEvent(models.Model):
    class Types(models.TextChoices):
        LESSON_VIEWED = "LESSON_VIEWED", "Lesson viewed"
        LESSON_COMPLETED = "LESSON_COMPLETED", "Lesson completed"
        ASSESSMENT_SUBMITTED = "ASSESSMENT_SUBMITTED", "Assessment submitted"
        RECOVERY_STEP = "RECOVERY_STEP", "Recovery step"
        TASK_COMPLETED = "TASK_COMPLETED", "Study task completed"
        NOTE_ADDED = "NOTE_ADDED", "Note added"
        LAB_INTERACTION = "LAB_INTERACTION", "Interactive lab"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_events")
    event_type = models.CharField(max_length=30, choices=Types.choices)
    resource = models.ForeignKey(LearningResource, null=True, blank=True, on_delete=models.SET_NULL)
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL)
    concepts = models.ManyToManyField(Concept, blank=True, related_name="learning_events")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["learner", "created_at"])]


class ConceptMastery(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mastery_estimates")
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="mastery_estimates")
    value = models.FloatField(default=0)
    evidence_count = models.PositiveIntegerField(default=0)
    uncertainty = models.FloatField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["learner", "concept"], name="unique_concept_mastery")]
        indexes = [models.Index(fields=["learner", "concept"])]


class StudyTask(models.Model):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        DONE = "DONE", "Done"
        SNOOZED = "SNOOZED", "Snoozed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_tasks")
    concept = models.ForeignKey(Concept, null=True, blank=True, on_delete=models.SET_NULL, related_name="study_tasks")
    title = models.CharField(max_length=180)
    due_date = models.DateField()
    minutes = models.PositiveSmallIntegerField(default=15)
    source = models.CharField(max_length=30, default="RECOMMENDED")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    updated_at = models.DateTimeField(auto_now=True)


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="notes")
    body = models.TextField()
    timestamp_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Bookmark(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="bookmarks")
    timestamp_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["learner", "lesson", "timestamp_seconds"], name="unique_bookmark")]


class AppPreferences(models.Model):
    """Small, learner-owned preferences used to shape the local demo workspace."""

    learner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="app_preferences")
    goal_minutes_per_week = models.PositiveSmallIntegerField(default=90)
    focus_subjects = models.JSONField(default=list, blank=True)
    reduced_motion = models.BooleanField(default=False)
    recommendation_categories = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
