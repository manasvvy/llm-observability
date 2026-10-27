from __future__ import annotations

import time
from typing import Any

from fastapi import Request
from starlette.responses import Response


async def logging_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started_at) * 1000)
    request_id = request.headers.get("x-request-id", "n/a")
    print(f"[{request_id}] {request.method} {request.url.path} {elapsed_ms}ms")
    return response
