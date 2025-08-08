from fastapi import APIRouter, HTTPException, status
import logging

from ..models.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse
from ..services.video_service import analyze_video, validate_video_url, get_processing_status

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_video_endpoint(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a video from URL and return structured scene and physics data.
    
    Args:
        request: Video analysis request
        
    Returns:
        Structured analysis with scenes and physics information
        
    Raises:
        HTTPException: Various error conditions
    """
    try:
        # Validate request
        if not request.video_url or not request.video_url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video URL is required"
            )
        
        if not validate_video_url(request.video_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video URL format. Please provide a direct video file URL."
            )
        
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
        
        logger.info(f"Processing video analysis request: {request.video_url}")
        
        # Process video
        result = await analyze_video(request)
        
        logger.info("Video analysis completed successfully")
        return result
        
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
