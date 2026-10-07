# Build stage: deps, sample database and static files are baked into the image.
FROM python:3.13-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=1 PATH=/code/.venv/bin:$PATH
WORKDIR /code
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction && rm -rf /root/.cache
COPY . .
RUN python manage.py migrate --noinput \
 && python manage.py loaddata formula/fixtures/* \
 && python manage.py shell -c "from django.contrib.auth import authenticate; authenticate(username='demo', password='demo')" \
 && python manage.py collectstatic --noinput

# Runtime stage: no poetry, no git.
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PATH=/code/.venv/bin:$PATH
WORKDIR /code
COPY --from=build /code /code
EXPOSE 8000
CMD ["gunicorn", "--bind", ":8000", "--workers", "1", "--threads", "4", "formula.wsgi"]
