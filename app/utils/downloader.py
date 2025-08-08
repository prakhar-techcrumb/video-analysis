import os
import asyncio
import aiohttp
import aiofiles
import logging
from urllib.parse import urlparse

from ..core.config import settings

logger = logging.getLogger(__name__)


async def download_video(url: str, output_dir: str) -> str:
    """
    Download video from direct URL using aiohttp.
    
    Args:
        url: Direct video URL
        output_dir: Directory to save the video
        
    Returns:
        Path to downloaded video file
        
    Raises:
        Exception: If download fails or URL is not accessible
    """
    logger.info(f"Downloading video from: {url}")
    
    # Validate URL format
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format - missing scheme or domain")
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename from URL
    filename = os.path.basename(parsed_url.path) or "video.mp4"
    if not any(filename.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv']):
        filename += '.mp4'
    
    filepath = os.path.join(output_dir, filename)
    
    try:
        timeout = aiohttp.ClientTimeout(total=settings.DOWNLOAD_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '').lower()
                if content_type and not any(vid_type in content_type for vid_type in ['video', 'octet-stream', 'mp4', 'avi', 'mov']):
                    logger.warning(f"Content-Type may not be video: {content_type}")
                
                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > settings.MAX_VIDEO_SIZE_MB:
                        raise ValueError(f"Video too large: {size_mb:.1f}MB > {settings.MAX_VIDEO_SIZE_MB}MB")
                    logger.info(f"Downloading video: {size_mb:.1f}MB")
                
                # Download file
                async with aiofiles.open(filepath, 'wb') as f:
                    downloaded_size = 0
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Check size during download
                        if downloaded_size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
                            raise ValueError(f"Video exceeded size limit during download: {downloaded_size / (1024*1024):.1f}MB")
                
                # Verify file was created and has content
                if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                    raise Exception("Downloaded file is empty or was not created")
                
                logger.info(f"Video downloaded successfully: {filepath} ({downloaded_size / (1024*1024):.1f}MB)")
                return filepath
                
    except aiohttp.ClientError as e:
        # Clean up partial download
        if os.path.exists(filepath):
            os.remove(filepath)
        logger.error(f"HTTP error downloading video: {e}")
        raise Exception(f"Failed to access video URL: {e}")
    except asyncio.TimeoutError:
        # Clean up partial download  
        if os.path.exists(filepath):
            os.remove(filepath)
        logger.error("Download timeout")
        raise Exception(f"Download timeout after {settings.DOWNLOAD_TIMEOUT_SECONDS} seconds")
    except Exception as e:
        # Clean up partial download
        if os.path.exists(filepath):
            os.remove(filepath)
        logger.error(f"Video download failed: {e}")
        raise Exception(f"Video download failed: {e}")


def cleanup_file(filepath: str) -> None:
    """Safely remove a file if it exists."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up file: {filepath}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {filepath}: {e}")


def cleanup_directory(directory: str) -> None:
    """Safely remove all files in a directory."""
    try:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
            logger.info(f"Cleaned up directory: {directory}")
    except Exception as e:
        logger.warning(f"Failed to cleanup directory {directory}: {e}")
