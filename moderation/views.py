from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from resources.models import AuditLog, Resource, ResourceReport

@staff_member_required(login_url="accounts:login")
def queue(request):
    reports = ResourceReport.objects.select_related("resource", "resource__workspace").all()[:100]
    resources = Resource.objects.select_related("workspace").order_by("-created_at")[:100]
    return render(request, "moderation/queue.html", {"reports": reports, "resources": resources, "open_count": ResourceReport.objects.filter(status=ResourceReport.OPEN).count()})

@staff_member_required(login_url="accounts:login")
@require_POST
def review_report(request, report_id):
    report = get_object_or_404(ResourceReport.objects.select_related("resource"), pk=report_id)
    report.status = ResourceReport.REVIEWED
    report.reviewed_at = timezone.now()
    report.save(update_fields=["status", "reviewed_at"])
    AuditLog.objects.create(workspace=report.resource.workspace, actor=request.user, action="report.reviewed", target_type="resource_report", target_id=str(report.pk))
    messages.success(request, "Report marked reviewed.")
    return redirect("moderation:queue")

@staff_member_required(login_url="accounts:login")
@require_POST
def disable_resource(request, resource_id):
    resource = get_object_or_404(Resource.objects.select_related("workspace"), pk=resource_id)
    resource.status = Resource.DISABLED
    resource.save(update_fields=["status", "updated_at"])
    AuditLog.objects.create(workspace=resource.workspace, actor=request.user, action="resource.disabled", target_type="resource", target_id=str(resource.pk))
    messages.success(request, "Resource disabled. Its public page and download are no longer accessible.")
    return redirect("moderation:queue")
