# dockerfile
FROM python:3.12-slim

# Buenas prácticas de Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema (mínimas para SQLite + build de paquetes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos requirements primero → aprovecha cache de capas
COPY requirements/ requirements/

# ENV permite reutilizar el mismo Dockerfile para local/prod
ARG ENV=local
RUN pip install --upgrade pip && \
    pip install -r requirements/${ENV}.txt

# Copiamos el resto del proyecto
COPY . .

# Ejecutamos las migraciones durante la construcción para que se cree la base de datos SQLite con las tablas


# Usuario no root por seguridad
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:10000 config.wsgi:application"]
