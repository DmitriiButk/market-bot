FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "cd /app/djproject && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn djproject.wsgi:application --bind 0.0.0.0:8000"]
