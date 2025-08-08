from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from concurrent.futures import ThreadPoolExecutor
import uvicorn

from .routers import analyze
from .core.config import settings
from .models.schemas import ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global thread pool executor
executor: ThreadPoolExecutor = None

app = FastAPI(
    title="Video Analyzer API",
    description="Analyze videos from direct URLs using AI to extract scene and physics information",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    global executor
    
    logger.info("Starting Video Analyzer API...")
    
    # Initialize thread pool executor
    executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
    logger.info(f"Thread pool initialized with {settings.MAX_WORKERS} workers")
    
    # Test LLM connection
    try:
        from .core.llm_client import llm, gpt_4o_mini
        logger.info("LLM clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LLM clients: {e}")
        # Don't fail startup, but log the error
    
    logger.info("Video Analyzer API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global executor
    
    logger.info("Shutting down Video Analyzer API...")
    
    # Shutdown thread pool
    if executor:
        executor.shutdown(wait=True)
        logger.info("Thread pool executor shutdown complete")
    
    logger.info("Video Analyzer API shutdown complete")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Video Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(analyze.router, tags=["Video Analysis"])


def get_executor() -> ThreadPoolExecutor:
    """Get the global thread pool executor."""
    global executor
    if executor is None:
        raise RuntimeError("Thread pool executor not initialized")
    return executor


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
