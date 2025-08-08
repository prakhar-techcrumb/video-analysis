from pydantic import BaseModel, Field
from typing import List, Optional


class AnalyzeRequest(BaseModel):
    """Request model for video analysis."""
    video_url: str = Field(..., description="Direct video URL (mp4, avi, mkv, mov, webm, etc.)")
    frame_interval_seconds: float = Field(default=2.0, gt=0, le=10, description="Interval between frame extractions")
    max_frames: int = Field(default=200, gt=0, le=500, description="Maximum number of frames to extract")


class PhysicsObject(BaseModel):
    """Physics information for an object in a scene."""
    name: str = Field(..., description="Name of the object")
    approx_velocity_m_s: Optional[float] = Field(None, description="Approximate velocity in m/s")
    direction: Optional[str] = Field(None, description="Direction of movement")
    collisions: bool = Field(default=False, description="Whether collisions occurred")
    notes: Optional[str] = Field(None, description="Additional physics notes")


class Physics(BaseModel):
    """Physics information for a scene."""
    objects: List[PhysicsObject] = Field(default_factory=list, description="Objects in the scene")
    notes: Optional[str] = Field(None, description="General physics notes for the scene")


class Scene(BaseModel):
    """A scene in the video with timing and physics information."""
    start_time: float = Field(..., ge=0, description="Scene start time in seconds")
    end_time: float = Field(..., ge=0, description="Scene end time in seconds")
    summary: str = Field(..., description="Summary of what happens in the scene")
    physics: Physics = Field(..., description="Physics information for the scene")


class SceneAnalysis(BaseModel):
    """Scene analysis wrapper containing the scenes array."""
    scenes: List[Scene] = Field(..., description="List of analyzed scenes")


class AnalyzeResponse(BaseModel):
    """Response model for video analysis."""
    scene_analysis: SceneAnalysis = Field(..., description="Structured scene analysis with scenes array")
    full_analysis: str = Field(..., description="Complete detailed frame analysis from LLM")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
