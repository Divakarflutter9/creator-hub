from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("resources/", include("resources.urls")),
    path("admin/", include("moderation.urls")),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.svg", permanent=False)),
]
