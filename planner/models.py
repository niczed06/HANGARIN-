from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Priority(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Priority"
        verbose_name_plural = "Priorities"

    def __str__(self):
        return self.name


class Task(BaseModel):
    class TaskStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        IN_PROGRESS = "In Progress", "In Progress"
        COMPLETED = "Completed", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    deadline = models.DateTimeField()
    priority = models.ForeignKey(
        Priority,
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tasks",
    )

    class Meta:
        ordering = ("deadline", "-updated_at")

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.status != self.TaskStatus.COMPLETED and self.deadline < timezone.now()

    @property
    def progress_percentage(self):
        total = getattr(self, "subtask_total", None)
        completed = getattr(self, "completed_subtasks", None)

        if total is None:
            total = self.subtasks.count()
        if completed is None:
            completed = self.subtasks.filter(status=self.TaskStatus.COMPLETED).count()

        if total == 0:
            return 0
        return int((completed / total) * 100)

    @property
    def note_total_value(self):
        total = getattr(self, "note_total", None)
        return total if total is not None else self.notes.count()


class SubTask(BaseModel):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="subtasks",
    )
    title = models.CharField(max_length=200)
    status = models.CharField(
        max_length=50,
        choices=Task.TaskStatus.choices,
        default=Task.TaskStatus.PENDING,
    )

    class Meta:
        ordering = ("task", "created_at")

    def __str__(self):
        return f"{self.task.title}: {self.title}"


class Note(BaseModel):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    content = models.TextField()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Note for {self.task.title}"
