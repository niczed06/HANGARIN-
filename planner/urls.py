from django.urls import path

from .views import DashboardView, NotesFeedView, TaskBoardView

app_name = "planner"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("tasks/", TaskBoardView.as_view(), name="tasks"),
    path("notes/", NotesFeedView.as_view(), name="notes"),
]

