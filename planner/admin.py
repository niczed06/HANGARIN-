from django.contrib import admin

from .models import Category, Note, Priority, SubTask, Task

admin.site.site_header = "Hangarin Admin"
admin.site.site_title = "Hangarin Admin"
admin.site.index_title = "Manage tasks, notes, and priorities"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "deadline", "priority", "category")
    list_filter = ("status", "priority", "category")
    search_fields = ("title", "description")
    list_select_related = ("priority", "category")
    ordering = ("deadline",)


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "parent_task_name")
    list_filter = ("status",)
    search_fields = ("title",)
    list_select_related = ("task",)

    @admin.display(ordering="task__title", description="Parent Task")
    def parent_task_name(self, obj):
        return obj.task.title


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("task", "content_preview", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content",)
    list_select_related = ("task",)

    @admin.display(description="Content")
    def content_preview(self, obj):
        if len(obj.content) <= 80:
            return obj.content
        return f"{obj.content[:77]}..."
