from django.db import migrations

PRIORITIES = ["Critical", "High", "Medium", "Low", "Optional"]
CATEGORIES = ["Work", "School", "Personal", "Finance", "Projects"]


def seed_reference_data(apps, schema_editor):
    Category = apps.get_model("planner", "Category")
    Priority = apps.get_model("planner", "Priority")

    for name in PRIORITIES:
        Priority.objects.get_or_create(name=name)

    for name in CATEGORIES:
        Category.objects.get_or_create(name=name)


def remove_reference_data(apps, schema_editor):
    Category = apps.get_model("planner", "Category")
    Priority = apps.get_model("planner", "Priority")

    Category.objects.filter(name__in=CATEGORIES).delete()
    Priority.objects.filter(name__in=PRIORITIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("planner", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, remove_reference_data),
    ]
