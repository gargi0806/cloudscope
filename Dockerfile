FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock && useradd --create-home --uid 10001 scanner
COPY cloudscope ./cloudscope
RUN mkdir /reports && chown scanner:scanner /reports
USER scanner
ENTRYPOINT ["python", "-m", "cloudscope"]
CMD ["demo", "--out", "/reports"]
