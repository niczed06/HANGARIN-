from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.requests import RequestSite
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from .models import Category, Note, Priority, SubTask, Task

STATUS_ORDER = [
    Task.TaskStatus.PENDING,
    Task.TaskStatus.IN_PROGRESS,
    Task.TaskStatus.COMPLETED,
]

STATUS_TONES = {
    Task.TaskStatus.PENDING: "pending",
    Task.TaskStatus.IN_PROGRESS: "progress",
    Task.TaskStatus.COMPLETED: "complete",
}


def format_long_date(value):
    return value.strftime("%A, %B %d, %Y").replace(" 0", " ")


def paginate(request, queryset, per_page=8):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def get_search_query(request):
    return request.GET.get("q", "").strip()


def get_navigation_metrics():
    today = timezone.localdate()
    return {
        "task_count": Task.objects.count(),
        "subtask_count": SubTask.objects.count(),
        "category_count": Category.objects.count(),
        "priority_count": Priority.objects.count(),
        "open_count": Task.objects.exclude(status=Task.TaskStatus.COMPLETED).count(),
        "note_count": Note.objects.count(),
        "due_today": Task.objects.filter(deadline__date=today).count(),
    }


def get_task_queryset():
    return Task.objects.select_related("priority", "category").annotate(
        subtask_total=Count("subtasks", distinct=True),
        completed_subtasks=Count(
            "subtasks",
            filter=Q(subtasks__status=Task.TaskStatus.COMPLETED),
            distinct=True,
        ),
        note_total=Count("notes", distinct=True),
    )


def get_display_name(user):
    full_name = user.get_full_name().strip()
    return full_name or user.get_username()


def provider_is_configured(request, provider_id):
    provider_app = f"allauth.socialaccount.providers.{provider_id}"
    if not apps.is_installed(provider_app):
        return False

    provider_settings = settings.SOCIALACCOUNT_PROVIDERS.get(provider_id, {})
    if provider_settings.get("APPS") or provider_settings.get("APP"):
        return True

    try:
        SocialApp = apps.get_model("socialaccount", "SocialApp")
    except LookupError:
        return False

    try:
        queryset = SocialApp.objects.filter(provider=provider_id)
        if apps.is_installed("django.contrib.sites"):
            queryset = queryset.filter(sites=get_current_site(request))
        return queryset.exists()
    except (OperationalError, ProgrammingError):
        return False


class PlannerLoginView(LoginView):
    template_name = "planner/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        try:
            current_site = get_current_site(self.request)
        except (OperationalError, ProgrammingError):
            current_site = RequestSite(self.request)
        context.update(
            {
                self.redirect_field_name: self.get_redirect_url(),
                "site": current_site,
                "site_name": current_site.name,
                "google_login_available": provider_is_configured(self.request, "google"),
                "github_login_available": provider_is_configured(self.request, "github"),
            }
        )
        return context


class PlannerBaseView(LoginRequiredMixin, TemplateView):
    active_page = ""
    page_title = ""
    primary_action_label = "New Task"
    primary_action_url = reverse_lazy("admin:planner_task_add")
    login_url = reverse_lazy("planner:login")

    def build_shell_context(self):
        today = timezone.localdate()
        display_name = get_display_name(self.request.user)
        first_name = self.request.user.first_name.strip() if self.request.user.first_name else ""
        return {
            "active_page": self.active_page,
            "page_title": self.page_title,
            "nav_stats": get_navigation_metrics(),
            "search_query": get_search_query(self.request),
            "toolbar_date": today.strftime("%b %d, %Y"),
            "toolbar_date_long": format_long_date(today),
            "toolbar_user": display_name,
            "toolbar_initial": display_name[:1].upper(),
            "primary_action_label": self.primary_action_label,
            "primary_action_url": self.primary_action_url,
            "secondary_action_label": "Log Out",
            "secondary_action_url": reverse_lazy("planner:logout"),
            "welcome_name": first_name or display_name,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.build_shell_context())
        return context


class DashboardView(PlannerBaseView):
    template_name = "planner/dashboard.html"
    active_page = "dashboard"
    page_title = "Dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        task_queryset = get_task_queryset()
        total_tasks = task_queryset.count()
        status_totals = {
            row["status"]: row["total"]
            for row in Task.objects.values("status").annotate(total=Count("id"))
        }
        hero_metrics = [
            {"label": "SubTasks", "value": context["nav_stats"]["subtask_count"]},
            {"label": "Notes", "value": context["nav_stats"]["note_count"]},
            {"label": "Categories", "value": context["nav_stats"]["category_count"]},
            {"label": "Priorities", "value": context["nav_stats"]["priority_count"]},
        ]
        overview_cards = [
            {"label": "Total Tasks", "value": total_tasks, "tone": "neutral"},
            {
                "label": "Pending",
                "value": status_totals.get(Task.TaskStatus.PENDING, 0),
                "tone": "pending",
            },
            {
                "label": "In Progress",
                "value": status_totals.get(Task.TaskStatus.IN_PROGRESS, 0),
                "tone": "progress",
            },
            {
                "label": "Completed",
                "value": status_totals.get(Task.TaskStatus.COMPLETED, 0),
                "tone": "complete",
            },
        ]

        status_rows = []
        for status in STATUS_ORDER:
            count = status_totals.get(status, 0)
            percentage = int((count / total_tasks) * 100) if total_tasks else 0
            status_rows.append(
                {
                    "label": status,
                    "count": count,
                    "percentage": percentage,
                    "tone": STATUS_TONES[status],
                }
            )

        category_rows = list(
            Task.objects.values("category__name")
            .annotate(total=Count("id"))
            .order_by("-total", "category__name")[:5]
        )
        recent_tasks = task_queryset.order_by("-updated_at")[:6]
        upcoming_tasks = list(task_queryset.filter(deadline__gte=now).order_by("deadline")[:5])
        if not upcoming_tasks:
            upcoming_tasks = list(task_queryset.order_by("deadline")[:5])

        context.update(
            {
                "hero_metrics": hero_metrics,
                "overview_cards": overview_cards,
                "status_rows": status_rows,
                "category_rows": category_rows,
                "recent_tasks": recent_tasks,
                "upcoming_tasks": upcoming_tasks,
            }
        )
        return context


