# AGENTS.md

Guidance for agents working in this repository — the live demo of
[`django-unfold-agentic-layer`](https://github.com/JargeZ/django-unfold-agentic-layer)
on top of the Unfold sample project “Formula”.

## What this repo is

A Django + Unfold admin that also serves an MCP Streamable HTTP endpoint at
`/mcp/`. Staff users (demo login `demo` / `unfold123` in production) connect Claude
Code, Cursor or any OAuth MCP client and get the same models, filters, actions
and permissions the admin already exposes.

| | |
|---|---|
| Admin UI | `/admin/` |
| MCP endpoint | `/mcp/` |
| Package | `django_unfold_agentic_layer` in `INSTALLED_APPS` + `urls` include |

Production demo: <https://django-formula-admin-agentic.fly.dev/admin/> —
MCP at `/mcp/`, login `demo` / `unfold123`. Upstream package docs:
<https://github.com/JargeZ/django-unfold-agentic-layer#readme>.

## Layout

- `formula/` — Django project (settings, URLs, admin templates, F1 models)
- `demo/` — commerce/CRM demo app, dashboard views and templates
- `utils/` — shared admin/chart helpers
- Database is **read-only** in the deployed demo (writes validate then fail with
  `ReadonlyException`). OAuth clients/tokens use a writable sqlite copy
  (`agentic_layer` DB + router in `formula/routers.py`).

## Local development

```bash
# .env with DEBUG=1 and a long SECRET_KEY
docker compose up
docker compose exec web python manage.py seed   # login demo / unfold123 (or LOGIN_PASSWORD)
npm install && npm run tailwind:watch           # if you change template classes
```

MCP OAuth behind TLS needs the request to look secure (`SECURE_PROXY_SSL_HEADER`
is set for Fly). Do not invent a separate auth path — consent goes through the
admin login.

## Admin: MCP clients and tokens

Registered under app **Django Unfold Agentic Layer**:

- **MCP clients** — `admin:django_unfold_agentic_layer_oauthclient_changelist` —
  clients that asked staff to log in (Claude Code, Cursor, …). Delete = revoke
  all of that client’s tokens.
- **MCP access tokens** — `admin:django_unfold_agentic_layer_oauthtoken_changelist` —
  one row per approved login (user, client, scopes, expiry). Delete = revoke
  that session.

## Connect an agent (Claude Code)

```bash
claude mcp add --transport http unfold-mcp-demo "<origin>/mcp/"
```

Then `/mcp` → **Authenticate** → sign in as staff and allow access.
