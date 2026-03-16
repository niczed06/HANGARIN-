from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Note, Priority, SubTask, Task


class PlannerModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.get(name="Projects")
        self.priority = Priority.objects.get(name="High")
        self.task = Task.objects.create(
            title="Launch planning page",
            description="Finish the first dashboard draft.",
            status=Task.TaskStatus.IN_PROGRESS,
            deadline=timezone.now() + timedelta(days=2),
            priority=self.priority,
            category=self.category,
        )

    def test_string_representations_are_human_readable(self):
        note = Note.objects.create(task=self.task, content="Prepare release notes.")
        subtask = SubTask.objects.create(task=self.task, title="Create wireframe")

        self.assertEqual(str(self.category), "Projects")
        self.assertEqual(str(self.priority), "High")
        self.assertEqual(str(self.task), "Launch planning page")
        self.assertEqual(str(subtask), "Launch planning page: Create wireframe")
        self.assertEqual(str(note), "Note for Launch planning page")

    def test_progress_percentage_uses_related_subtasks(self):
        SubTask.objects.create(task=self.task, title="Draft cards", status=Task.TaskStatus.COMPLETED)
        SubTask.objects.create(task=self.task, title="Style sidebar", status=Task.TaskStatus.PENDING)

        self.assertEqual(self.task.progress_percentage, 50)


class PlannerViewTests(TestCase):
    def setUp(self):
        category = Category.objects.get(name="Work")
        priority = Priority.objects.get(name="Critical")
        task = Task.objects.create(
            title="Publish schedule",
            description="Sync the task list with the dashboard.",
            deadline=timezone.now() + timedelta(days=1),
            priority=priority,
            category=category,
        )
        Note.objects.create(task=task, content="Admin changes should appear on the frontend.")
        SubTask.objects.create(task=task, title="Prepare sidebar preview")

    def test_dashboard_renders_shared_task_data(self):
        response = self.client.get(reverse("planner:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Publish schedule")
        self.assertContains(response, "Overview")
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "SubTasks")
        self.assertContains(response, "--sidebar: #1b2646;")

    def test_task_board_page_is_available(self):
        response = self.client.get(reverse("planner:tasks"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending")

    def test_additional_navigation_pages_are_available(self):
        for route_name, expected in [
            ("planner:subtasks", "Recent SubTasks"),
            ("planner:categories", "Categories"),
            ("planner:priorities", "Priorities"),
            ("planner:notes", "Notes Feed"),
        ]:
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected)


class SeedCommandTests(TestCase):
    def test_seed_command_creates_reference_and_demo_records(self):
        call_command("seed_hangarin", tasks=3, max_subtasks=2, max_notes=2, clear=True)

        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(Priority.objects.count(), 5)
        self.assertEqual(Task.objects.count(), 3)
        self.assertGreater(Note.objects.count(), 0)
        self.assertGreater(SubTask.objects.count(), 0)
