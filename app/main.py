import os
import logging
import asyncio

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError

# ---------------------------
# OpenTelemetry imports
# ---------------------------
from opentelemetry import trace
from opentelemetry._logs import get_logger, set_logger_provider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry._logs import SeverityNumber



from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# ---------------------------
# Database imports
# ---------------------------
from .database import AsyncSessionLocal, engine, Base
from . import crud, schema, models


# =====================================================
# Standard Python logger
# =====================================================
logger = logging.getLogger("app")#set up the log and name it app 
logger.setLevel(logging.INFO)#Log only info and above things 
handler = logging.StreamHandler()#Create the output destination here it is console 
logger.addHandler(handler)#Attach the destination to our logger

# =====================================================
# OpenTelemetry Resource
# =====================================================
service_name = os.getenv("OTEL_SERVICE_NAME", "fastapi-otel-app")#get the environment variable 
resource = Resource.create({"service.name": service_name})#Create a metadata describing the service and attach metadata to every span and log

# =====================================================
# Tracing setup
# =====================================================
trace_provider = TracerProvider(resource=resource)#Create a central tracing system . it manages everything like span and all 
trace.set_tracer_provider(trace_provider)#register this to get use it as central tracer 

OTEL_HOST = os.getenv("OTEL_COLLECTOR_HOST", "otel-collector")#where to send the tracing send the environment variables of that 
OTEL_PORT = os.getenv("OTEL_COLLECTOR_PORT", "4317")
OTLP_ENDPOINT = f"{OTEL_HOST}:{OTEL_PORT}"#The endpoint for the tracing and also the destination 

span_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)#It sends log to the otel
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))#Send the logs in batches 

tracer = trace.get_tracer(__name__)#create a tracer/span

# =====================================================
# Logging setup (OpenTelemetry logs)
# =====================================================
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

log_exporter = OTLPLogExporter(endpoint=OTLP_ENDPOINT, insecure=True)
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(log_exporter)
)

# OTel structured logger
otel_logger = get_logger(__name__)

# Bridge Python logging → OTel logs
LoggingInstrumentor().instrument(
    set_logging_format=True,
    log_level=logging.INFO
)

# =====================================================
# FastAPI app
# =====================================================
app = FastAPI(title="FastAPI + MySQL + OpenTelemetry demo")

# auto HTTP tracing
FastAPIInstrumentor().instrument_app(app)

# =====================================================
# DB dependency
# =====================================================
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# =====================================================
# Routes
# =====================================================
@app.get("/")
async def root():
    logger.info("Root endpoint hit")

    otel_logger.emit(
        severity_number=SeverityNumber.INFO,
        severity_text="INFO",
        body="Root endpoint accessed"
    )

    return {"message": "API running"}


@app.post("/items/")
async def create_item():
    logger.info("Create item request received")

    otel_logger.emit(
        severity_number=SeverityNumber.INFO,
        severity_text="INFO",
        body="Item creation started"
    )

    await asyncio.sleep(1)

    otel_logger.emit(
        severity_number=SeverityNumber.INFO,
        severity_text="INFO",
        body="Item created successfully"
    )

    return {"status": "created"}


# =====================================================
# Startup: wait for DB + create tables
# =====================================================
@app.on_event("startup")
async def startup():
    logger.info("Starting API...")

    otel_logger.emit(
        severity_number=SeverityNumber.INFO,
        severity_text="INFO",
        body="Startup event triggered"
    )

    max_attempts = 30

    for attempt in range(max_attempts):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database ready")
            otel_logger.emit(
                severity_number=SeverityNumber.INFO,
                severity_text="INFO",
                body="Database connection established"
            )
            return

        except OperationalError:
            logger.warning("DB not ready, retrying...")
            await asyncio.sleep(3)

    logger.error("Database failed to start")
    otel_logger.emit(
        severity_number=SeverityNumber.ERROR,
        severity_text="ERROR",
        body="Database startup failed"
    )
