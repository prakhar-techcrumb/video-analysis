#!/usr/bin/env python3
"""
Test script for Video Analyzer API
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any


async def test_health_endpoint(base_url: str = "http://localhost:8000"):
    """Test the health endpoint."""
    print("Testing health endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False


async def test_analyze_endpoint(
    video_url: str,
    base_url: str = "http://localhost:8000",
    frame_interval: float = 2.0,
    max_frames: int = 50
):
    """Test the analyze endpoint with a video URL."""
    print(f"Testing analyze endpoint with URL: {video_url}")
    
    request_data = {
        "video_url": video_url,
        "frame_interval_seconds": frame_interval,
        "max_frames": max_frames
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/analyze",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=600)  # 10 minutes
            ) as response:
                
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Analysis completed successfully!")
                    scene_count = len(data.get('scene_analysis', {}).get('scenes', []))
                    print(f"Number of scenes: {scene_count}")
                    print(f"Full analysis length: {len(data.get('full_analysis', ''))}")
                    
                    # Print first scene as example
                    scenes = data.get('scene_analysis', {}).get('scenes', [])
                    if scenes:
                        first_scene = scenes[0]
                        print(f"First scene: {first_scene}")
                    
                    # Print beginning of full analysis
                    if data.get('full_analysis'):
                        analysis_preview = data['full_analysis'][:200] + "..." if len(data['full_analysis']) > 200 else data['full_analysis']
                        print(f"Full analysis preview: {analysis_preview}")
                    
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Analysis failed: {response.status}")
                    print(f"Error: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            print("❌ Request timed out")
            return None
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None


def print_curl_example():
    """Print example curl command."""
    print("\n" + "="*50)
    print("EXAMPLE CURL COMMAND:")
    print("="*50)
    print("""
curl -X POST "http://localhost:8000/analyze" \\
  -H "Content-Type: application/json" \\
  -d '{
    "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "frame_interval_seconds": 2,
    "max_frames": 120
  }'
""")


async def main():
    """Main test function."""
    print("Video Analyzer API Test Script")
    print("="*40)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    health_ok = await test_health_endpoint(base_url)
    if not health_ok:
        print("❌ Server not responding. Make sure it's running:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)
    
    print("\n" + "-"*40)
    
    # Test with different video URLs
    test_urls = [
        # Example direct video URLs
        "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        result = await test_analyze_endpoint(
            video_url=url,
            base_url=base_url,
            frame_interval=3.0,
            max_frames=30
        )
        
        if result:
            # Save result to file
            output_file = f"test_result_{len(test_urls)}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"💾 Result saved to {output_file}")
        
        print("-"*40)
    
    print_curl_example()


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
