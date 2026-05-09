from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from composition import AppContext, build_app_context
from presentation.http.routes import build_router


def create_app(
    app_context: AppContext | None = None,
    app_context_factory: Callable[[], AppContext] = build_app_context,
) -> FastAPI:
    load_dotenv(override=False)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        context = app_context or app_context_factory()
        app.state.app_context = context
        try:
            yield
        finally:
            context.close()

    app = FastAPI(title="Pet Log Backend", version="0.1.0", lifespan=lifespan)
    app.include_router(build_router())
    return app
