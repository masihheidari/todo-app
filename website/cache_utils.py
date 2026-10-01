def task_list_cache_key(user):
    """Return the cache key for the task list shown to this user."""
    # Admins and teachers see all tasks, so they share one key per role
    if user.role in [user.Role.ADMIN, user.Role.TEACHER]:
        return f"task_list_role_{user.role}"
    # Students only see their own tasks, so each one gets a private key
    return f"task_list_user_{user.id}"
