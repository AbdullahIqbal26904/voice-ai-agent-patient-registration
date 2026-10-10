import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import async_session, engine
from app.models import Base
from app.routers import patients, vapi_webhook
from app.schemas import APIResponse
from app.seed import seed_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        await seed_database(db)
    logger.info("Application started")
    yield
    await engine.dispose()


app = FastAPI(
    title="CareCloud Patient Registration API",
    description="Voice AI Agent - Patient Registration System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(vapi_webhook.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=422,
        content=APIResponse(error="; ".join(errors)).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content=APIResponse(error="Internal server error").model_dump(),
    )


@app.get("/")
async def root():
    return {"status": "healthy", "service": "CareCloud Patient Registration API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
