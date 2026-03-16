import random

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from planner.models import Category, Note, Priority, SubTask, Task

PRIORITY_NAMES = ["Critical", "High", "Medium", "Low", "Optional"]
CATEGORY_NAMES = ["Work", "School", "Personal", "Finance", "Projects"]


class Command(BaseCommand):
    help = "Seed priorities, categories, tasks, notes, and subtasks."

    def add_arguments(self, parser):
        parser.add_argument("--tasks", type=int, default=10, help="Number of tasks to create.")
        parser.add_argument(
            "--max-subtasks",
            type=int,
            default=4,
            help="Maximum subtasks to generate per task.",
        )
        parser.add_argument(
            "--max-notes",
            type=int,
            default=3,
            help="Maximum notes to generate per task.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing tasks, notes, and subtasks before seeding.",
        )

    def handle(self, *args, **options):
        faker = Faker()
        task_count = max(options["tasks"], 1)
        max_subtasks = max(options["max_subtasks"], 1)
        max_notes = max(options["max_notes"], 1)

        priorities = [Priority.objects.get_or_create(name=name)[0] for name in PRIORITY_NAMES]
        categories = [Category.objects.get_or_create(name=name)[0] for name in CATEGORY_NAMES]

        if options["clear"]:
            Note.objects.all().delete()
            SubTask.objects.all().delete()
            Task.objects.all().delete()

        statuses = [choice for choice, _ in Task.TaskStatus.choices]

        for _ in range(task_count):
            deadline = faker.date_time_this_month(before_now=False, after_now=False)
            if timezone.is_naive(deadline):
                deadline = timezone.make_aware(deadline)

            task = Task.objects.create(
                title=faker.sentence(nb_words=5).rstrip("."),
                description=faker.paragraph(nb_sentences=3),
                status=faker.random_element(elements=statuses),
                deadline=deadline,
                priority=random.choice(priorities),
                category=random.choice(categories),
            )

            for _ in range(random.randint(1, max_subtasks)):
                SubTask.objects.create(
                    task=task,
                    title=faker.sentence(nb_words=4).rstrip("."),
                    status=faker.random_element(elements=statuses),
                )

            for _ in range(random.randint(1, max_notes)):
                Note.objects.create(
                    task=task,
                    content=faker.paragraph(nb_sentences=3),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {task_count} tasks with related subtasks and notes."
            )
        )
