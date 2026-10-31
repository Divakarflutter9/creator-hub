from pathlib import Path
import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify

def resource_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"{instance.workspace_id}/{uuid.uuid4().hex}{suffix}"

class Resource(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    DISABLED = "disabled"
    STATUS_CHOICES = [(DRAFT, "Draft"), (PUBLISHED, "Published"), (DISABLED, "Disabled")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="resources")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="resources")
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=1000, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
    file = models.FileField(upload_to=resource_upload_path, max_length=500)
    original_file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=80)
    file_size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["workspace", "status", "created_at"], name="resource_tenant_status_idx")]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:60] or "resource"
            self.slug = f"{base}-{uuid.uuid4().hex[:10]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ResourceEvent(models.Model):
    VIEW = "view"
    DOWNLOAD = "download"
    EVENT_CHOICES = [(VIEW, "View"), (DOWNLOAD, "Download")]
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="resource_events")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=12, choices=EVENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["workspace", "created_at"], name="event_tenant_created_idx"), models.Index(fields=["resource", "event_type", "created_at"], name="event_resource_type_date_idx")]

class ResourceReport(models.Model):
    OPEN = "open"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"
    STATUS_CHOICES = [(OPEN, "Open"), (REVIEWED, "Reviewed"), (DISMISSED, "Dismissed")]
    REASON_CHOICES = [("copyright", "Copyright concern"), ("unsafe", "Unsafe or harmful"), ("spam", "Spam or misleading"), ("other", "Other")]
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="reports")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.CharField(max_length=1000, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

class AuditLog(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