class TaskBoardView(PlannerBaseView):
    template_name = "planner/tasks.html"
    active_page = "tasks"
    page_title = "Tasks"
    primary_action_label = "New Task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = context["search_query"]
        tasks = get_task_queryset().order_by("deadline", "title")
        if query:
            tasks = tasks.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
                | Q(priority__name__icontains=query)
                | Q(status__icontains=query)
            )

        page_obj = paginate(self.request, tasks, per_page=8)
        total_tasks = tasks.count()
        status_totals = {
            row["status"]: row["total"]
            for row in tasks.values("status").annotate(total=Count("id"))
        }

        context.update(
            {
                "summary_cards": [
                    {"label": "Tasks", "value": total_tasks},
                    {
                        "label": "Pending",
                        "value": status_totals.get(Task.TaskStatus.PENDING, 0),
                    },
                    {
                        "label": "In Progress",
                        "value": status_totals.get(Task.TaskStatus.IN_PROGRESS, 0),
                    },
                    {
                        "label": "Completed",
                        "value": status_totals.get(Task.TaskStatus.COMPLETED, 0),
                    },
                ],
                "page_obj": page_obj,
                "tasks": page_obj.object_list,
            }
        )
        return context


class SubTaskListView(PlannerBaseView):
    template_name = "planner/subtasks.html"
    active_page = "subtasks"
    page_title = "Sub Tasks"
    primary_action_label = "New Task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = context["search_query"]
        subtasks = SubTask.objects.select_related(
            "task", "task__category", "task__priority"
        ).order_by("-updated_at", "-created_at")
        if query:
            subtasks = subtasks.filter(
                Q(title__icontains=query)
                | Q(status__icontains=query)
                | Q(task__title__icontains=query)
            )

        page_obj = paginate(self.request, subtasks, per_page=8)
        status_totals = {
            row["status"]: row["total"]
            for row in subtasks.values("status").annotate(total=Count("id"))
        }

        context.update(
            {
                "summary_cards": [
                    {"label": "Sub Tasks", "value": subtasks.count()},
                    {
                        "label": "Pending",
                        "value": status_totals.get(Task.TaskStatus.PENDING, 0),
                    },
                    {
                        "label": "In Progress",
                        "value": status_totals.get(Task.TaskStatus.IN_PROGRESS, 0),
                    },
                    {
                        "label": "Completed",
                        "value": status_totals.get(Task.TaskStatus.COMPLETED, 0),
                    },
                ],
                "page_obj": page_obj,
                "subtasks": page_obj.object_list,
            }
        )
        return context


class CategoryListView(PlannerBaseView):
    template_name = "planner/categories.html"
    active_page = "categories"
    page_title = "Categories"
    primary_action_label = "New Task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = context["search_query"]
        categories = Category.objects.annotate(
            task_total=Count("tasks", distinct=True)
        ).order_by("name")
        if query:
            categories = categories.filter(name__icontains=query)

        page_obj = paginate(self.request, categories, per_page=8)
        context.update(
            {
                "summary_cards": [
                    {"label": "Categories", "value": categories.count()},
                    {
                        "label": "Assigned Tasks",
                        "value": sum(item.task_total for item in categories),
                    },
                ],
                "page_obj": page_obj,
                "categories": page_obj.object_list,
            }
        )
        return context


class PriorityListView(PlannerBaseView):
    template_name = "planner/priorities.html"
    active_page = "priorities"
    page_title = "Priorities"
    primary_action_label = "New Task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = context["search_query"]
        priorities = Priority.objects.annotate(
            task_total=Count("tasks", distinct=True)
        ).order_by("name")
        if query:
            priorities = priorities.filter(name__icontains=query)

        page_obj = paginate(self.request, priorities, per_page=8)
        context.update(
            {
                "summary_cards": [
                    {"label": "Priorities", "value": priorities.count()},
                    {
                        "label": "Tagged Tasks",
                        "value": sum(item.task_total for item in priorities),
                    },
                ],
                "page_obj": page_obj,
                "priorities": page_obj.object_list,
            }
        )
        return context


class NotesFeedView(PlannerBaseView):
    template_name = "planner/notes.html"
    active_page = "notes"
    page_title = "Notes"
    primary_action_label = "New Task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = context["search_query"]
        notes = Note.objects.select_related(
            "task", "task__category", "task__priority"
        ).order_by("-updated_at", "-created_at")
        if query:
            notes = notes.filter(
                Q(content__icontains=query) | Q(task__title__icontains=query)
            )

        page_obj = paginate(self.request, notes, per_page=8)
        context.update(
            {
                "summary_cards": [
                    {"label": "Notes", "value": notes.count()},
                    {
                        "label": "Tasks With Notes",
                        "value": Task.objects.annotate(note_total=Count("notes"))
                        .filter(note_total__gt=0)
                        .count(),
                    },
                ],
                "page_obj": page_obj,
                "notes": page_obj.object_list,
            }
        )
        return context
