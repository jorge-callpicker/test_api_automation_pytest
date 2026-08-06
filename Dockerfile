# Contenedor de ejecución del framework de pruebas — alternativa a instalar
# Python 3.11+ localmente. Sin entorno virtual: el propio contenedor ya es
# el aislamiento, instalar en su Python de sistema es correcto aquí.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Se copian solo los archivos de dependencias primero para aprovechar la
# cache de capas de Docker; el resto del repo llega en runtime vía bind
# mount (ver README.md), pisando este contenido sin invalidar la capa.
COPY pyproject.toml ./
COPY src/ ./src/

RUN python -m pip install --upgrade pip \
    && pip install -e ".[dev]"

CMD ["bash"]
