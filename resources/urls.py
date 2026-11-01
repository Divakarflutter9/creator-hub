from django.urls import path
from . import views

app_name = "resources"
urlpatterns = [
    path("new/", views.resource_create, name="create"),
    path("", views.resource_list, name="list"),
    path("manage/<uuid:resource_id>/edit/", views.resource_edit, name="edit"),
    path("manage/<uuid:resource_id>/download/", views.download_managed_resource, name="managed_download"),
    path("<slug:slug>/", views.public_resource, name="public"),
    path("<slug:slug>/download/", views.download_resource, name="download"),
    path("<slug:slug>/report/", views.report_resource, name="report"),
]
