from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db import connection, DatabaseError
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from accounts.models import Membership, Workspace
from resources.models import Resource, ResourceEvent

def home(request):
    return render(request, "home.html")

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return HttpResponse("unavailable", status=503, content_type="text/plain")
    response = HttpResponse("ok", content_type="text/plain")
    response["Cache-Control"] = "no-store"
    return response

def workspace_for(user):
    return Workspace.objects.filter(memberships__user=user, memberships__status=Membership.ACTIVE).distinct().first()

@login_required
def dashboard(request):
    workspace = workspace_for(request.user)
    since = timezone.now() - timedelta(days=30)
    resources = Resource.objects.filter(workspace=workspace) if workspace else Resource.objects.none()
    events = ResourceEvent.objects.filter(workspace=workspace, created_at__gte=since) if workspace else ResourceEvent.objects.none()
    popular = resources.annotate(download_count=Count("events", filter=Q(events__event_type=ResourceEvent.DOWNLOAD, events__created_at__gte=since))).order_by("-download_count", "-created_at")[:3]
    return render(request, "dashboard/home.html", {
        "workspace": workspace,
        "resource_count": resources.count(),
        "published_count": resources.filter(status=Resource.PUBLISHED).count(),
        "views": events.filter(event_type=ResourceEvent.VIEW).count(),
        "downloads": events.filter(event_type=ResourceEvent.DOWNLOAD).count(),
        "resources": resources[:5],
        "popular": popular,
    })

@login_required
def analytics(request):
    workspace = workspace_for(request.user)
    since = timezone.now() - timedelta(days=30)
    events = ResourceEvent.objects.filter(workspace=workspace, created_at__gte=since) if workspace else ResourceEvent.objects.none()
    views = events.filter(event_type=ResourceEvent.VIEW).count()
    downloads = events.filter(event_type=ResourceEvent.DOWNLOAD).count()
    by_day = []
    for offset in range(6, -1, -1):
        day = timezone.localdate() - timedelta(days=offset)
        day_events = events.filter(created_at__date=day)
        by_day.append({"date": day, "views": day_events.filter(event_type=ResourceEvent.VIEW).count(), "downloads": day_events.filter(event_type=ResourceEvent.DOWNLOAD).count()})
    resource_rows = (Resource.objects.filter(workspace=workspace).annotate(
        view_count=Count("events", filter=Q(events__event_type=ResourceEvent.VIEW, events__created_at__gte=since)),
        download_count=Count("events", filter=Q(events__event_type=ResourceEvent.DOWNLOAD, events__created_at__gte=since)),
    ).order_by("-download_count", "-view_count") if workspace else Resource.objects.none())
    return render(request, "dashboard/analytics.html", {"views": views, "downloads": downloads, "rate": round(downloads * 100 / views) if views else 0, "by_day": by_day, "resources": resource_rows[:20]})
