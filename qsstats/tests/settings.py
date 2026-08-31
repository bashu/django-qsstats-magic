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

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

USE_TZ = os.environ.get("USE_TZ", "true").lower() not in ("0", "false")
