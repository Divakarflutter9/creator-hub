# Deploy CreatorHub beside existing websites

This procedure adds CreatorHub as an independent Django service and one hostname-specific Nginx virtual host. It does not replace existing site files, change DNS for other hostnames, bind Django publicly, or open another firewall port. The examples use `/srv/creatorhub`, a dedicated `creatorhub` Linux account, PostgreSQL database `creatorhub_prod`, and loopback port `8017`; change those values consistently if your server uses them already.

The first Nginx config is tested before every reload. Nginx reloads its workers gracefully after accepting valid configuration; existing virtual hosts remain in the loaded config. Django is served by its own Gunicorn service, and later releases can reload only CreatorHub's Gunicorn workers.

## Important boundaries

- Do not run `systemctl restart nginx`, stop existing web services, edit existing `server {}` blocks, or replace the default Nginx site for this deployment.
- Do not expose port `8017` publicly. It is bound to `127.0.0.1`; only the local Nginx proxy reaches it.
- Create a separate app account, PostgreSQL role/database, systemd unit, private uploads directory, and Nginx hostname for CreatorHub.
- Keep the private uploads directory outside every site's web root. The provided Nginx config does not map it to a URL.
- These examples target Linux with systemd, Nginx, PostgreSQL, and Certbot. If your VPS uses Apache, a hosting panel, or a nonstandard Nginx layout, stop before enabling a vhost and adapt the proxy config to that setup.

## 0. Gather details and check for conflicts

Before installing anything, record the VPS distribution/version, Nginx version and active include layout, PostgreSQL availability, the hostname to use, SMTP provider details, free disk/RAM, and the desired private upload path.

Run read-only checks first:

```bash
cat /etc/os-release
nginx -v
sudo nginx -T
sudo ss -ltnp
df -h
free -h
systemctl --type=service --state=running
```

Check that `creatorhub.example.com` is not already assigned to another virtual host and that `127.0.0.1:8017` is unused. If that port is occupied, choose another unused loopback port and change it in both the systemd and Nginx examples. Confirm you have backups and a rollback window for the Nginx configuration.

Use a dedicated hostname such as `creatorhub.example.com` or `resources.example.com`; avoid hosting it at `/` on a hostname already serving another site. Add only that hostname's DNS record, pointing to this VPS. Leave existing DNS records alone.

If traffic passes through Cloudflare or another proxy/CDN, tell me before deploying or configure Nginx's real-IP module using only that provider's published proxy IP ranges. Do not trust arbitrary `X-Forwarded-For` values; the rate-limit examples key on the IP Nginx sees.

## 1. Back up and prepare the isolated app paths

Back up the Nginx configuration and PostgreSQL before making changes. Do not store these backups in a web root. For Debian/Ubuntu-style paths, a root-only archive is one option:

```bash
sudo install -d -o root -g root -m 0700 /root/creatorhub-deploy-backup
sudo tar -C /etc/nginx -czf /root/creatorhub-deploy-backup/nginx-before-creatorhub.tgz .
```

Create the dedicated Linux account and storage directories. If the account or paths already exist, inspect their ownership instead of overwriting them.

```bash
sudo useradd --system --home-dir /srv/creatorhub --shell /usr/sbin/nologin creatorhub
sudo install -d -o root -g creatorhub -m 0750 /srv/creatorhub
sudo install -d -o creatorhub -g creatorhub -m 0750 /srv/creatorhub/app
sudo install -d -o root -g creatorhub -m 0750 /etc/creatorhub
sudo install -d -o creatorhub -g creatorhub -m 0700 /var/lib/creatorhub/private
```

If `useradd` reports the account already exists, continue only after confirming it is the dedicated CreatorHub account. Copy or clone this project into `/srv/creatorhub/app`, then set ownership on that app directory:

```bash
sudo chown -R creatorhub:creatorhub /srv/creatorhub/app
sudo -u creatorhub python3 -m venv /srv/creatorhub/app/.venv
sudo -u creatorhub /srv/creatorhub/app/.venv/bin/pip install -r /srv/creatorhub/app/requirements.txt
```

