import os
import asyncio
import subprocess
import logging
import cv2
from typing import List

from ..core.config import settings

logger = logging.getLogger(__name__)


def get_video_duration(video_path: str) -> float:
    """
    Get video duration using ffprobe.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Duration in seconds
    """
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        logger.info(f"Video duration: {duration:.2f} seconds")
        return duration
        
    except Exception as e:
        logger.warning(f"Failed to get video duration with ffprobe: {e}")
        # Fallback to OpenCV
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                duration = frame_count / fps if fps > 0 else 0
                cap.release()
                logger.info(f"Video duration (OpenCV fallback): {duration:.2f} seconds")
                return duration
        except Exception as cv_e:
            logger.error(f"Failed to get duration with OpenCV: {cv_e}")
        
        # Default fallback
        return 0.0


async def extract_frames_ffmpeg(
    video_path: str,
    output_dir: str,
    interval_seconds: float,
    max_frames: int
) -> List[str]:
    """
    Extract frames using ffmpeg.
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save frames
        interval_seconds: Interval between frames in seconds
        max_frames: Maximum number of frames to extract
        
    Returns:
        List of frame file paths
    """
    logger.info(f"Extracting frames with ffmpeg: interval={interval_seconds}s, max={max_frames}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    def _extract():
        """Blocking frame extraction function."""
        try:
            # Build ffmpeg command
            output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f'fps=1/{interval_seconds}',
                '-q:v', '2',  # High quality JPEG
                '-frames:v', str(max_frames),
                '-y',  # Overwrite output files
                output_pattern
            ]
            
            # Run ffmpeg
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Collect extracted frame paths
            frame_paths = []
            for i in range(1, max_frames + 1):
                frame_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
                if os.path.exists(frame_path):
                    frame_paths.append(frame_path)
                else:
                    break
            
            logger.info(f"Extracted {len(frame_paths)} frames with ffmpeg")
            return frame_paths
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed: {e.stderr}")
            raise Exception(f"Frame extraction failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Frame extraction error: {e}")
            raise
    
    # Run in executor
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _extract)


async def extract_frames_opencv(
    video_path: str,
    output_dir: str,
    interval_seconds: float,
    max_frames: int
) -> List[str]:
    """
    Extract frames using OpenCV (fallback method).
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save frames
        interval_seconds: Interval between frames in seconds
        max_frames: Maximum number of frames to extract
        
    Returns:
        List of frame file paths
    """
    logger.info(f"Extracting frames with OpenCV: interval={interval_seconds}s, max={max_frames}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    def _extract():
        """Blocking frame extraction function."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"Cannot open video file: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # Default fallback
            
            frame_interval = int(fps * interval_seconds)
            frame_paths = []
            frame_count = 0
            extracted_count = 0
            
            while extracted_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract frame at interval
                if frame_count % frame_interval == 0:
                    frame_filename = f"frame_{extracted_count + 1:04d}.jpg"
                    frame_path = os.path.join(output_dir, frame_filename)
                    
                    # Save frame
                    cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    frame_paths.append(frame_path)
                    extracted_count += 1
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(frame_paths)} frames with OpenCV")
            return frame_paths
            
        except Exception as e:
            logger.error(f"OpenCV frame extraction error: {e}")
            raise
    
    # Run in executor
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _extract)


async def extract_frames(
    video_path: str,
    output_dir: str,
    interval_seconds: float,
    max_frames: int
) -> List[str]:
    """
    Extract frames from video using ffmpeg (preferred) or OpenCV (fallback).
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save frames
        interval_seconds: Interval between frames in seconds
        max_frames: Maximum number of frames to extract
        
    Returns:
        List of frame file paths
    """
    # Validate video duration
    duration = get_video_duration(video_path)
    if duration > settings.MAX_VIDEO_DURATION_SECONDS:
        raise ValueError(f"Video too long: {duration:.1f}s > {settings.MAX_VIDEO_DURATION_SECONDS}s")
    
    # Calculate expected frames and adjust if needed
    expected_frames = min(max_frames, int(duration / interval_seconds) + 1)
    actual_max_frames = min(max_frames, expected_frames)
    
    logger.info(f"Video duration: {duration:.1f}s, extracting up to {actual_max_frames} frames")
    
    try:
        # Try ffmpeg first
        return await extract_frames_ffmpeg(video_path, output_dir, interval_seconds, actual_max_frames)
    except Exception as ffmpeg_error:
        logger.warning(f"ffmpeg extraction failed, trying OpenCV: {ffmpeg_error}")
        try:
            # Fallback to OpenCV
            return await extract_frames_opencv(video_path, output_dir, interval_seconds, actual_max_frames)
        except Exception as opencv_error:
            logger.error(f"Both ffmpeg and OpenCV extraction failed: {opencv_error}")
            raise Exception(f"Frame extraction failed: ffmpeg error: {ffmpeg_error}, opencv error: {opencv_error}")


def cleanup_frames(frame_paths: List[str]) -> None:
    """Clean up extracted frame files."""
    for frame_path in frame_paths:
        try:
            if os.path.exists(frame_path):
                os.remove(frame_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup frame {frame_path}: {e}")
    
    logger.info(f"Cleaned up {len(frame_paths)} frame files")


def get_frame_timestamps(frame_paths: List[str], interval_seconds: float) -> List[float]:
    """
    Calculate timestamps for extracted frames.
    
    Args:
        frame_paths: List of frame file paths
        interval_seconds: Interval between frames
        
    Returns:
        List of timestamps in seconds
    """
    return [i * interval_seconds for i in range(len(frame_paths))]
