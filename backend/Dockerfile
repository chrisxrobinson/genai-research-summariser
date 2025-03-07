FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy only dependency files to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root --without dev

# Copy application code
COPY . .

# For development, install all dependencies including dev
RUN if [ -f poetry.lock ]; then \
      poetry install --no-interaction; \
    else \
      poetry install --no-interaction; \
    fi

EXPOSE 8000

# Use a script for flexible startup options
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
