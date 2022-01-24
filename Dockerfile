FROM python:3.9.10-slim as builder

RUN apt update && apt install -y git curl

ENV PATH=/root/.local/bin:$PATH

RUN curl -sSL https://install.python-poetry.org | python - \
    && poetry self update --preview \
    && poetry config virtualenvs.in-project true

WORKDIR /app

COPY . .

RUN poetry export -o requirements.txt && poetry build -f wheel

FROM python:3.9.10-slim as prod

COPY --from=builder /app/static /app/static
COPY --from=builder /app/templates /app/templates
COPY --from=builder /app/requirements.txt /app/requirements.txt
COPY --from=builder /app/dist/ /app/dist/

WORKDIR /app

RUN pip install -r requirements.txt && pip install wqw-app -f dist

CMD ["uvicorn", "wqw_app.app:app", "--reload"]
