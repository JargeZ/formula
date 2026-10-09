# Build stage: deps, sample database and static files are baked into the image.
FROM python:3.13-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=1 PATH=/code/.venv/bin:$PATH
WORKDIR /code
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction \
 && rm -rf /root/.cache .venv/lib/python3.13/site-packages/pip* .venv/bin/pip*
COPY . .
RUN python manage.py migrate --noinput \
 && LOGIN_PASSWORD=demo python manage.py seed \
 && python manage.py shell -c "from django.contrib.auth import authenticate; authenticate(username='demo', password='demo')" \
 && python manage.py collectstatic --noinput \
 && python -m compileall -q formula demo utils

# Runtime stage: no poetry, no git.
FROM python:3.13-slim
# Bytecode is precompiled: do not write .pyc into the machine rootfs layer.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH=/code/.venv/bin:$PATH
WORKDIR /code
COPY --from=build /code /code
EXPOSE 8000
CMD ["gunicorn", "--bind", ":8000", "--workers", "1", "--threads", "2", "formula.wsgi"]
