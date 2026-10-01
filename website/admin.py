from django.contrib import admin

from .models import Task

# Register your models here.


class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "content", "is_done", "created_date"]


admin.site.register(Task, TaskAdmin)
# Register your models here.
