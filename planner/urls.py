from django.urls import path

from .views import (
    CategoryListView,
    DashboardView,
    NotesFeedView,
    PriorityListView,
    SubTaskListView,
    TaskBoardView,
)

app_name = "planner"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("tasks/", TaskBoardView.as_view(), name="tasks"),
    path("subtasks/", SubTaskListView.as_view(), name="subtasks"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("priorities/", PriorityListView.as_view(), name="priorities"),
    path("notes/", NotesFeedView.as_view(), name="notes"),
]
