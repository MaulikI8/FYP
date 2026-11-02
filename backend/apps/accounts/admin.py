from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PathloomUserAdmin(UserAdmin):
    list_display = ("username", "display_name", "role", "school")
    fieldsets = UserAdmin.fieldsets + (("Pathloom profile", {"fields": ("display_name", "role", "avatar_initials", "school")}),)
