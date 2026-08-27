FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy pydantic-settings passlib[bcrypt] python-jose[cryptography] python-multipart networkx shapely psycopg[binary] redis celery
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
