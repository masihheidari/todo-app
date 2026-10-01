from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from users.models import CustomUser

from .models import Task


@receiver([post_save, post_delete], sender=Task)
def clear_task_cache(sender, instance, **kwargs):
    """Invalidate cached task lists whenever a task is saved or deleted."""
    # The author's own list (what a student sees)
    cache.delete(f"task_list_user_{instance.author_id}")

    # Lists shared by admins and teachers (they see every task).
    # Keys must match website.cache_utils.task_list_cache_key.
    cache.delete(f"task_list_role_{CustomUser.Role.ADMIN}")
    cache.delete(f"task_list_role_{CustomUser.Role.TEACHER}")
