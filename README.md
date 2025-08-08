# Video Analyzer API

A production-ready FastAPI application that analyzes videos using LLMs```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "frame_interval_seconds": 2,
    "max_frames": 120
  }'act detailed scene information and physics data. The system downloads videos (YouTube or direct URLs), extracts frames at configurable intervals, and uses GPT-4o for comprehensive analysis with LangSmith monitoring.

## 🚀 Features

- **Direct Video URL Support**: Handles direct video file URLs (mp4, avi, mkv, mov, webm, etc.)
- **Intelligent Frame Extraction**: Configurable intervals using ffmpeg/OpenCV
- **Dual LLM Analysis**: GPT-4o for detailed analysis, GPT-4o-mini for JSON structuring
- **LangSmith Monitoring**: Full traceability of all LLM interactions
- **Async & Concurrent**: Non-blocking request handling with ThreadPoolExecutor
- **Production Ready**: Comprehensive error handling, logging, and cleanup
- **Structured Output**: Well-defined JSON schema with scene and physics data

## Requirements

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with the following variables:

```bash
# LangSmith Monitoring
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=video-analyzer
LANGCHAIN_API_KEY=your_langsmith_api_key

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

## 🚀 Quick Start

### Option 1: Local Development

```bash
# 1. Clone and setup
git clone <repository>
cd video-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Docker

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t video-analyzer .
docker run -p 8000:8000 --env-file .env video-analyzer
```

## 📚 API Usage

### Analyze Video

**POST** `/analyze`

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "frame_interval_seconds": 2,
    "max_frames": 120
  }'
```

**Request Body:**
```json
{
  "video_url": "string",
  "frame_interval_seconds": 2,
  "max_frames": 200
}
```

**Response:**
```json
{
  "scene_analysis": {
    "scenes": [
      {
        "start_time": 0.0,
        "end_time": 4.0,
        "summary": "Person walking across the street",
        "physics": {
          "objects": [
            {
              "name": "person",
              "approx_velocity_m_s": 1.5,
              "direction": "left-to-right",
              "collisions": false,
              "notes": "steady walking pace"
            }
          ],
          "notes": "No significant physics events"
        }
      }
    ]
  },
  "full_analysis": "From 0.0s to 4.0s: A person enters the frame from the left side and walks steadily across the street. The individual maintains a consistent pace of approximately 1.5 m/s with no sudden accelerations or changes in direction. No other moving objects are visible in the scene, and no collisions or interactions occur during this timeframe. The background elements remain stationary throughout the sequence."
}
```

## 🧪 Testing

Test the API using the included test script:

```bash
# Run the test script
python test_api.py
```

Or test manually with curl:

```bash
# Health check
curl http://localhost:8000/health

# Analyze a video
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "frame_interval_seconds": 2,
    "max_frames": 50
  }'
```

## 🏗️ Architecture

```
video-analyzer/
├── app/
│   ├── main.py              # FastAPI app with startup/shutdown
│   ├── routers/
│   │   └── analyze.py       # /analyze endpoint
│   ├── services/
│   │   ├── video_service.py # Download + frame extraction orchestration
│   │   └── llm_service.py   # LLM analysis and JSON structuring
│   ├── utils/
│   │   ├── downloader.py    # Direct URL video downloads with aiohttp
│   │   └── frames.py        # Frame extraction (ffmpeg/OpenCV)
│   ├── core/
│   │   ├── llm_client.py    # LangChain + LangSmith initialization
│   │   └── config.py        # Environment variables and settings
│   └── models/
│       └── schemas.py       # Pydantic request/response models
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── test_api.py
```

### Key Design Principles

- **Separation of Concerns**: Clear separation between routing, business logic, and utilities
- **Async by Design**: All I/O operations are non-blocking
- **Resource Management**: Automatic cleanup of temporary files and proper thread pool management
- **Observability**: Comprehensive logging and LangSmith tracing
- **Error Resilience**: Graceful handling of failures with appropriate HTTP status codes

## ⚙️ Configuration

Environment variables (set in `.env` file):

### Required Settings
- `LANGCHAIN_API_KEY`: LangSmith API key for monitoring
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL

### Optional Settings
- `MAX_FRAMES`: Maximum frames to extract (default: 200)
- `MAX_VIDEO_DURATION_SECONDS`: Maximum video duration (default: 300)
- `FRAME_INTERVAL_SECONDS_DEFAULT`: Default frame interval (default: 2)
- `MAX_WORKERS`: Thread pool size (default: 4)
- `MAX_VIDEO_SIZE_MB`: Maximum video file size (default: 500)
- `DOWNLOAD_TIMEOUT_SECONDS`: Download timeout (default: 300)
- `LLM_TIMEOUT_SECONDS`: LLM request timeout (default: 120)

## 🚨 Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Invalid request (bad URL, missing fields)
- `413`: Video too large or too many frames requested
- `422`: Validation errors
- `500`: Server errors (LLM failures, processing errors)
- `503`: Service unavailable (health check failed)

## 📊 Monitoring

All LLM interactions are automatically traced in LangSmith when properly configured. View your traces at: https://smith.langchain.com/

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive error handling and logging
3. Include tests for new functionality
4. Update documentation as needed

## 📄 License

This project is licensed under the MIT License.
