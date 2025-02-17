FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
