import uuid

from django.db import models


class Subject(models.Model):
    slug = models.SlugField(unique=True)
    display_name = models.CharField(max_length=100)
    icon_key = models.CharField(max_length=30, default="book-open")
    accent = models.CharField(max_length=30, default="indigo")

    def __str__(self):
        return self.display_name


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="courses")
    grade = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=160)
    description = models.TextField()
    estimated_minutes = models.PositiveIntegerField(default=360)

    def __str__(self):
        return self.title


class Unit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="units")
    title = models.CharField(max_length=160)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["course", "order"], name="unique_unit_order")]


class Concept(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="concepts")
    title = models.CharField(max_length=180)
    description = models.TextField()

    def __str__(self):
        return self.title


class ConceptPrerequisite(models.Model):
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="prerequisites")
    prerequisite = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="dependents")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["concept", "prerequisite"], name="unique_prerequisite")]


class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=180)
    duration_minutes = models.PositiveSmallIntegerField(default=15)
    summary = models.TextField()
    concepts = models.ManyToManyField(Concept, related_name="lessons")

    class Meta:
        ordering = ["unit__order", "id"]


class LessonSection(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="sections")
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=160)
    content = models.TextField()
    timestamp_start = models.PositiveSmallIntegerField(default=0)
    timestamp_end = models.PositiveSmallIntegerField(default=120)
    concepts = models.ManyToManyField(Concept, related_name="lesson_sections")

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["lesson", "order"], name="unique_section_order")]


class LearningResource(models.Model):
    class Types(models.TextChoices):
        LESSON = "LESSON", "Lesson"
        WORKED_EXAMPLE = "WORKED_EXAMPLE", "Worked example"
        PRACTICE = "PRACTICE", "Practice"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_type = models.CharField(max_length=30, choices=Types.choices)
    title = models.CharField(max_length=180)
    length_minutes = models.PositiveSmallIntegerField(default=10)
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL, related_name="resources")
    concepts = models.ManyToManyField(Concept, related_name="resources")
    body = models.TextField(blank=True)
