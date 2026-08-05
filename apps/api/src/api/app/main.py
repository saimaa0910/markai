"""
Application Factory & Lifespan Hooks.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown event handling.
    """
    # TODO: Perform database connection pool initialization and cache handshakes
    yield
    # TODO: Perform clean shutdown and connection pool disposal


def create_app() -> FastAPI:
    """
    Application factory helper.
    """
    app = FastAPI(
        title="EAIMOS Enterprise API",
        version="1.0.0",
        lifespan=lifespan,
    )
    return app
