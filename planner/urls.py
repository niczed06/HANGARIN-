from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from .views import (
    CategoryListView,
    DashboardView,
    NotesFeedView,
    PlannerLoginView,
    PriorityListView,
    SubTaskListView,
    TaskBoardView,
)

app_name = "planner"

urlpatterns = [
    path("login/", PlannerLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("planner:login")), name="logout"),
    path("", DashboardView.as_view(), name="dashboard"),
    path("tasks/", TaskBoardView.as_view(), name="tasks"),
    path("subtasks/", SubTaskListView.as_view(), name="subtasks"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("priorities/", PriorityListView.as_view(), name="priorities"),
    path("notes/", NotesFeedView.as_view(), name="notes"),
]
