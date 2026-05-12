import os

# Default tests to SQLite so contributors don't need MySQL running locally.
os.environ.setdefault("DB_USE_MYSQL", "0")
os.environ.setdefault("DJANGO_DEBUG", "false")
