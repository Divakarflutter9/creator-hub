from django.contrib import admin
from .models import AuditLog, Resource, ResourceEvent, ResourceReport

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "slug", "workspace__name")
    readonly_fields = ("id", "created_at", "updated_at", "file_size", "mime_type")

@admin.register(ResourceReport)
class ResourceReportAdmin(admin.ModelAdmin):
    list_display = ("resource", "reason", "status", "created_at")
    list_filter = ("status", "reason")
    readonly_fields = ("resource", "reason", "details", "created_at")

admin.site.register(ResourceEvent)
admin.site.register(AuditLog)
