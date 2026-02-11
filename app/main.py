import logging
import asyncio

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from .database import AsyncSessionLocal, engine, Base


# ---------------------------
# Logger
# ---------------------------
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(title="FastAPI + MySQL + OpenTelemetry demo")


# ---------------------------
# Routes
# ---------------------------
@app.get("/")
async def root():
    logger.info("Root endpoint hit")
    return {"message": "API running"}


@app.post("/items/")
async def create_item():
    logger.info("Create item request received")
    await asyncio.sleep(1)
    return {"status": "created"}


# ---------------------------
# Startup: wait for DB
# ---------------------------
@app.on_event("startup")
async def startup():
    logger.info("Starting API...")

    max_attempts = 30

    for attempt in range(max_attempts):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database ready")
            return

        except OperationalError:
            logger.warning("DB not ready, retrying...")
            await asyncio.sleep(3)

    logger.error("Database failed to start")
