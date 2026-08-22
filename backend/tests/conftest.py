import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://astrea_test:astrea_test@localhost:5432/astrea_test",
)
os.environ.setdefault("APP_ENV", "test")
