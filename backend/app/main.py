import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.config import settings
from app.infra.cleanup import sweep_expired_jobs

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok"}


async def _run_sweep_loop() -> None:
    """Periodically run the expired-job cleanup sweep."""
    while True:
        try:
            count = sweep_expired_jobs()
            if count:
                logger.info("Sweep: marked %d expired job(s)", count)
        except Exception:
            logger.exception("Sweep iteration failed")
        await asyncio.sleep(settings.sweep_interval_minutes * 60)


@app.on_event("startup")
async def startup() -> None:
    """Register the background sweep loop on application start."""
    asyncio.create_task(_run_sweep_loop())
    logger.info(
        "Sweep scheduler registered (interval=%d min)",
        settings.sweep_interval_minutes,
    )
