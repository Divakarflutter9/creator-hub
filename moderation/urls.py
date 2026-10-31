from django.urls import path
from . import views

app_name = "moderation"
urlpatterns = [
    path("", views.queue, name="queue"),
    path("reports/<int:report_id>/review/", views.review_report, name="review_report"),
    path("resources/<uuid:resource_id>/disable/", views.disable_resource, name="disable_resource"),
]
