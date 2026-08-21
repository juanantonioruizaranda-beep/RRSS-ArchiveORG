"""FastAPI application and SSE streaming for the landing page."""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from rss_archiveorg.io import parse_sites_text
from rss_archiveorg.pipeline import run_sites_batch

MIN_DELAY_SECONDS = 3.0
DEFAULT_DELAY_SECONDS = 5.0
MAX_URLS = 200
DEFAULT_PROXIES_PATH = Path("proxies.txt")

app = FastAPI(title="RSS-ArchiveORG", version="0.2.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ExtractRequest(BaseModel):
    urls_text: str = Field(..., min_length=1)
    delay: float = Field(default=DEFAULT_DELAY_SECONDS, ge=MIN_DELAY_SECONDS, le=120.0)
    use_proxies: bool = False

    @field_validator("urls_text")
    @classmethod
    def validate_urls(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Añade al menos una URL")
        return value


def _resolve_proxies_path(use_proxies: bool) -> Path | None:
    if not use_proxies:
        return None
    if not DEFAULT_PROXIES_PATH.exists():
        raise HTTPException(
            status_code=400,
            detail=(
                "Se activaron los proxys pero no existe proxies.txt en la raíz del proyecto. "
                "Copia proxies.example.txt y configura tus proxys."
            ),
        )
    return DEFAULT_PROXIES_PATH


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
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/api/config")
def api_config() -> dict:
    return {
        "min_delay": MIN_DELAY_SECONDS,
        "default_delay": DEFAULT_DELAY_SECONDS,
        "max_urls": MAX_URLS,
        "proxies_available": DEFAULT_PROXIES_PATH.exists(),
    }


@app.post("/api/extract")
async def extract_stream(request: ExtractRequest) -> StreamingResponse:
    sites = _parse_request_urls(request.urls_text)
    proxies_path = _resolve_proxies_path(request.use_proxies)
    event_queue: queue.Queue[str | None] = queue.Queue()

    def worker() -> None:
        def on_result(result, index: int, total: int) -> None:
            payload = result.to_web_dict(index=index, total=total)
            event_queue.put(json.dumps(payload, ensure_ascii=False))

        try:
            run_sites_batch(
                sites,
                delay=request.delay,
                proxies_path=proxies_path,
                on_result=on_result,
            )
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
            item = await asyncio.to_thread(event_queue.get)
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
