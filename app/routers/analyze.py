from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from starlette.concurrency import run_in_threadpool
import logging

from ..models.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse
from ..services.video_service import analyze_video, validate_videoUrl, get_processing_status

router = APIRouter()
logger = logging.getLogger(__name__)


async def background_analyze_video(request: AnalyzeRequest):
    """
    Background task to analyze video and send callbacks.
    
    Args:
        request: Video analysis request
    """
    try:
        logger.info(f"Starting background video analysis for: {request.videoUrl}")
        
        # Process video analysis
        result = await analyze_video(request)
        
        logger.info("Background video analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Background video analysis failed: {e}")
        # Note: In a production system, you might want to send error callbacks here


@router.post("/analyze")
async def analyze_video_endpoint(request: AnalyzeRequest, background_tasks: BackgroundTasks, op_type: str = "async"):
    """
    Analyze a video from URL and return structured scene and physics data.
    
    Args:
        request: Video analysis request
        background_tasks: FastAPI background tasks
        op_type: Operation type - "sync" for immediate response, "async" for background processing
        
    Returns:
        For sync: Structured analysis with scenes and physics information
        For async: Job submission confirmation
        
    Raises:
        HTTPException: Various error conditions
    """
    try:
        # Validate request
        if not request.videoUrl or not request.videoUrl.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video URL is required"
            )
        
        # if not validate_videoUrl(request.videoUrl):
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Invalid video URL format. Please provide a direct video file URL."
        #     )
        
        if request.frame_interval_seconds <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Frame interval must be positive"
            )
        
        if request.max_frames <= 0 or request.max_frames > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max frames must be between 1 and 500"
            )
        
        # For async processing, callbacks are required
        if op_type == "async" and not request.callback_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Callback payload is required for async processing"
            )
        
        logger.info(f"Processing video analysis request ({op_type}): {request.videoUrl}")
        
        if op_type == "sync":
            # Synchronous processing - return result immediately
            result = await run_in_threadpool(analyze_video, request)
            logger.info("Synchronous video analysis completed successfully")
            return result
        else:
            # Asynchronous processing - submit background task
            background_tasks.add_task(background_analyze_video, request)
            logger.info("Video analysis job submitted for background processing")
            return {"status": "job submitted", "message": "Video analysis started. Results will be sent to callback URLs."}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except ValueError as e:
        # Handle validation errors (e.g., video too long, too large)
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e)
        )
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during video analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video analysis failed: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    try:
        status_info = get_processing_status()
        return HealthResponse(
            status=status_info["status"],
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@router.get("/status")
async def get_status():
    """
    Get detailed processing status.
    
    Returns:
        Detailed status information
    """
    try:
        return get_processing_status()
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get status"
        )
