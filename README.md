# Formula - Django Unfold Admin + MCP Demo <!-- omit from toc -->

**Project: <https://github.com/JargeZ/django-unfold-agentic-layer>**

A live demo of [django-unfold-agentic-layer](https://github.com/JargeZ/django-unfold-agentic-layer): it turns a regular [Unfold](https://github.com/unfoldadmin/django-unfold) Django admin into an MCP server, so an AI agent (Claude Code, Claude Desktop, any MCP client) can browse, filter and edit admin data the same way a human does in the admin UI.

The project is a fork of the Unfold sample project "Formula" with extra demo data: Formula 1 drivers, races and standings, a small shop (products, orders, customers, tickets), Waffle flags and Celery Beat periodic tasks.

- [Live demo](#live-demo)
- [Connect an agent over MCP](#connect-an-agent-over-mcp)
- [What the agent can do](#what-the-agent-can-do)
- [Limitations](#limitations)
- [Local development](#local-development)

## Live demo

| | |
|---|---|
| Admin UI | <https://django-formula-admin-agentic.fly.dev/admin/> |
| MCP endpoint | `https://django-formula-admin-agentic.fly.dev/mcp/` |
| Login | `demo` |
| Password | `demo` |

The login form is pre-filled with these credentials.

## Connect an agent over MCP

The MCP server uses the HTTP transport with OAuth: the agent opens the demo login page in the browser and you sign in with `demo` / `demo`.

### Claude Code

```bash
claude mcp add --transport http unfold-mcp-demo "https://django-formula-admin-agentic.fly.dev/mcp/"
```

Then authorize:

1. Start `claude` and run `/mcp`.
2. Select `unfold-mcp-demo` and choose **Authenticate**.
3. A browser window opens with the demo login page. Sign in with `demo` / `demo` and allow access.
4. Go back to Claude Code. The server shows as connected and its tools and resources are available.

Try a prompt like *"Using unfold-mcp-demo, list the races at Monza after 2020 and who won them"*.

### Other MCP clients

Any client that supports remote MCP servers over HTTP with OAuth works. Add the server URL `https://django-formula-admin-agentic.fly.dev/mcp/` and complete the same browser login with `demo` / `demo`.

## What the agent can do

- **Resources** (read): `dj-admin://<app>/<model>/` for every registered admin model, with search, filters, ordering and pagination taken from the `ModelAdmin` (`search_fields`, `list_filter`, `ordering`). For example `dj-admin://formula/race/?year_from=2021&limit=5` or one record via `dj-admin://formula/driver/27/`.
- **Tools** (write): `create_*`, `update_*` and `delete_*` per model, validated through the admin form, plus `run_*` for admin actions (for example resolve tickets, enable Waffle flags, run periodic tasks).
- **Docs tools**: `unfold_*` tools that return the Unfold documentation.

## Limitations

- **The database is read-only.** It is baked into the image and reset on every deploy. Reads work. Writes (`create_*`, `update_*`, `delete_*` and actions that save data) run form validation first, so you still get field errors, but a valid write fails with `ReadonlyException: Database is operating in readonly mode`. Nothing is saved.
- **The login session can expire.** OAuth tokens are kept on the machine and are lost when the app is redeployed or restarted. If the agent gets `Unauthorized`, run `/mcp` → `unfold-mcp-demo` → **Authenticate** again.
- **Cold start.** The machine suspends when idle, so the first request after a pause can take a few seconds.
- **Small machine.** The demo runs on one small instance. Many parallel requests at the same time can fail. Send fewer requests at once and retry.

## Local development

Create a `.env` file with `DEBUG=1` and a long random `SECRET_KEY`, then start the project:

```bash
git clone https://github.com/JargeZ/formula.git
cd formula
docker compose up
```

Fill the database with demo data. The `seed` command deletes all data, loads `formula/fixtures` and generates the `demo` app data, Constance, Waffle and Celery Beat. Login: `demo` / `unfold123` (or the value of `LOGIN_PASSWORD`).

```bash
docker compose exec web python manage.py seed
```

### Custom dashboard

The dashboard widgets are custom-made for this showcase and are not part of Unfold. They are in `formula/templates/admin/components/`, the layout is in `formula/templates/admin/index.html`.

### Compiling styles

Tailwind classes used in project templates are compiled into the stylesheet referenced by `UNFOLD["STYLES"]` in `settings.py`:

```bash
npm install
npm run tailwind:build  # one-time build
npm run tailwind:watch  # watch all files for changes
```
