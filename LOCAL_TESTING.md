# Local run and manual test guide

This setup runs Django locally with SQLite and private files on your computer. No Supabase account, Node.js, or cloud account is needed for the MVP.

## 1. Create the local environment

From PowerShell in the project folder:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If `py` says it can't find an installed Python on this machine, use the installed interpreter directly:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m venv .venv
```

This workspace's Python launcher currently does not discover that Python 3.14 installation; the direct interpreter path works here.

Generate a local secret key:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Paste the output into `DJANGO_SECRET_KEY` in `.env`. Then initialize the SQLite database and run the site:

```powershell
python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). When signup sends an email verification link, copy it from the terminal running Django and open it in your browser.

If PowerShell blocks virtual environment activation, run the commands without activating and use `.venv\Scripts\python.exe` in place of `python`.

## 2. Creator account flow

1. Open `/accounts/signup/`, submit a name, email, and strong password.
2. Confirm signup shows the “check your email” page and the server terminal prints a confirmation link.
3. Open the link. Confirm you land in `/dashboard/` and your workspace is created.
4. Log out and log in again at `/accounts/login/`.
5. Try `/accounts/password-reset/`; use the reset link printed to the console email output.

## 3. Create, publish, and download a resource

1. In the creator dashboard, open **New resource**.
2. Upload a valid PDF, PNG, JPG, ZIP, or TXT file smaller than 25 MB.
3. Publish it and save. Open its public link from the resource list.
4. In a private browser window, open the link and download the file. Check that the download contains the original contents and filename.
5. Submit a report from the public page.
6. Back in the creator account, open Analytics and confirm the view and download activity is shown.
7. Edit the resource to a draft. Its public page and download should stop working. Edit it back to published to restore the link.

## 4. Test a second creator and tenant isolation

1. Use a private window or a second browser profile to sign up with another email address.
2. Create a resource under creator A, then sign into creator B.
3. Confirm B's dashboard and resource list do not show A's resources or analytics.
4. As B, try to visit A's edit URL. It should return 404.
5. Confirm A's published resource page is still public when opened in the private window. Public published links are meant to work for anyone who has the URL.

## 5. Test upload validation and privacy

- Try an unsupported extension, a zero-byte file, and a file larger than 25 MB; each should be rejected.
- Rename a non-PDF file to `.pdf`; signature validation should reject it.
- Confirm private storage is under `creatorhub-private` next to the project and there is no public `/media/` route.
- Confirm a draft, disabled, or unknown resource slug does not reveal its title or file.
- Confirm download uses POST with CSRF protection and the response is an attachment with `nosniff`.

## 6. Test moderation

Create a staff account from the terminal:

```powershell
python manage.py createsuperuser
```

Open `/admin/` while logged in as that account. Review the report submitted earlier and disable a test published resource. Confirm the public link and download stop working and the creator cannot edit the disabled resource. Non-staff accounts should be redirected away from `/admin/`.

The separate Django built-in admin is at `/django-admin/` and is intended for trusted operators.

## 7. Run Django's configuration checks

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

This repository does not currently include an automated test suite. These are manual checks and Django configuration/migration checks.

## Troubleshooting

- **Signup email not received:** local email is printed to the terminal running `runserver`; check that process output.
- **Login fails after signup:** open the email confirmation URL first; unverified accounts are inactive.
- **Upload rejected:** check the extension, file signature, and 25 MB size limit.
- **Uploaded file cannot be found:** check `PRIVATE_MEDIA_ROOT` and confirm the process user can write there.
- **Static styling missing:** restart Django after install, then run `python manage.py collectstatic` if using production settings.
- **VPS file access returns 404:** verify the project writes to the persistent private directory and Nginx does not expose that directory as a URL.

This is a local MVP checklist, not a complete production security review. Add and verify edge rate limits, production email delivery, backups, monitoring, and malware scanning before inviting a large audience.
