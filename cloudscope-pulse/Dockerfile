FROM python:3.12-alpine3.24
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apk upgrade --no-cache \
    && addgroup -S -g 10001 app \
    && adduser -S -u 10001 -G app -H app
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt
COPY --chown=10001:10001 app/ /app/
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/health/live', timeout=2)"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
