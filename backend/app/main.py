import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models import init_db
from app.demo.seed_data import seed_standard_data
from app.services.followup_worker import FollowupWorker
from app.api.routes_scan import router as scan_router
from app.api.routes_payments import router as payments_router
from app.api.routes_cases import router as cases_router
from app.api.routes_pulse import router as pulse_router
from app.api.routes_chat import router as chat_router
from app.api.routes_demo import router as demo_router
from app.api.routes_webhooks import router as webhooks_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("raah")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database tables and seed initial demo data
    logger.info("Initializing RAAH Database and models...")
    init_db()
    try:
        seed_standard_data()
        logger.info("Standard demo seed data populated successfully.")
    except Exception as e:
        logger.warning(f"Seed note: {e}")

    # Start autonomous background follow-up worker
    worker_task = asyncio.create_task(FollowupWorker.start(interval_seconds=settings.BACKGROUND_WORKER_INTERVAL_SECONDS))
    logger.info("FollowupWorker background loop activated.")

    yield

    # Shutdown
    FollowupWorker.stop()
    worker_task.cancel()
    logger.info("RAAH Backend shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Payment Intelligence & Recovery for Paytm — Hackathon Prototype",
    lifespan=lifespan
)

# Enable CORS for React Native mobile app & local inspection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(scan_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(pulse_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(webhooks_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