Use the Python version supported by the installed Django 5.2 release (Python 3.12+ is a suitable target). Don't change the VPS's system Python or other apps' virtual environments.

## 2. Give CreatorHub its own PostgreSQL database

Use the existing PostgreSQL server if one is already managed on this VPS. Create a dedicated least-privilege login role and database; do not use a superuser application account and do not change PostgreSQL's global listen address or restart it for this app.

As a PostgreSQL administrator, create a role and database. Generate a long random password and use a value that is easy to paste safely into the environment file (avoid shell quoting mistakes):

```sql
CREATE ROLE creatorhub_app LOGIN PASSWORD 'REPLACE_WITH_A_LONG_RANDOM_PASSWORD';
CREATE DATABASE creatorhub_prod OWNER creatorhub_app ENCODING 'UTF8';
```

If PostgreSQL is not installed, do not install or reconfigure it blindly on a shared production VPS. Use an existing managed PostgreSQL service or ask for a server-specific plan first. Keep its network access restricted to this app host.

## 3. Create the private production environment file

Copy the example outside the repository and edit it as root:

```bash
sudo install -o root -g creatorhub -m 0640 /srv/creatorhub/app/deploy/creatorhub.env.example /etc/creatorhub/creatorhub.env
sudoedit /etc/creatorhub/creatorhub.env
```

Set the real hostname in `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, the PostgreSQL role/database/password, persistent `PRIVATE_MEDIA_ROOT`, and real SMTP settings. Set `DJANGO_SECRET_KEY` from a fresh random value, for example:

```bash
sudo -u creatorhub /srv/creatorhub/app/.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

Keep `DJANGO_DEBUG=0`, `DJANGO_TRUST_PROXY=1`, `DJANGO_SSL_REDIRECT=1`, and `DJANGO_HSTS_INCLUDE_SUBDOMAINS=0`. Start with the example HSTS age of 300 seconds; increase it after HTTPS has been stable. Subdomain inclusion and preload remain off so this hostname's policy does not automatically cover sibling sites. `POSTGRES_SSLMODE=prefer` suits a local database; use `require` for a remote PostgreSQL provider that supports TLS.

The sample uses SMTP submission with STARTTLS on port 587. Use the exact TLS mode and port your mail provider specifies. Do not keep the example SMTP values or password in the file.

## 4. Apply migrations, collect static files, and check production settings

The project settings load `/etc/creatorhub/creatorhub.env` through `DJANGO_ENV_FILE`. Run management commands as the app user:

```bash
sudo -u creatorhub env DJANGO_ENV_FILE=/etc/creatorhub/creatorhub.env /srv/creatorhub/app/.venv/bin/python /srv/creatorhub/app/manage.py check --deploy
sudo -u creatorhub env DJANGO_ENV_FILE=/etc/creatorhub/creatorhub.env /srv/creatorhub/app/.venv/bin/python /srv/creatorhub/app/manage.py migrate --noinput
sudo -u creatorhub env DJANGO_ENV_FILE=/etc/creatorhub/creatorhub.env /srv/creatorhub/app/.venv/bin/python /srv/creatorhub/app/manage.py collectstatic --noinput
```

Resolve every deployment-check warning that applies to your configuration before continuing. The Django warnings `security.W005` and `security.W021` are expected with the included shared-VPS defaults: HSTS subdomain coverage and browser preload intentionally stay disabled to avoid imposing a policy on sibling site hostnames. Do not enable them without confirming every covered hostname is HTTPS-ready. Migrations affect only `creatorhub_prod`; they do not touch databases used by your other sites. Create a platform administrator:

```bash
sudo -u creatorhub env DJANGO_ENV_FILE=/etc/creatorhub/creatorhub.env /srv/creatorhub/app/.venv/bin/python /srv/creatorhub/app/manage.py createsuperuser
```

