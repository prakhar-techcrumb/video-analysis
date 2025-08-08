import json
import logging
import base64
from typing import List, Dict, Any
from pathlib import Path

from ..core.llm_client import invokeLLM, invoke_mini_llm
from ..core.config import settings

logger = logging.getLogger(__name__)


def create_frame_description(frame_path: str, timestamp: float) -> str:
    """
    Create a text description of a frame for LLM analysis.
    
    Args:
        frame_path: Path to frame image
        timestamp: Timestamp of frame in seconds
        
    Returns:
        Frame description string
    """
    frame_name = Path(frame_path).name
    return f"Frame at {timestamp:.1f}s ({frame_name}): Frame extracted from video"


def encode_frame_as_base64(frame_path: str, max_size_kb: int = 200) -> str:
    """
    Encode frame as base64 string for LLM vision analysis.
    
    Args:
        frame_path: Path to frame image
        max_size_kb: Maximum size in KB
        
    Returns:
        Base64 encoded string or empty string if too large
    """
    try:
        file_size = Path(frame_path).stat().st_size
        if file_size > max_size_kb * 1024:
            logger.warning(f"Frame {frame_path} too large ({file_size/1024:.1f}KB > {max_size_kb}KB), skipping")
            return ""  # Skip large files
        
        with open(frame_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        logger.warning(f"Failed to encode frame {frame_path}: {e}")
        return ""


async def analyze_frames(frame_paths: List[str], timestamps: List[float]) -> str:
    """
    Analyze video frames using LLM to generate detailed analysis.
    
    Args:
        frame_paths: List of frame file paths
        timestamps: List of frame timestamps
        
    Returns:
        Detailed text analysis of the video
    """
    logger.info(f"Analyzing {len(frame_paths)} frames with LLM")
    
    # Create frame descriptions with base64 encoding for vision analysis
    frame_descriptions = []
    vision_content = []
    
    for frame_path, timestamp in zip(frame_paths, timestamps):
        # Try to encode frame as base64 for vision models
        encoded_frame = encode_frame_as_base64(frame_path, max_size_kb=200)  # Increased size limit
        
        if encoded_frame:
            # Add image to vision content
            vision_content.append({
                "type": "image_url",
                "image_url": {"url": encoded_frame}
            })
            frame_descriptions.append(f"Frame at {timestamp:.1f}s: [Image provided for visual analysis]")
        else:
            frame_descriptions.append(f"Frame at {timestamp:.1f}s: Video frame extracted from {Path(frame_path).name}")
    
    system_prompt = """You are an expert video analyst. Analyze the provided video frames to create a detailed scene-by-scene analysis describing:
- What objects/entities are present in each frame
- Motion and behavior of objects between frames
- Notable events (collisions, changes of direction, appearances/disappearances)
- Rough timestamps where things occur
- Physics observations (e.g., acceleration, speed estimates, forces, gravity effects, momentum transfers)

Provide clear time-coded notes and keep the analysis factual and detailed. Focus on actual visual content you can observe."""

    # Prepare user content - mix text and images if available
    user_content = [
        {
            "type": "text", 
            "text": f"Analyze these {len(frame_paths)} video frames extracted at the following timestamps:\n\n" + 
                   "\n".join(frame_descriptions) + 
                   "\n\nProvide a comprehensive scene-by-scene analysis with specific timestamps, object movements, and physics observations."
        }
    ]
    
    # Add vision content if we have encoded frames
    user_content.extend(vision_content)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        response = await _invoke_llm_async(messages, "Video Frame Analysis")
        analysis_text = response.content if hasattr(response, 'content') else str(response)
        logger.info(f"Frame analysis completed, length: {len(analysis_text)} characters")
        
        if not analysis_text or len(analysis_text.strip()) < 50:
            raise Exception("LLM returned empty or very short analysis")
        
        return analysis_text
        
    except Exception as e:
        logger.error(f"Frame analysis failed: {e}")
        raise Exception(f"Failed to analyze frames: {e}")



async def structure_analysis(analysis_text: str, video_duration: float = 10.0) -> Dict[str, Any]:
    """
    Convert text analysis to structured JSON using LLM.
    
    Args:
        analysis_text: Text analysis from first LLM call
        video_duration: Duration of the video in seconds
        
    Returns:
        Structured JSON as dictionary
    """
    logger.info("Converting analysis to structured JSON")
    
    schema = """{
  "scenes": [
    {
      "start_time": float,
      "end_time": float,
      "summary": string,
      "physics": {
        "objects": [
          {
            "name": string,
            "approx_velocity_m_s": float | null,
            "direction": string | null,
            "collisions": boolean,
            "notes": string | null
          }
        ],
        "notes": string | null
      }
    }
  ]
}"""

    system_prompt = f"""Convert the following analysis into strict JSON matching this schema:
{schema}

Requirements:
- Return ONLY valid JSON, no other text or markdown
- Extract all scenes mentioned in the analysis
- Use exact start_time and end_time values from the analysis
- Include all objects and their physics properties
- Convert velocity descriptions to numeric m/s values where possible
- Set collisions to true only if explicitly mentioned"""

    user_prompt = f"""Convert this detailed video analysis to the required JSON format:

{analysis_text}

Extract all scenes with their exact timing and physics information."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = await _invoke_mini_llm_async(messages, "Analysis Structuring")
        json_text = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"Raw LLM JSON response length: {len(json_text)}")
        
        # Clean up JSON text (remove any markdown formatting)
        json_text = json_text.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        # Parse JSON
        structured_data = json.loads(json_text)
        
        # Validate the structure
        if not isinstance(structured_data, dict):
            raise ValueError("LLM returned non-dict JSON")
        
        if 'scenes' not in structured_data:
            raise ValueError("LLM response missing 'scenes' key")
        
        scenes = structured_data.get('scenes', [])
        if len(scenes) == 0:
            raise ValueError("LLM returned empty scenes array")
        
        logger.info(f"Successfully structured analysis into {len(scenes)} scenes")
        return structured_data
            
    except json.JSONDecodeError as je:
        logger.error(f"Failed to parse LLM JSON response: {je}")
        logger.error(f"Raw response that failed: {json_text}")
        raise Exception(f"LLM returned invalid JSON: {je}")
        
    except Exception as e:
        logger.error(f"Analysis structuring failed: {e}")
        raise Exception(f"Failed to structure analysis: {e}")


async def _invoke_llm_async(messages: List[Dict[str, str]], name: str) -> Any:
    """Async wrapper for LLM invocation."""
    import asyncio
    
    def _invoke():
        return invokeLLM(messages, name)
    
    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, _invoke),
        timeout=settings.LLM_TIMEOUT_SECONDS
    )


async def _invoke_mini_llm_async(messages: List[Dict[str, str]], name: str) -> Any:
    """Async wrapper for mini LLM invocation."""
    import asyncio
    
    def _invoke():
        return invoke_mini_llm(messages, name)
    
    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, _invoke),
        timeout=settings.LLM_TIMEOUT_SECONDS
    )
