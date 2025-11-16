# =================================================================
# PRESSO BACKEND - Dockerfile
# =================================================================
# Multi-stage build pour optimiser la taille de l'image
# =================================================================

FROM python:3.12-slim as builder

# Variables d'environnement Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système pour GeoDjango
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialite-dev \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =================================================================
# Stage final
# =================================================================
FROM python:3.12-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so.36 \
    GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so.1

# Installer uniquement les librairies runtime (pas de build tools)
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal36 \
    libgeos-c1t64 \
    libgeos3.13.1 \
    libproj25 \
    libspatialite8t64 \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/lib/x86_64-linux-gnu/libgdal.so.36 /usr/lib/x86_64-linux-gnu/libgdal.so.34 \
    && ln -s /usr/lib/x86_64-linux-gnu/libgdal.so.36.3.10.3 /usr/lib/x86_64-linux-gnu/libgdal.so.34.3.8.4 \
    && ln -s /usr/lib/x86_64-linux-gnu/libgeos_c.so.1 /usr/lib/x86_64-linux-gnu/libgeos_c.so

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 presso && \
    mkdir -p /app /app/media /app/staticfiles && \
    chown -R presso:presso /app

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances Python depuis le builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code de l'application
COPY --chown=presso:presso . .

# Passer à l'utilisateur non-root
USER presso

# Exposer le port
EXPOSE 8000

# Script d'entrée (sera créé dans docker-compose)
# Note: La commande réelle est dans docker-compose.yml (daphne pour WebSockets)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]

