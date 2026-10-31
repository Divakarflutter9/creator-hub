import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTION_ENV_FILE = Path(os.environ.get("DJANGO_ENV_FILE", "/etc/creatorhub/creatorhub.env"))
if PRODUCTION_ENV_FILE.is_file():
    load_dotenv(PRODUCTION_ENV_FILE, override=False)
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me-before-deploy-7Xq2vR5pD9kL")
DEBUG = os.environ.get("DJANGO_DEBUG", "1").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
if not DEBUG:
    production_required = ["DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "DJANGO_CSRF_TRUSTED_ORIGINS", "POSTGRES_DB", "POSTGRES_PASSWORD", "PRIVATE_MEDIA_ROOT", "EMAIL_HOST", "DEFAULT_FROM_EMAIL"]
    missing_production = [name for name in production_required if not os.environ.get(name)]
    if missing_production:
        raise ImproperlyConfigured("Missing production environment values: " + ", ".join(missing_production))
    if SECRET_KEY.startswith("dev-only-") or len(SECRET_KEY) < 50:
        raise ImproperlyConfigured("Set a unique random DJANGO_SECRET_KEY of at least 50 characters in production.")
    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("Wildcards are not permitted in production DJANGO_ALLOWED_HOSTS.")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("Set one or more exact hostnames in DJANGO_ALLOWED_HOSTS.")
    if not any(origin.startswith("https://") for origin in os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"].split(",")):
        raise ImproperlyConfigured("Set the HTTPS site origin in DJANGO_CSRF_TRUSTED_ORIGINS.")
    if os.environ.get("DJANGO_TRUST_PROXY", "0") != "1" or os.environ.get("DJANGO_SSL_REDIRECT", "1") != "1":
        raise ImproperlyConfigured("Production requires HTTPS redirect and the trusted reverse-proxy header configuration.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "resources",
    "dashboard",
    "moderation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "creatorhub.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "creatorhub.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "creatorhub.wsgi.application"
ASGI_APPLICATION = "creatorhub.asgi.application"

if os.environ.get("POSTGRES_DB"):
    database_options = {"connect_timeout": 5}
    if os.environ.get("POSTGRES_SSLMODE"):
        database_options["sslmode"] = os.environ["POSTGRES_SSLMODE"]
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ.get("POSTGRES_USER", "creatorhub"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": database_options,
    }}
else:
    if not DEBUG:
        raise ImproperlyConfigured("SQLite is only permitted in development; configure PostgreSQL for production.")
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "resources.storage.PrivateFileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
PRIVATE_MEDIA_ROOT = Path(os.environ.get("PRIVATE_MEDIA_ROOT", BASE_DIR.parent / "creatorhub-private"))
if PRIVATE_MEDIA_ROOT.resolve().is_relative_to(BASE_DIR):
    raise ImproperlyConfigured("PRIVATE_MEDIA_ROOT must be outside the project directory and static web root.")
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:dashboard"
LOGOUT_REDIRECT_URL = "dashboard:home"
EMAIL_BACKEND = os.environ.get("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "CreatorHub <no-reply@example.com>")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "0").lower() in {"1", "true", "yes"}
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "0").lower() in {"1", "true", "yes"}
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured("Use either EMAIL_USE_TLS or EMAIL_USE_SSL, not both.")
if not DEBUG:
    if EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
        raise ImproperlyConfigured("The console email backend is for development only.")
    if EMAIL_HOST.lower() not in {"localhost", "127.0.0.1", "::1"} and not (EMAIL_USE_TLS or EMAIL_USE_SSL):
        raise ImproperlyConfigured("Remote SMTP connections must use TLS or SSL.")

CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if os.environ.get("DJANGO_TRUST_PROXY", "0") == "1" else None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "creatorhub_sessionid"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = "creatorhub_csrftoken"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = not DEBUG and os.environ.get("DJANGO_SSL_REDIRECT", "1") == "1"
SECURE_HSTS_SECONDS = 0 if DEBUG else int(os.environ.get("DJANGO_HSTS_SECONDS", "300"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("DJANGO_HSTS_INCLUDE_SUBDOMAINS", "0").lower() in {"1", "true", "yes"}
SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_HSTS_PRELOAD", "0").lower() in {"1", "true", "yes"}
PASSWORD_RESET_TIMEOUT = 60 * 60 * 2

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "creatorhub": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
    },
}
