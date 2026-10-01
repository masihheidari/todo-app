from rest_framework.routers import DefaultRouter

from . import views

# Namespace for reverse(), e.g. "website:api-v1:task-list"
app_name = "api-v1"

# The router generates list/detail routes for the viewset:
#   tasks/        -> list, create
#   tasks/<pk>/   -> retrieve, update, partial_update, destroy
router = DefaultRouter()
router.register("tasks", views.TaskModelViewSet, basename="task")

urlpatterns = router.urls
