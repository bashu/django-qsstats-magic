import os

SECRET_KEY = "DUMMY_SECRET_KEY"  # noqa: S105

# Application definition

PROJECT_APPS = ["qsstats.tests", "qsstats"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    *PROJECT_APPS,
]

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
#
# Defaults to an in-memory SQLite database. Set DB_ENGINE=postgres or
# DB_ENGINE=mysql (with the matching POSTGRES_*/MYSQL_* env vars) to run
# against a real database instead - see .github/workflows/test.yml, which
# is currently the only place that does this.

DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite")

if DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "qsstats"),
            "USER": os.environ.get("POSTGRES_USER", "qsstats"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "qsstats"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        },
    }
elif DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("MYSQL_DATABASE", "qsstats"),
            "USER": os.environ.get("MYSQL_USER", "qsstats"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", "qsstats"),
            "HOST": os.environ.get("MYSQL_HOST", "localhost"),
            "PORT": os.environ.get("MYSQL_PORT", "3306"),
        },
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        },
    }

USE_TZ = os.environ.get("USE_TZ", "true").lower() not in ("0", "false")
