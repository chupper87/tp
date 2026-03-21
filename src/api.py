import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from starlette_context.middleware.raw_middleware import RawContextMiddleware
from starlette_context.plugins.correlation_id import CorrelationIdPlugin
from structlog.contextvars import bind_contextvars, clear_contextvars

import employees
import idp
from api_core import GenericAPIResponse, __api_exception_handlers
from config import config
from log_setup import get_logger

log = get_logger(__name__)

routers = [
    idp.router,
    employees.router,
]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    log.info("Starting tp API")
    yield
    log.info("Shutting down tp API")


app = FastAPI(lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class _BindCorrelationIdPlugin(CorrelationIdPlugin):
    async def process_request(self, *args, **kwargs) -> Optional[str]:
        value = await super().process_request(*args, **kwargs)
        clear_contextvars()
        bind_contextvars(correlation_id=value)
        return value


app.add_middleware(
    RawContextMiddleware,
    plugins=(_BindCorrelationIdPlugin(validate=False),),
)


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}"

    log.debug(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        response_time=f"{duration:.3f}",
    )
    return response


@app.get("/ping", tags=["Health"], include_in_schema=True)
async def ping():
    return GenericAPIResponse(detail="Pong!")


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse("/docs")


for router in routers:
    app.include_router(router)

for exception, (api_error_class, status_code) in __api_exception_handlers.items():

    async def handler(request: Request, exc: Exception) -> Response:
        _ = request
        _class, _code = __api_exception_handlers[type(exc)]
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=_code,
            content=_class.from_original_error(exc).model_dump(mode="json"),
        )

    app.exception_handler(exception)(handler)
