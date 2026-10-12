# 한채 백엔드 이미지: Django + gunicorn
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# mysqlclient 를 빌드하려면 MySQL 클라이언트 라이브러리가 필요하다
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN DJANGO_SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput

EXPOSE 8000
# 컨테이너가 뜰 때마다 DB 를 최신 마이그레이션으로 맞춘 뒤 서버를 켠다
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile - --error-logfile -"]
