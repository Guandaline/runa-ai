FROM python:3.12-slim AS builder

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry

COPY poetry.lock pyproject.toml ./

COPY plugins/ ./plugins

RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-interaction --no-ansi --no-root

COPY src/ ./src
COPY settings/ ./settings


FROM python:3.12-slim

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && adduser --system --group app

WORKDIR /app

ENV PYTHONPATH=/app/src

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

COPY --from=builder --chown=root:app --chmod=0550 /app/src ./src

COPY --from=builder --chown=root:app --chmod=0550 /app/plugins ./plugins

RUN mkdir -p /app/var /app/tmp \
    && chown -R app:app /app/var /app/tmp \
    && chmod 0750 /app/var /app/tmp

USER app

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "nala.main:app"]
