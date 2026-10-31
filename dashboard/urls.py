from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/analytics/", views.analytics, name="analytics"),
    path("healthz/", views.health, name="health"),
]
