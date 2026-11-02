import uuid

from django.conf import settings
from django.db import models


class School(models.Model):
    name = models.CharField(max_length=180)
    region = models.CharField(max_length=120, default="Bagmati Province")
    is_demo = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classrooms")
    name = models.CharField(max_length=120)
    grade = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=10, default="A")
    subject = models.ForeignKey("curriculum.Subject", null=True, blank=True, on_delete=models.SET_NULL, related_name="classrooms")
    teachers = models.ManyToManyField(settings.AUTH_USER_MODEL, through="TeacherAssignment", related_name="teaching_classes")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Enrollment", related_name="enrolled_classes")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["school", "name", "subject"], name="unique_demo_class_subject")]
        indexes = [models.Index(fields=["grade", "subject"])]

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["classroom", "student"], name="unique_enrollment")]


class TeacherAssignment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="teacher_assignments")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teacher_assignments")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["classroom", "teacher"], name="unique_teacher_assignment")]


class GuardianLink(models.Model):
    guardian = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guardian_links")
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guardian_links_received")
    relationship = models.CharField(max_length=40, default="Guardian")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["guardian", "learner"], name="unique_guardian_link")]
