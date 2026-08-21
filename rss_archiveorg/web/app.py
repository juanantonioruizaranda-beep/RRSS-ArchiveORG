"""FastAPI application and SSE streaming for the landing page."""

from __future__ import annotations

import asyncio
import json
import queue
import re
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from rss_archiveorg.extractor import SOCIAL_NETWORKS
from rss_archiveorg.io import parse_sites_text, results_to_csv_text, results_to_json_text
from rss_archiveorg.pipeline import BatchCancelled, run_sites_batch
from rss_archiveorg.proxy import resolve_proxies_for_run

MIN_DELAY_SECONDS = 3.0
DEFAULT_DELAY_SECONDS = 5.0
MAX_URLS = 200
DEFAULT_PROXIES_PATH = Path("proxies.txt")
TIMESTAMP_PATTERN = re.compile(r"^\d{8}(\d{6})?$")
ROBOTS_HEADER_VALUE = "noindex, nofollow"
PRIMARY_SOCIAL_FILTERS = [
    {"id": "twitter", "label": "Twitter / X"},
    {"id": "instagram", "label": "Instagram"},
    {"id": "youtube", "label": "YouTube"},
    {"id": "facebook", "label": "Facebook"},
    {"id": "tiktok", "label": "TikTok"},
]


class RobotsTagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Robots-Tag"] = ROBOTS_HEADER_VALUE
        return response


app = FastAPI(title="RSS-ArchiveORG", version="0.3.0")
app.add_middleware(RobotsTagMiddleware)
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ExtractRequest(BaseModel):
    urls_text: str = Field(..., min_length=1)
    delay: float = Field(default=DEFAULT_DELAY_SECONDS, ge=MIN_DELAY_SECONDS, le=120.0)
    use_proxies: bool = False
    proxies_text: str | None = None
    timestamp: str | None = None

    @field_validator("urls_text")
    @classmethod
    def validate_urls(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Añade al menos una URL")
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if not TIMESTAMP_PATTERN.fullmatch(cleaned):
            raise ValueError("El timestamp debe tener formato YYYYMMDD o YYYYMMDDhhmmss")
        return cleaned


class ExportRequest(BaseModel):
    results: list[dict]
    format: str = Field(pattern="^(json|csv)$")


def _resolve_proxies(use_proxies: bool, proxies_text: str | None) -> list | None:
    try:
        return resolve_proxies_for_run(
            enabled=use_proxies,
            proxies_text=proxies_text,
            fallback_path=DEFAULT_PROXIES_PATH,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _parse_request_urls(urls_text: str) -> list[str]:
    try:
        sites = parse_sites_text(urls_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not sites:
        raise HTTPException(status_code=400, detail="Añade al menos una URL válida")
    if len(sites) > MAX_URLS:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo {MAX_URLS} URLs por petición (recibidas: {len(sites)})",
        )
    return sites


@app.get("/", response_class=HTMLResponse)
def landing_page() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(
        index_path.read_text(encoding="utf-8"),
        headers={"X-Robots-Tag": ROBOTS_HEADER_VALUE},
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt() -> PlainTextResponse:
    return PlainTextResponse(
        "User-agent: *\nDisallow: /\n",
        headers={"X-Robots-Tag": ROBOTS_HEADER_VALUE},
    )


@app.get("/api/config")
def api_config() -> dict:
    return {
        "min_delay": MIN_DELAY_SECONDS,
        "default_delay": DEFAULT_DELAY_SECONDS,
        "max_urls": MAX_URLS,
        "proxies_file_available": DEFAULT_PROXIES_PATH.exists(),
        "proxy_format": "host:port:user:pass",
        "social_networks": sorted(SOCIAL_NETWORKS.keys()),
        "primary_social_filters": PRIMARY_SOCIAL_FILTERS,
    }


@app.post("/api/export")
def export_results(request: ExportRequest) -> Response:
    if not request.results:
        raise HTTPException(status_code=400, detail="No hay resultados para exportar")

    if request.format == "json":
        content = results_to_json_text(request.results)
        media_type = "application/json"
        filename = "rss-archiveorg-results.json"
    else:
        content = results_to_csv_text(request.results)
        media_type = "text/csv; charset=utf-8"
        filename = "rss-archiveorg-results.csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/extract")
async def extract_stream(http_request: Request, request: ExtractRequest) -> StreamingResponse:
    sites = _parse_request_urls(request.urls_text)
    proxies = _resolve_proxies(request.use_proxies, request.proxies_text)
    event_queue: queue.Queue[str | None] = queue.Queue()
    cancel_event = threading.Event()

    def worker() -> None:
        processed = 0

        def on_result(result, index: int, total: int) -> None:
            nonlocal processed
            processed = index
            payload = result.to_web_dict(index=index, total=total)
            event_queue.put(json.dumps(payload, ensure_ascii=False))

        try:
            run_sites_batch(
                sites,
                delay=request.delay,
                proxies=proxies,
                timestamp=request.timestamp,
                should_cancel=cancel_event.is_set,
                on_result=on_result,
            )
            if cancel_event.is_set():
                event_queue.put(
                    json.dumps(
                        {
                            "type": "cancelled",
                            "processed": processed,
                            "total": len(sites),
                            "message": "Proceso cancelado",
                        },
                        ensure_ascii=False,
                    )
                )
            else:
                event_queue.put(
                    json.dumps(
                        {
                            "type": "done",
                            "total": len(sites),
                            "message": "Proceso completado",
                        },
                        ensure_ascii=False,
                    )
                )
        except BatchCancelled:
            event_queue.put(
                json.dumps(
                    {
                        "type": "cancelled",
                        "processed": processed,
                        "total": len(sites),
                        "message": "Proceso cancelado",
                    },
                    ensure_ascii=False,
                )
            )
        except Exception as exc:  # noqa: BLE001 - surface job failures to the UI
            event_queue.put(
                json.dumps(
                    {
                        "type": "fatal",
                        "message": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
        finally:
            event_queue.put(None)

    threading.Thread(target=worker, daemon=True).start()

    async def event_generator():
        while True:
            if await http_request.is_disconnected():
                cancel_event.set()
            try:
                item = await asyncio.to_thread(event_queue.get, True, 0.25)
            except queue.Empty:
                continue
            if item is None:
                break
            yield f"data: {item}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
