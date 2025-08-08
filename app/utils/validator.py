"""
Data validation and cleanup utilities for video analysis.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def validate_and_clean_scenes(structured_data: Dict[str, Any], video_duration: float) -> Dict[str, Any]:
    """
    Validate and clean the structured scenes data.
    
    Args:
        structured_data: Raw structured data from LLM
        video_duration: Duration of the video in seconds
        
    Returns:
        Cleaned and validated structured data
    """
    # Basic structure validation
    if not isinstance(structured_data, dict):
        raise ValueError("LLM returned non-dict JSON")
    
    if 'scenes' not in structured_data:
        raise ValueError("LLM response missing 'scenes' key")
    
    scenes = structured_data.get('scenes', [])
    if len(scenes) == 0:
        raise ValueError("LLM returned empty scenes array")
    
    cleaned_scenes = []
    
    for i, scene in enumerate(scenes):
        try:
            # Ensure required fields exist
            if not isinstance(scene, dict):
                logger.warning(f"Scene {i} is not a dict, skipping")
                continue
            
            # Fix missing or invalid start_time
            if 'start_time' not in scene or scene['start_time'] is None:
                scene['start_time'] = i * 2.0  # Default based on scene index
                logger.warning(f"Scene {i} missing start_time, using default: {scene['start_time']}")
            
            # Fix missing or invalid end_time
            if 'end_time' not in scene or scene['end_time'] is None:
                # Use start_time + 2 seconds or video duration, whichever is smaller
                scene['end_time'] = min(scene['start_time'] + 2.0, video_duration)
                logger.warning(f"Scene {i} missing end_time, using default: {scene['end_time']}")
            
            # Ensure end_time is after start_time
            if scene['end_time'] <= scene['start_time']:
                scene['end_time'] = scene['start_time'] + 1.0
                logger.warning(f"Scene {i} end_time <= start_time, adjusting end_time to {scene['end_time']}")
            
            # Ensure times are within video duration
            scene['start_time'] = max(0.0, min(scene['start_time'], video_duration))
            scene['end_time'] = max(scene['start_time'] + 0.1, min(scene['end_time'], video_duration))
            
            # Ensure summary exists
            if 'summary' not in scene or not scene['summary']:
                scene['summary'] = f"Scene {i+1} from {scene['start_time']:.1f}s to {scene['end_time']:.1f}s"
                logger.warning(f"Scene {i} missing summary, using default")
            
            # Ensure physics structure exists
            if 'physics' not in scene or not isinstance(scene['physics'], dict):
                scene['physics'] = {"objects": [], "notes": None}
                logger.warning(f"Scene {i} missing physics structure, using default")
            
            if 'objects' not in scene['physics']:
                scene['physics']['objects'] = []
            
            if 'notes' not in scene['physics']:
                scene['physics']['notes'] = None
            
            # Clean physics objects
            cleaned_objects = []
            for obj in scene['physics'].get('objects', []):
                if isinstance(obj, dict) and 'name' in obj:
                    # Ensure all required fields exist with defaults
                    cleaned_obj = {
                        'name': obj.get('name', 'Unknown object'),
                        'approx_velocity_m_s': obj.get('approx_velocity_m_s'),
                        'direction': obj.get('direction'),
                        'collisions': bool(obj.get('collisions', False)),
                        'notes': obj.get('notes')
                    }
                    cleaned_objects.append(cleaned_obj)
            
            scene['physics']['objects'] = cleaned_objects
            cleaned_scenes.append(scene)
            
        except Exception as e:
            logger.error(f"Error cleaning scene {i}: {e}")
            # Skip problematic scenes rather than failing completely
            continue
    
    if len(cleaned_scenes) == 0:
        raise ValueError("No valid scenes after cleaning")
    
    structured_data['scenes'] = cleaned_scenes
    return structured_data


def validate_scene_structure(scene: Dict[str, Any]) -> bool:
    """
    Validate that a scene has the minimum required structure.
    
    Args:
        scene: Scene dictionary to validate
        
    Returns:
        True if scene is valid, False otherwise
    """
    if not isinstance(scene, dict):
        return False
    
    required_fields = ['start_time', 'end_time', 'summary', 'physics']
    for field in required_fields:
        if field not in scene:
            return False
    
    # Check physics structure
    physics = scene.get('physics', {})
    if not isinstance(physics, dict):
        return False
    
    if 'objects' not in physics or not isinstance(physics['objects'], list):
        return False
    
    return True


def clean_physics_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and validate a physics object.
    
    Args:
        obj: Raw physics object dictionary
        
    Returns:
        Cleaned physics object
    """
    return {
        'name': obj.get('name', 'Unknown object'),
        'approx_velocity_m_s': obj.get('approx_velocity_m_s'),
        'direction': obj.get('direction'),
        'collisions': bool(obj.get('collisions', False)),
        'notes': obj.get('notes')
    }
