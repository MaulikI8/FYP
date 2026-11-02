from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"
        COORDINATOR = "COORDINATOR", "Coordinator"
        GUARDIAN = "GUARDIAN", "Guardian"

    display_name = models.CharField(max_length=120)
    role = models.CharField(max_length=20, choices=Roles.choices)
    avatar_initials = models.CharField(max_length=5, blank=True)
    school = models.ForeignKey("schools.School", null=True, blank=True, on_delete=models.SET_NULL, related_name="users")

    def __str__(self):
        return self.display_name or self.username
