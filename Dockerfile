FROM python:3.12-slim

ARG BUILD_SHA=unknown
ARG BUILD_DATE=unknown
ENV BUILD_SHA=${BUILD_SHA}
ENV BUILD_DATE=${BUILD_DATE}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY templates/ ./templates/

# Uploads, images, and DB are all mounted at runtime via the /data volume
ENV UPLOAD_DIR=/data/uploads
ENV IMAGES_DIR=/data/uploads/images
ENV DATABASE_URL=sqlite+aiosqlite:////data/nivpro.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
