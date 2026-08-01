#!/usr/bin/env python
# =============================================================
# manage.py — Django Management CLI
# =============================================================
# This is Django's command-line utility for administrative tasks.
#
# Usage examples:
#   python manage.py runserver          — Start dev server
#   python manage.py makemigrations     — Generate migration files
#   python manage.py migrate            — Apply migrations to DB
#   python manage.py createsuperuser    — Create admin user
#   python manage.py shell_plus         — Enhanced interactive shell
#   python manage.py dbshell            — PostgreSQL psql shell
#
# Java equivalent: Maven goals / Gradle tasks (mvn spring-boot:run, etc.)
# But manage.py is a Python script, so it's simpler and more flexible.
#
# DJANGO_SETTINGS_MODULE tells Django which settings file to use.
# We default to development here. Tests override this via pytest.ini.
# =============================================================

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "the virtual environment is activated? "
            "Run: .venv\\Scripts\\activate (Windows)"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
