from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.info_page, {"page": "about"}, name="about"),
    path("privacy/", views.info_page, {"page": "privacy"}, name="privacy"),
    path("terms/", views.info_page, {"page": "terms"}, name="terms"),
    path("contact/", views.info_page, {"page": "contact"}, name="contact"),
    path("content-guidelines/", views.info_page, {"page": "content-guidelines"}, name="content_guidelines"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/analytics/", views.analytics, name="analytics"),
    path("healthz/", views.health, name="health"),
]