Confirm `/var/lib/creatorhub/private` is writable by `creatorhub` and remains outside Nginx's document roots. Keep its filesystem persistent and included in backups.

Prepare the password file used by PostgreSQL tools for scheduled backups. Use the database password set above, escaping `:` and `\\` with a backslash in the password field. Keep this file readable only by the app account:

```bash
sudo install -o creatorhub -g creatorhub -m 0600 /dev/null /var/lib/creatorhub/.pgpass
sudoedit /var/lib/creatorhub/.pgpass
```

Its line should be `127.0.0.1:5432:creatorhub_prod:creatorhub_app:YOUR_DATABASE_PASSWORD`; replace host, port, database, role, and password with your actual values. The backup script reads connection settings from the protected environment file and the password from this file.

## 5. Start only the CreatorHub systemd service

Install the dedicated unit and review its paths/port before starting it:

```bash
sudo install -o root -g root -m 0644 /srv/creatorhub/app/deploy/systemd/creatorhub.service.example /etc/systemd/system/creatorhub.service
sudo systemctl daemon-reload
sudo systemctl enable --now creatorhub
sudo systemctl status creatorhub --no-pager
sudo journalctl -u creatorhub -n 100 --no-pager
```

Verify the app is bound only to loopback and that its database-backed health endpoint responds:

```bash
sudo ss -ltnp | grep ':8017'
curl -fsS -H 'Host: creatorhub.example.com' http://127.0.0.1:8017/healthz/
```

The health response should be `ok`. If not, inspect only `journalctl -u creatorhub`; don't restart PostgreSQL, Nginx, or any existing site's service to troubleshoot CreatorHub.

## 6. Add Nginx configuration without replacing existing sites

First inspect `sudo nginx -T` to see whether `/etc/nginx/conf.d/*.conf` is included from inside the main `http {}` block. If it is, install the rate-limit zones as a new independent file:

```bash
sudo install -o root -g root -m 0644 /srv/creatorhub/app/deploy/nginx/creatorhub-rate-zones.conf.example /etc/nginx/conf.d/creatorhub-rate-zones.conf
```

If your Nginx layout does not include that directory, add one include for this zones file inside the existing `http {}` block after backing up the config. Do not replace the block or edit another site's server configuration. These zones define limits but affect no requests until CreatorHub's own vhost references them.

Install the proxy parameter snippet:

```bash
sudo install -d -o root -g root -m 0755 /etc/nginx/snippets
sudo install -o root -g root -m 0644 /srv/creatorhub/app/deploy/nginx/creatorhub-proxy-params.conf.example /etc/nginx/snippets/creatorhub-proxy-params.conf
```

For the first certificate, copy `deploy/nginx/creatorhub-acme.conf.example` into the server's site-specific include directory, replace only its example hostname, and enable it under a unique CreatorHub filename. Debian/Ubuntu commonly use `sites-available` plus a `sites-enabled` symlink; other distributions may include files from `conf.d` directly. Never reuse an existing site's config filename or symlink.

Test the complete Nginx configuration before reloading:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

