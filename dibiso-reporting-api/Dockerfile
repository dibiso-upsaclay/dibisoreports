FROM python:3.12-slim-bookworm

# ── WeasyPrint system dependencies ───────────────────────────────────────────
# libpango-1.0-0 pulls in Cairo, GDK-Pixbuf and GLib transitively — all that
# WeasyPrint needs to produce PDFs on Linux.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        fonts-open-sans \
        fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# ── Python dependencies ───────────────────────────────────────────────────────
# Build context is the project root (set in docker-compose.yml), so we can reach
# the local library sources.
COPY dibiso-reporting-api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install dibisoreporting and dibisoplot from local source.
# The PyPI versions are outdated and lack HTML-template support.
COPY dibisoreporting/ /build/dibisoreporting/
COPY dibisoplot/ /build/dibisoplot/
RUN pip install --no-cache-dir /build/dibisoplot/ /build/dibisoreporting/

# ── Application ───────────────────────────────────────────────────────────────
RUN mkdir -p /api_data

COPY dibiso-reporting-api/app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
