# Hangarin

Hangarin is a Django task and to-do manager that keeps the public dashboard and Django admin on the same data model. Tasks, notes, subtasks, priorities, and categories all live in one application, so records created in the admin are reflected immediately in the frontend.

## Features

- Task, subtask, note, category, and priority models built on a shared `BaseModel`
- Django admin with filters, search, and custom task-parent display
- Seed command that uses Faker for tasks, notes, and subtasks
- Dashboard UI with a left sidebar, overview metrics, task board, and notes feed
- Lookup data for categories and priorities inserted by migration

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_hangarin --tasks 12 --clear
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the frontend and `http://127.0.0.1:8000/admin/` for the admin.

## Seeder

```powershell
python manage.py seed_hangarin --tasks 15 --max-subtasks 4 --max-notes 3 --clear
```

The command keeps the reference priorities and categories, then generates fake tasks with related subtasks and notes.

## PythonAnywhere notes

1. Create a Python 3.12 virtual environment.
2. Clone this repository on PythonAnywhere.
3. Install requirements and run `python manage.py migrate`.
4. Run `python manage.py createsuperuser`.
5. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and `DJANGO_ALLOWED_HOSTS=<your-pythonanywhere-domain>`.
6. Run `python manage.py collectstatic`.
7. Point the PythonAnywhere WSGI file to `config.wsgi`.

