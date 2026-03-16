from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from .models import Category, Note, Priority, SubTask, Task

STATUS_TONES = {
    Task.TaskStatus.PENDING: "pending",
    Task.TaskStatus.IN_PROGRESS: "progress",
    Task.TaskStatus.COMPLETED: "complete",
}


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


class DashboardView(TemplateView):
    template_name = "planner/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today = timezone.localdate()
        task_queryset = get_task_queryset()
        total_tasks = task_queryset.count()
        completed_tasks = task_queryset.filter(status=Task.TaskStatus.COMPLETED).count()
        due_this_week = Task.objects.filter(
            deadline__date__gte=today,
            deadline__date__lte=today + timedelta(days=7),
        ).count()
        overdue_tasks = Task.objects.filter(deadline__lt=now).exclude(
            status=Task.TaskStatus.COMPLETED
        ).count()
        completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

        status_map = {
            row["status"]: row["total"]
            for row in Task.objects.values("status").annotate(total=Count("id"))
        }
        status_cards = [
            {
                "label": status,
                "count": status_map.get(status, 0),
                "tone": STATUS_TONES[status],
            }
            for status in Task.TaskStatus.values
        ]

        overview_cards = [
            {
                "label": "Total Tasks",
                "value": total_tasks,
                "caption": "Everything tracked across the workspace.",
            },
            {
                "label": "Completion Rate",
                "value": f"{completion_rate}%",
                "caption": "Based on the current task status mix.",
            },
            {
                "label": "Due This Week",
                "value": due_this_week,
                "caption": "Deadlines scheduled within the next 7 days.",
            },
            {
                "label": "Overdue",
                "value": overdue_tasks,
                "caption": "Tasks that need immediate attention.",
            },
        ]

        category_summary = Task.objects.values("category__name").annotate(
            total=Count("id")
        ).order_by("-total", "category__name")[:5]
        priority_summary = Task.objects.values("priority__name").annotate(
            total=Count("id")
        ).order_by("-total", "priority__name")[:5]

        context.update(
            {
                "active_page": "dashboard",
                "page_title": "Overview",
                "nav_stats": get_navigation_metrics(),
                "overview_cards": overview_cards,
                "status_cards": status_cards,
                "upcoming_tasks": task_queryset.filter(deadline__gte=now).order_by("deadline")[:5],
                "recent_tasks": task_queryset.order_by("-updated_at")[:6],
                "recent_notes": Note.objects.select_related("task").order_by("-created_at")[:6],
                "category_summary": category_summary,
                "priority_summary": priority_summary,
            }
        )
        return context


class TaskBoardView(TemplateView):
    template_name = "planner/tasks.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = list(get_task_queryset().order_by("deadline", "title"))
        columns = []
        for status in Task.TaskStatus.values:
            bucket = [task for task in tasks if task.status == status]
            columns.append(
                {
                    "label": status,
                    "tone": STATUS_TONES[status],
                    "count": len(bucket),
                    "tasks": bucket,
                }
            )

        context.update(
            {
                "active_page": "tasks",
                "page_title": "Task Board",
                "nav_stats": get_navigation_metrics(),
                "columns": columns,
                "task_count": len(tasks),
            }
        )
        return context


class SubTaskListView(TemplateView):
    template_name = "planner/subtasks.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subtasks = SubTask.objects.select_related(
            "task", "task__category", "task__priority"
        ).order_by("-updated_at", "-created_at")
        parent_tasks = (
            Task.objects.select_related("category", "priority")
            .annotate(
                subtask_total=Count("subtasks", distinct=True),
                completed_subtasks=Count(
                    "subtasks",
                    filter=Q(subtasks__status=Task.TaskStatus.COMPLETED),
                    distinct=True,
                ),
            )
            .filter(subtask_total__gt=0)
            .order_by("-subtask_total", "title")[:6]
        )
        status_counts = {
            row["status"]: row["total"]
            for row in SubTask.objects.values("status").annotate(total=Count("id"))
        }
        subtask_cards = [
            {
                "label": status,
                "count": status_counts.get(status, 0),
                "tone": STATUS_TONES[status],
            }
            for status in Task.TaskStatus.values
        ]

        context.update(
            {
                "active_page": "subtasks",
                "page_title": "SubTasks",
                "nav_stats": get_navigation_metrics(),
                "subtasks": subtasks[:18],
                "parent_tasks": parent_tasks,
                "subtask_cards": subtask_cards,
            }
        )
        return context


class CategoryListView(TemplateView):
    template_name = "planner/categories.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = (
            Category.objects.annotate(
                task_total=Count("tasks", distinct=True),
                completed_total=Count(
                    "tasks",
                    filter=Q(tasks__status=Task.TaskStatus.COMPLETED),
                    distinct=True,
                ),
                open_total=Count(
                    "tasks",
                    filter=Q(
                        tasks__status__in=[
                            Task.TaskStatus.PENDING,
                            Task.TaskStatus.IN_PROGRESS,
                        ]
                    ),
                    distinct=True,
                ),
            )
            .order_by("-task_total", "name")
        )
        busiest_tasks = (
            get_task_queryset()
            .order_by("-note_total", "-subtask_total", "title")[:8]
        )

        context.update(
            {
                "active_page": "categories",
                "page_title": "Categories",
                "nav_stats": get_navigation_metrics(),
                "categories": categories,
                "busiest_tasks": busiest_tasks,
            }
        )
        return context


class PriorityListView(TemplateView):
    template_name = "planner/priorities.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        priorities = (
            Priority.objects.annotate(
                task_total=Count("tasks", distinct=True),
                open_total=Count(
                    "tasks",
                    filter=Q(
                        tasks__status__in=[
                            Task.TaskStatus.PENDING,
                            Task.TaskStatus.IN_PROGRESS,
                        ]
                    ),
                    distinct=True,
                ),
                completed_total=Count(
                    "tasks",
                    filter=Q(tasks__status=Task.TaskStatus.COMPLETED),
                    distinct=True,
                ),
                overdue_total=Count(
                    "tasks",
                    filter=Q(tasks__deadline__lt=timezone.now())
                    & Q(
                        tasks__status__in=[
                            Task.TaskStatus.PENDING,
                            Task.TaskStatus.IN_PROGRESS,
                        ]
                    ),
                    distinct=True,
                ),
            )
            .order_by("-task_total", "name")
        )

        context.update(
            {
                "active_page": "priorities",
                "page_title": "Priorities",
                "nav_stats": get_navigation_metrics(),
                "priorities": priorities,
                "priority_tasks": get_task_queryset().order_by("deadline", "title")[:10],
            }
        )
        return context


class NotesFeedView(TemplateView):
    template_name = "planner/notes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notes = Note.objects.select_related(
            "task", "task__category", "task__priority"
        ).order_by("-created_at")
        task_notes = (
            Task.objects.select_related("category", "priority")
            .annotate(note_total=Count("notes"))
            .filter(note_total__gt=0)
            .order_by("-note_total", "title")[:5]
        )

        context.update(
            {
                "active_page": "notes",
                "page_title": "Notes Feed",
                "nav_stats": get_navigation_metrics(),
                "notes": notes[:18],
                "task_notes": task_notes,
            }
        )
        return context
