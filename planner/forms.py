from django import forms
from django.utils import timezone

from .models import Category, Note, Priority, SubTask, Task

DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class TaskForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        input_formats=[DATETIME_LOCAL_FORMAT],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format=DATETIME_LOCAL_FORMAT,
        ),
    )

    class Meta:
        model = Task
        fields = ["title", "description", "category", "priority", "status", "deadline"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.deadline:
            self.initial["deadline"] = timezone.localtime(
                self.instance.deadline
            ).strftime(DATETIME_LOCAL_FORMAT)


class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ["task", "title", "status"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class PriorityForm(forms.ModelForm):
    class Meta:
        model = Priority
        fields = ["name"]


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["task", "content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }
