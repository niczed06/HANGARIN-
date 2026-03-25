from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from .views import (
    CategoryCreateView,
    CategoryListView,
    CategoryUpdateView,
    DashboardView,
    NoteCreateView,
    NoteUpdateView,
    NotesFeedView,
    PlannerLoginView,
    PriorityCreateView,
    PriorityListView,
    PriorityUpdateView,
    SubTaskCreateView,
    SubTaskListView,
    SubTaskUpdateView,
    TaskCreateView,
    TaskBoardView,
    TaskUpdateView,
)

app_name = "planner"

urlpatterns = [
    path("login/", PlannerLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("planner:login")), name="logout"),
    path("", DashboardView.as_view(), name="dashboard"),
    path("tasks/", TaskBoardView.as_view(), name="tasks"),
    path("tasks/new/", TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/edit/", TaskUpdateView.as_view(), name="task-edit"),
    path("subtasks/", SubTaskListView.as_view(), name="subtasks"),
    path("subtasks/new/", SubTaskCreateView.as_view(), name="subtask-create"),
    path("subtasks/<int:pk>/edit/", SubTaskUpdateView.as_view(), name="subtask-edit"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/new/", CategoryCreateView.as_view(), name="category-create"),
    path("categories/<int:pk>/edit/", CategoryUpdateView.as_view(), name="category-edit"),
    path("priorities/", PriorityListView.as_view(), name="priorities"),
    path("priorities/new/", PriorityCreateView.as_view(), name="priority-create"),
    path("priorities/<int:pk>/edit/", PriorityUpdateView.as_view(), name="priority-edit"),
    path("notes/", NotesFeedView.as_view(), name="notes"),
    path("notes/new/", NoteCreateView.as_view(), name="note-create"),
    path("notes/<int:pk>/edit/", NoteUpdateView.as_view(), name="note-edit"),
]
