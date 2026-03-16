from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import health, api, metrics, evaluation
from app.config import settings
from app.utils.logger import logger
import time

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(api.router, prefix="/api/v1", tags=["API"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(evaluation.router, prefix="/api/v1", tags=["Evaluation"])

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    logger.info(f"API Documentation available at /docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")


@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

