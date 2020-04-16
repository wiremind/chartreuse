# Only used for e2e tests. Do not use in production.

FROM python:3.7

WORKDIR /app

COPY requirements.txt requirements.txt
ARG PYPI_PASSWORD_READONLY
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://readonly:$PYPI_PASSWORD_READONLY@pypi.wiremind.fr

COPY . .
RUN pip install -e .
COPY src/chartreuse/tests/e2e_tests/sample_alembic alembic
COPY src/chartreuse/tests/e2e_tests/sample_eslembic eslembic
