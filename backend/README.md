# DermAI API setup

1. Create/activate a Python environment and install the backend dependencies with `pip install -r requirements.txt` from this directory.
2. Copy `backend/.env.example` to `backend/.env`, generate distinct secret keys, and configure the database and allowed origins. Never commit `backend/.env`.
3. Start PostgreSQL and apply the schema with `alembic -c alembic.ini upgrade head` from this directory.
4. For a new deployment, create the first administrator interactively with `python scripts/create_admin.py` from this directory. The script never uses a hard-coded credential and refuses to create another active admin.
5. Run the API with `uvicorn app.main:app --reload` from this directory. FastAPI docs are available at `/docs`.

The existing migration chain includes an unsafe legacy revision that can transform/drop patient data. Do not apply migrations until its data transformations, backup, and restore procedure have been reviewed and approved. The API no longer calls `create_all()` on startup; schema changes must be managed by explicit migrations.

## Authentication security configuration

- `APP_ENV=development` uses `CORS_DEVELOPMENT_ORIGINS` (default `http://localhost:5173`). `APP_ENV=staging` or `production` requires exact HTTPS values in `CORS_PRODUCTION_ORIGINS`, such as `https://app.example.org` (no wildcard and no path). Credentialed CORS uses only these explicit origins.
- `SESSION_COOKIE_SECURE=true` is required in staging and production. Set the cookie SameSite, path, and optional domain for the actual hosting topology. Do not set a broad cookie domain without deployment/security review.
- Unsafe browser requests require an exact configured `Origin`; missing and untrusted origins are rejected. Referer is not used as a fallback. Non-browser clients that mutate data must use an explicitly supported client/authentication design; none is currently configured.
- Anonymous login/registration use a signed pre-auth CSRF token. After login, CSRF tokens are HMAC-bound to the opaque session cookie; they are not valid for another session. `/auth/csrf` bootstraps either flow.
- Auth rate limits are fixed-window counters stored in the shared `auth_rate_limit_buckets` PostgreSQL table. Defaults are 10 login attempts per normalized account, 100 per source IP, 20 registration requests per source IP, and 120 CSRF bootstrap requests per source IP per 900 seconds. Limits include successful login attempts and are configurable. Request source IP is the direct peer address; do not trust client-supplied forwarded headers. Configure trusted-proxy handling at the deployment edge before relying on per-IP limits behind a proxy.
- Production startup fails if secure session cookies or explicit HTTPS CORS origins are missing. Login and CSRF bootstrap return `429` with `Retry-After` when a limit is exceeded.

## PostgreSQL verification blocker

Phase 3 automated tests use isolated in-memory SQLite. PostgreSQL migration/rate-limit integration has not been run. The existing base migration is not safe to run against an existing database, and the session migration must remain unapplied until its database target and restore procedure are approved.

To establish a disposable PostgreSQL target for a later verification phase (do not point it at an existing project database):

1. Install Docker Desktop and start an isolated PostgreSQL container with no host volume, for example `docker run --name dermai-auth-pg-test -e POSTGRES_USER=dermai_test -e POSTGRES_PASSWORD=REPLACE_WITH_FRESH_RANDOM_PASSWORD -e POSTGRES_DB=dermai_auth_test -p 55432:5432 --tmpfs /var/lib/postgresql/data:rw,size=512m -d postgres:16`. Replace the password placeholder before running.
2. Confirm the container name, database name, and port are unique test values. Do not copy application `.env` credentials into this target.
3. Create a disposable test environment using `DB_HOST=127.0.0.1`, `DB_PORT=55432`, `DB_NAME=dermai_auth_test`, `DB_USER=dermai_test`, and the generated test password. Keep the normal `backend/.env` untouched.
4. Before testing a migration chain, prepare a reviewed schema baseline and verify a dump/restore entirely within disposable databases. The current unsafe base migration must be reviewed first; this Phase 3 work did not run it or apply any revision.
5. To exercise the PostgreSQL upsert without applying migrations, set `DERMAI_AUTH_TEST_POSTGRES_URL` to the loopback `dermai_auth_test` URL and `DERMAI_ALLOW_DISPOSABLE_POSTGRES_TEST=1`, then run `python -m pytest tests/test_auth_rate_limit_postgres.py -q` from `backend`. This opt-in test creates only the rate-limit table if absent, performs counter checks, removes its own test row, and drops that table if it created it. Stop the container with `docker rm -f dermai-auth-pg-test` when finished; the database uses ephemeral storage.
