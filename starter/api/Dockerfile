FROM python:3.12-slim

WORKDIR /app

# системные зависимости для WeasyPrint и pyswisseph
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# uv для быстрой установки
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY src ./src

RUN uv pip install --system -e ".[dev]"

EXPOSE 8000
CMD ["uvicorn", "vlad.main:app", "--host", "0.0.0.0", "--port", "8000"]
