"""CloudScope Pulse: an intentionally small, observable, stateless workload."""
import json
import logging
import os
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

START = time.monotonic()
APP_NAME = "CloudScope Pulse"
REQUESTS = Counter("cloudscope_http_requests_total", "HTTP requests", ["method", "status"])
LATENCY = Histogram("cloudscope_http_request_duration_seconds", "Request duration in seconds")


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("cloudscope")
logger.handlers = [handler]
logger.setLevel(logging.INFO)
logger.propagate = False

app = FastAPI(title=APP_NAME, version="1.0.0", docs_url="/docs", redoc_url=None)


@app.middleware("http")
async def observability(request: Request, call_next):
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        REQUESTS.labels(request.method, "500").inc()
        logger.exception("request_failed")
        raise
    finally:
        LATENCY.observe(time.monotonic() - start)
    REQUESTS.labels(request.method, str(response.status_code)).inc()
    logger.info(f"request_completed method={request.method} status={response.status_code}")
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/", include_in_schema=False)
async def homepage():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    # Add explicit dependency probes here when the service gains dependencies.
    return {"status": "ready"}


@app.get("/api/v1/status")
async def status():
    return {
        "service": APP_NAME,
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.monotonic() - START, 1),
        "environment": os.getenv("APP_ENV", "local"),
        "version": os.getenv("APP_VERSION", "dev"),
        "revision": os.getenv("GIT_SHA", "unknown")[:12],
        "pod_name": os.getenv("POD_NAME", socket.gethostname()),
        "region": os.getenv("AWS_REGION", "local"),
    }


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(404)
async def custom_404(request: Request, exc):
    return JSONResponse({"error": "not_found"}, status_code=404)
