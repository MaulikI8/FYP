import uuid

from django.conf import settings
from django.db import models

from apps.curriculum.models import Concept, LearningResource


class RecoveryPlan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        INCONCLUSIVE = "INCONCLUSIVE", "Inconclusive"
        DISMISSED = "DISMISSED", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recovery_plans")
    originating_concept = models.ForeignKey(Concept, on_delete=models.PROTECT, related_name="recovery_plans")
    reason = models.TextField()
    evidence_ids = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_recovery_plans")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class RecoveryStep(models.Model):
    class Types(models.TextChoices):
        LESSON = "LESSON", "Worked lesson"
        REFLECTION = "REFLECTION", "Reflection"
        PRACTICE = "PRACTICE", "Fresh practice"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(RecoveryPlan, on_delete=models.CASCADE, related_name="steps")
    step_type = models.CharField(max_length=20, choices=Types.choices)
    resource = models.ForeignKey(LearningResource, null=True, blank=True, on_delete=models.SET_NULL)
    instruction = models.TextField()
    sequence = models.PositiveSmallIntegerField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sequence"]
        constraints = [models.UniqueConstraint(fields=["plan", "sequence"], name="unique_recovery_sequence")]


class Intervention(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interventions_created")
    concept = models.ForeignKey(Concept, on_delete=models.PROTECT, related_name="interventions")
    note = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class InterventionRecipient(models.Model):
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name="recipients")
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="intervention_recipients")
    follow_up_note = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["intervention", "learner"], name="unique_intervention_recipient")]
