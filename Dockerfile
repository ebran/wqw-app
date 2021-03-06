FROM python:3.9.10-slim as builder

RUN apt update && apt install -y git curl

ENV PATH=/root/.local/bin:$PATH

RUN curl -sSL https://install.python-poetry.org | python - \
    && poetry self update --preview \
    && poetry config virtualenvs.in-project true

WORKDIR /app

COPY . .

RUN poetry export -o requirements.txt && poetry build -f wheel

FROM python:3.9.10-slim as web

COPY --from=builder /app/static /web/static
COPY --from=builder /app/templates /web/templates
COPY --from=builder /app/requirements.txt /web/requirements.txt
COPY --from=builder /app/dist/ /web/dist/

WORKDIR /web

RUN pip install -r requirements.txt
RUN pip install wqw-app -f dist

CMD ["uvicorn", "wqw_app.app:app", "--reload", "--host", "0.0.0.0"]

FROM python:3.9.10-slim as worker

COPY --from=builder /app/requirements.txt /worker/requirements.txt
COPY --from=builder /app/dist/ /worker/dist/

WORKDIR /worker

RUN pip install -r requirements.txt
RUN pip install wqw-app -f dist

CMD ["arq", "wqw_app.worker.WorkerSettings"]
