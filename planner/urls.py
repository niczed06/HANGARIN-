from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from .views import (
    CategoryCreateView,
    CategoryListView,
    DashboardView,
    NoteCreateView,
    NotesFeedView,
    PlannerLoginView,
    PriorityCreateView,
    PriorityListView,
    SubTaskCreateView,
    SubTaskListView,
    TaskCreateView,
    TaskBoardView,
)

app_name = "planner"

urlpatterns = [
    path("login/", PlannerLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("planner:login")), name="logout"),
    path("", DashboardView.as_view(), name="dashboard"),
    path("tasks/", TaskBoardView.as_view(), name="tasks"),
    path("tasks/new/", TaskCreateView.as_view(), name="task-create"),
    path("subtasks/", SubTaskListView.as_view(), name="subtasks"),
    path("subtasks/new/", SubTaskCreateView.as_view(), name="subtask-create"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/new/", CategoryCreateView.as_view(), name="category-create"),
    path("priorities/", PriorityListView.as_view(), name="priorities"),
    path("priorities/new/", PriorityCreateView.as_view(), name="priority-create"),
    path("notes/", NotesFeedView.as_view(), name="notes"),
    path("notes/new/", NoteCreateView.as_view(), name="note-create"),
]