If `nginx -t` fails, do not reload. Remove or correct only the new CreatorHub files, verify `nginx -t` passes again, and leave existing site configs untouched. The sample includes IPv6 listeners: remove the `[::]` lines and do not publish an AAAA record if the VPS has no configured IPv6 listener. A successful Nginx reload starts new workers with the validated config and gracefully drains old workers. ([Nginx reload behavior](https://nginx.org/en/docs/control.html), [Nginx rate limiting](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html))

## 7. Obtain TLS and enable the final CreatorHub vhost

After DNS resolves to this server and the temporary HTTP vhost is active, obtain a certificate with the webroot method. Use an email you control for certificate notices:

```bash
sudo install -d -o root -g root -m 0755 /var/lib/letsencrypt/.well-known/acme-challenge
sudo certbot certonly --webroot -w /var/lib/letsencrypt -d creatorhub.example.com --email you@example.com --agree-tos --non-interactive
```

Copy `deploy/nginx/creatorhub-https.conf.example` over the **same CreatorHub-only site file**, replace its hostname, and verify the certificate paths match Certbot's result. Keep the existing HTTP challenge location and redirect in that vhost. Then:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Confirm automatic renewal is enabled using your distribution's Certbot timer, and run `sudo certbot renew --dry-run`. Don't add a global TLS redirect or change any other site's certificates.

## 8. Verify CreatorHub and leave other sites alone

Check HTTPS, redirects, signup email delivery, static CSS, a creator upload/download, and `/healthz/`. A local pre-DNS/TLS test can use `curl --resolve creatorhub.example.com:443:127.0.0.1 https://creatorhub.example.com/` after the certificate and vhost are active. Confirm the upload limit is 25 MB and that no route serves `/var/lib/creatorhub/private` directly.

Check the other site's hostnames and health checks too. No firewall change is needed for Gunicorn: it remains on loopback, and Nginx uses the already-open 80/443 listeners with a distinct `server_name`.

## Updating the app

Before an update, back up the CreatorHub database and private files. Install code/dependency changes into the CreatorHub app directory, run `check --deploy`, apply backward-compatible migrations, and collect static files. Then reload only the CreatorHub service:

```bash
sudo systemctl reload creatorhub
sudo systemctl status creatorhub --no-pager
curl -fsS -H 'Host: creatorhub.example.com' http://127.0.0.1:8017/healthz/
```

Gunicorn's HUP reload starts new workers and drains old workers gracefully; this avoids restarting Nginx for ordinary application releases. ([Gunicorn signal handling](https://docs.gunicorn.org/en/stable/signals.html))

## Backups and rollback

The repository includes an optional daily backup timer. It creates a private, checksummed PostgreSQL custom dump and archive of private uploads under `/var/backups/creatorhub`; it does not delete older backups. Install it after confirming the app's `.pgpass` file works and creating a protected backup directory:

```bash
sudo install -d -o creatorhub -g creatorhub -m 0700 /var/backups/creatorhub
sudo install -o root -g root -m 0644 /srv/creatorhub/app/deploy/systemd/creatorhub-backup.service.example /etc/systemd/system/creatorhub-backup.service
sudo install -o root -g root -m 0644 /srv/creatorhub/app/deploy/systemd/creatorhub-backup.timer.example /etc/systemd/system/creatorhub-backup.timer
sudo systemctl daemon-reload
sudo systemctl enable --now creatorhub-backup.timer
sudo systemctl start creatorhub-backup.service
sudo systemctl status creatorhub-backup.service --no-pager
sudo journalctl -u creatorhub-backup.service -n 50 --no-pager
```

Verify the timestamped directory contains `database.dump`, `private-files.tar.gz`, and `SHA256SUMS`; run `sha256sum -c SHA256SUMS` from inside that directory. A backup stored only on the same VPS will not protect against disk loss or VPS compromise: copy backups to a separate, access-controlled location and encrypt them in transit and at rest. Test restore into a separate database/path before relying on backups. Never put database passwords on the command line.

If an application release fails, restore the previous CreatorHub code release and reload/restart only `creatorhub`. If the hostname's Nginx config fails, `nginx -t` prevents a bad config from being reloaded; restore only the saved CreatorHub vhost file, re-test, and reload Nginx. Never restore an old copy of the entire `/etc/nginx` tree over current files while other sites are live. Keep the new database and file backup until the rollback is confirmed; do not delete or reverse migrations blindly.

Useful app-only diagnostics:

```bash
sudo systemctl status creatorhub --no-pager
sudo journalctl -u creatorhub -f
curl -i -H 'Host: creatorhub.example.com' http://127.0.0.1:8017/healthz/
```

## Values to customize before deployment

Replace `creatorhub.example.com`, `you@example.com`, the PostgreSQL credentials, SMTP values, certificate paths if nonstandard, filesystem paths, and port if `8017` is in use. Choose the Gunicorn worker count for available memory; the example starts with two workers to keep this app modest on a shared VPS.
