# 1. Basis-Image: Python 3.11 slim
FROM python:3.11-slim

# 2. Arbeitsverzeichnis im Container
WORKDIR /app

# 3. Systemabhängigkeiten (für Pillow, PostgreSQL etc.)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev musl-dev \
    libjpeg-dev zlib1g-dev \
    ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 4. Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 5. Copy the rest of the code
COPY . .

# 6. Port freigeben
EXPOSE 8002
EXPOSE 8000

# 7. ENV-Variable zum Umschalten zwischen dev/prod
ENV ENV=development

# 8. Start je nach Umgebung (gunicorn für production, runserver für dev)
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
