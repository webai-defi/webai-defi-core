FROM python:3.11.7-slim as poetry-dependencies

WORKDIR /tmp
RUN apt-get -y update && apt-get -y upgrade && pip install poetry && rm -rf /var/lib/apt/lists/*
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry self update
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --output requirements.txt

FROM python:3.11.7-slim

WORKDIR /app

COPY --from=poetry-dependencies /tmp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]