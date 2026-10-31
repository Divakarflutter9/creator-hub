from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django import forms
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from .forms import CreatorSignupForm
from .models import Membership, Workspace
from .models import User
from .tokens import email_verification_token
import uuid
import logging

logger = logging.getLogger("creatorhub.accounts")

def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = request.build_absolute_uri(f"/accounts/verify/{uid}/{token}/")
    body = render_to_string("accounts/verification_email.txt", {"name": user.first_name, "verify_url": verify_url})
    try:
        send_mail("Confirm your CreatorHub account", body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        return True
    except Exception:
        logger.exception("Could not send email confirmation for user id %s", user.pk)
        return False

@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")
    form = CreatorSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            base = slugify(user.first_name)[:38] or "creator"
            workspace = Workspace.objects.create(name=user.first_name, slug=f"{base}-{uuid.uuid4().hex[:8]}", owner=user)
            Membership.objects.create(workspace=workspace, user=user, role=Membership.OWNER)
        email_sent = send_verification_email(request, user)
        return render(request, "accounts/signup_sent.html", {"email": user.email, "email_sent": email_sent})
    return render(request, "accounts/signup.html", {"form": form})

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and not user.is_active and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Your email is confirmed. Welcome to CreatorHub!")
        return redirect("dashboard:dashboard")
    return render(request, "accounts/verification_failed.html", status=400)

@require_http_methods(["GET", "POST"])
def resend_verification(request):
    email = ""
    if request.method == "POST":
        try:
            email = forms.EmailField(max_length=254).clean(request.POST.get("email", "").strip().lower())
        except forms.ValidationError:
            return render(request, "accounts/resend_verification_done.html")
        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if user:
            send_verification_email(request, user)
        # Always show the same response to avoid revealing which addresses have accounts.
        return render(request, "accounts/resend_verification_done.html")
    return render(request, "accounts/resend_verification.html")

@login_required
@require_http_methods(["GET", "POST"])
def settings_page(request):
    if request.method == "POST":
        name = request.POST.get("display_name", "").strip()
        if 2 <= len(name) <= 80:
            request.user.first_name = name
            request.user.save(update_fields=["first_name"])
            workspace = get_user_workspace(request.user)
            if workspace:
                workspace.name = name
                workspace.save(update_fields=["name", "updated_at"])
            messages.success(request, "Your workspace profile was updated.")
            return redirect("accounts:settings")
        messages.error(request, "Enter a name between 2 and 80 characters.")
    return render(request, "accounts/settings.html")

def get_user_workspace(user):
    return Workspace.objects.filter(memberships__user=user, memberships__status=Membership.ACTIVE).first()
