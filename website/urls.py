from django.urls import include, path

from . import views

# Namespace for reverse(), e.g. reverse("website:task-list")
app_name = "website"

urlpatterns = [
    # Regular (template-based) task pages
    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/edit/", views.TaskEditView.as_view(), name="task-edit"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task-delete"),
    # REST API, available under /website/api/v1/
    path("api/v1/", include("website.api.v1.urls")),
]
