from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from accounts.models import Membership, Workspace
from .forms import ResourceEditForm, ResourceForm, ResourceReportForm
from .models import AuditLog, Resource, ResourceEvent

def public_resource(request, slug):
    resource = get_object_or_404(Resource.objects.select_related("workspace"), slug=slug, status=Resource.PUBLISHED)
    ResourceEvent.objects.create(workspace=resource.workspace, resource=resource, event_type=ResourceEvent.VIEW)
    return render(request, "resources/public.html", {"resource": resource, "report_form": ResourceReportForm(), "report_sent": request.GET.get("report") == "sent"})

@require_POST
def download_resource(request, slug):
    resource = get_object_or_404(Resource.objects.select_related("workspace"), slug=slug, status=Resource.PUBLISHED)
    try:
        file_handle = resource.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("This file is currently unavailable.")
    ResourceEvent.objects.create(workspace=resource.workspace, resource=resource, event_type=ResourceEvent.DOWNLOAD)
    response = FileResponse(file_handle, as_attachment=True, filename=resource.original_file_name, content_type="application/octet-stream")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response

@require_POST
def report_resource(request, slug):
    resource = get_object_or_404(Resource.objects.filter(status=Resource.PUBLISHED), slug=slug)
    form = ResourceReportForm(request.POST)
    if form.is_valid():
        report = form.save(commit=False)
        report.resource = resource
        report.save()
        messages.success(request, "Thanks for letting us know. Our team will review this resource.")
        return redirect("resources:public", slug=slug)
    return render(request, "resources/public.html", {"resource": resource, "report_form": form}, status=400)

def get_workspace_for_user(user):
    return Workspace.objects.filter(memberships__user=user, memberships__status=Membership.ACTIVE).distinct().first()

@login_required
@require_http_methods(["GET", "POST"])
def resource_create(request):
    workspace = get_workspace_for_user(request.user)
    if not workspace:
        raise Http404("Creator workspace not found.")
    form = ResourceForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            uploaded = form.cleaned_data["file"]
            from pathlib import Path
            mime_by_extension = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".zip": "application/zip", ".txt": "text/plain"}
            resource = Resource(
                workspace=workspace,
                created_by=request.user,
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                original_file_name=uploaded.name[:255],
                mime_type=mime_by_extension[Path(uploaded.name).suffix.lower()],
                file_size=uploaded.size,
                status=form.cleaned_data["visibility"],
            )
            resource.file = uploaded
            resource.save()
            AuditLog.objects.create(workspace=workspace, actor=request.user, action="resource.created", target_type="resource", target_id=str(resource.pk))
        messages.success(request, "Your resource has been saved.")
        return redirect("resources:list")
    return render(request, "resources/create.html", {"form": form})

@login_required
def resource_list(request):
    workspace = get_workspace_for_user(request.user)
    resources = Resource.objects.filter(workspace=workspace) if workspace else Resource.objects.none()
    return render(request, "resources/list.html", {"resources": resources})

@login_required
@require_http_methods(["GET", "POST"])
def resource_edit(request, resource_id):
    workspace = get_workspace_for_user(request.user)
    resource = get_object_or_404(Resource, pk=resource_id, workspace=workspace)
    if resource.status == Resource.DISABLED:
        raise Http404("This resource is unavailable for editing.")
    form = ResourceEditForm(request.POST or None, request.FILES or None, initial={
        "title": resource.title, "description": resource.description,
        "visibility": resource.status if resource.status in {Resource.DRAFT, Resource.PUBLISHED} else Resource.DRAFT,
    })
    if request.method == "POST" and form.is_valid():
        resource.title = form.cleaned_data["title"]
        resource.description = form.cleaned_data["description"]
        resource.status = form.cleaned_data["visibility"]
        old_file = resource.file
        replacement = form.cleaned_data.get("file")
        if replacement:
            from pathlib import Path
            mime_by_extension = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".zip": "application/zip", ".txt": "text/plain"}
            resource.file = replacement
            resource.original_file_name = replacement.name[:255]
            resource.mime_type = mime_by_extension[Path(replacement.name).suffix.lower()]
            resource.file_size = replacement.size
        resource.save()
        if replacement:
            old_file.delete(save=False)
        AuditLog.objects.create(workspace=workspace, actor=request.user, action="resource.updated", target_type="resource", target_id=str(resource.pk))
        messages.success(request, "Your resource was updated.")
        return redirect("resources:list")
    return render(request, "resources/edit.html", {"resource": resource, "form": form})
