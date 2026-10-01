from django.db import models
from django.utils import timezone


class Task(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_done = models.BooleanField(default=False)
    # Deleting a user also deletes their tasks
    author = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True)

    deadline_date = models.DateTimeField(null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    # Filled automatically by save() when the task is marked as done
    finished_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Keep finished_date in sync with is_done
        if self.is_done and self.finished_date is None:
            # Just marked as done: record when
            self.finished_date = timezone.now()
        elif not self.is_done:
            # Un-marked (or never done): clear the date
            self.finished_date = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
