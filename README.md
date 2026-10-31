# CreatorHub

CreatorHub is a multi-creator resource sharing MVP built with Django. Creators verify an email address, receive an isolated workspace, upload useful files, publish shareable links, and see basic view/download activity.

## Stack

- Django 5.2 LTS, Python, and Django templates
- Django authentication and PostgreSQL-ready Django ORM
- SQLite by default for local development
- Private filesystem storage for uploads; uploaded files are never served from the static or public media URL
- WhiteNoise for static assets; Gunicorn + Nginx for a Linux VPS

## Local development

Use Python 3.12 or newer. From PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DJANGO_SECRET_KEY` in `.env` to a new random value. Run migrations and start Django:

```powershell
python manage.py migrate
python manage.py runserver
```

Visit `http://127.0.0.1:8000`. Local email uses Django's console backend; signup verification links appear in the server terminal. For a full local checklist, see [LOCAL_TESTING.md](LOCAL_TESTING.md).

Local runs use SQLite and keep private uploads in a sibling `creatorhub-private` directory. Neither the database nor user uploads are inside Django's static web directory.

## Main routes

- `/` — public landing page
- `/accounts/signup/`, `/accounts/login/` — creator account flows
- `/dashboard/` — creator overview
- `/resources/` — creator resource management
- `/resources/<slug>/` — public resource page
- `/resources/<slug>/download/` — protected attachment response
- `/admin/` — platform moderation queue for staff accounts
- `/django-admin/` — Django's built-in administration

## Data and tenant isolation

Each creator gets a `Workspace` and an active `Membership`. All creator resource and analytics queries are scoped through the signed-in user's active workspace membership. Resource edit routes also bind the resource to that workspace before returning it. Public routes expose only published resources addressed by their unguessable slug. Platform staff can moderate across workspaces.

This MVP uses application-level tenant scoping and database constraints in Django. It does not use PostgreSQL row-level security; any new query involving creator data must resolve and filter by the authorized workspace. Review tenant-scoped query paths when adding APIs or background jobs.

## File handling

Uploads are limited to 25 MB and PDF, PNG, JPEG, ZIP, or TXT. The form checks file signatures, then stores the file under a random workspace-prefixed name in `PRIVATE_MEDIA_ROOT`. That directory must remain outside the Nginx document root and must not be configured as a public media URL. Downloads are streamed through an authorization view as attachments; filenames and storage paths are not used as URLs.

The local filesystem backend suits the MVP on one VPS. For multiple app servers or larger volume, configure a private S3-compatible storage backend and retain the same authorization check before issuing a short-lived object URL. Add malware scanning before opening uploads to a large public audience.

## VPS deployment

Use the step-by-step [VPS deployment guide](deploy/VPS_DEPLOYMENT.md). It is written for a shared VPS: separate service account, loopback port, PostgreSQL database, private upload directory, systemd unit, and hostname-specific Nginx vhost. It includes a config validation/reload sequence, HTTPS setup, rate limits, backups, and rollback instructions. No VPS or other live site is changed from this workspace.

## MVP boundaries

Included: creator accounts and email verification, isolated workspaces, resource create/edit/publish/draft, private uploads and downloads, public resource pages, simple analytics, reporting, staff moderation, audit events, and responsive templates.

Later work: creator teams, S3 storage backend, malware scanning, richer analytics, brand ad management, AdSense, billing, and public integrations. Nginx rate-limit examples are included for the Linux VPS deployment. No queue or microservice is needed for this first version.
