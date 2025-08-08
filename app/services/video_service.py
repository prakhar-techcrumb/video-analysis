import os
import tempfile
import logging
from typing import Dict, Any

from ..models.schemas import AnalyzeRequest, AnalyzeResponse
from ..utils.downloader import download_video, cleanup_file, cleanup_directory
from ..utils.frames import extract_frames, cleanup_frames, get_frame_timestamps, get_video_duration
from ..services.llm_service import analyze_frames, structure_analysis
from ..core.config import settings

logger = logging.getLogger(__name__)


async def analyze_video(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Main video analysis orchestration function.
    
    Args:
        request: Analysis request with video URL and parameters
        
    Returns:
        Structured analysis response
    """
    logger.info(f"Starting video analysis for URL: {request.video_url}")
    
    # Create temporary directories
    temp_base_dir = tempfile.mkdtemp(prefix="video_analyzer_")
    video_dir = os.path.join(temp_base_dir, "video")
    frames_dir = os.path.join(temp_base_dir, "frames")
    
    video_path = None
    frame_paths = []
    
    try:
        # Step 1: Download video
        logger.info("Step 1: Downloading video")
        video_path = await download_video(request.video_url, video_dir)
        
        # Step 2: Extract frames
        logger.info("Step 2: Extracting frames")
        frame_paths = await extract_frames(
            video_path,
            frames_dir,
            request.frame_interval_seconds,
            request.max_frames
        )
        
        if not frame_paths:
            raise Exception("No frames could be extracted from the video")
        
        # Calculate timestamps and get video duration
        timestamps = get_frame_timestamps(frame_paths, request.frame_interval_seconds)
        video_duration = get_video_duration(video_path)
        
        # Step 3: Analyze frames with LLM
        logger.info("Step 3: Analyzing frames with LLM")
        analysis_text = await analyze_frames(frame_paths, timestamps)
        
        # Step 4: Structure analysis into JSON
        logger.info("Step 4: Converting to structured JSON")
        structured_data = await structure_analysis(analysis_text, video_duration)
        
        # Create response with both structured scenes and original analysis
        response_data = {
            "scenes": structured_data.get("scenes", []),
            "frame_analysis": analysis_text
        }
        response = AnalyzeResponse(**response_data)
        logger.info(f"Analysis completed successfully with {len(response.scenes)} scenes")
        return response
        
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        raise
        
    finally:
        # Cleanup resources
        logger.info("Cleaning up temporary files")
        try:
            if video_path:
                cleanup_file(video_path)
            if frame_paths:
                cleanup_frames(frame_paths)
            cleanup_directory(temp_base_dir)
            
            # Remove temp base directory
            if os.path.exists(temp_base_dir):
                os.rmdir(temp_base_dir)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup error: {cleanup_error}")


def validate_video_url(url: str) -> bool:
    """
    Validate if URL looks like a valid direct video URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL appears valid
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Check if URL has scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Only allow http/https schemes
        if parsed.scheme.lower() not in ['http', 'https']:
            return False
        
        # Check for common video file extensions in direct URLs
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv']
        path_lower = parsed.path.lower()
        
        # Allow URLs with video extensions or containing 'video' in path/query
        has_video_ext = any(path_lower.endswith(ext) for ext in video_extensions)
        has_video_in_path = 'video' in url.lower()
        
        return has_video_ext or has_video_in_path
        
    except Exception:
        return False


def get_processing_status() -> Dict[str, Any]:
    """
    Get current processing status (placeholder for future monitoring).
    
    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "max_workers": settings.MAX_WORKERS,
        "max_frames": settings.MAX_FRAMES,
        "max_video_duration": settings.MAX_VIDEO_DURATION_SECONDS
    }
