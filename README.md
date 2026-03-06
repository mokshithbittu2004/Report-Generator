# Artifact Report Generator

A **production-grade, modular FastAPI backend service** that transforms automation artifacts into AI-powered HTML and PDF reports at scale.

## Overview

Process thousands of automation script artifact ZIPs automatically with:
- **Gemini-powered step summaries** - AI analysis of each automation step
- **Process narratives** - Contextual overview of execution flow
- **Embedded screenshots** - Step-by-step visual documentation
- **Dual export** - HTML + PDF downloads
- **Async processing** - Concurrent report generation
- **Rate limiting** - 30 requests/minute with in-memory throttling
- **Structured logging** - JSON logs with Sentry integration
- **Modular architecture** - Service-oriented design with clear separation of concerns

## Architecture

Fully modular production-grade structure:

```
app/
├── core/               # Configuration, logging, error handling
│   ├── config.py       # Settings management
│   ├── logger.py       # Structured JSON logging
│   ├── errors.py       # Error codes and exceptions
│   └── exceptions.py   # Global exception handlers
├── services/           # Business logic
│   ├── zip_service.py       # ZIP extraction & validation
│   ├── ai_service.py        # Gemini AI integration
│   ├── report_service.py    # HTML generation
│   └── pdf_service.py       # PDF conversion
├── routes/             # API endpoints
│   ├── health.py       # Health checks
│   └── report.py       # Report generation
├── middleware/         # HTTP middleware
│   ├── rate_limit.py   # Rate limiting
│   └── logging.py      # Request/response logging
└── main.py            # FastAPI app initialization
```

## Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
export GEMINI_API_KEY="your_gemini_api_key"

# Start service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Service runs at `http://localhost:8000` with Swagger UI at `/docs`

## API Endpoints

### Generate Report
**POST** `/api/v1/generate-report`

Generate HTML and PDF reports from automation artifacts ZIP.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/generate-report \
  -F "file=@artifacts.zip"
```

**Response:**
```json
{
  "status": "success",
  "html": "base64_encoded_html",
  "pdf": "base64_encoded_pdf",
  "metadata": {
    "total_steps": 15,
    "passed_steps": 14,
    "failed_steps": 1,
    "total_duration_sec": 285.5
  }
}
```

### Health Check
**GET** `/health`

```bash
curl http://localhost:8000/health
```

Response: `{"status": "healthy", "service": "Artifact Report Generator"}`

## ZIP Structure

Expected artifact ZIP format:

```
automation_artifact.zip
├── status.txt                    # "passed" or "failed"
├── started_at.txt                # ISO 8601 timestamp
├── finished_at.txt               # ISO 8601 timestamp
└── success/ (or failures/)
    ├── 0__step_0_hash/
    │   ├── step_summary.json
    │   └── screenshot.png
    ├── 1__step_1_hash/
    │   ├── step_summary.json
    │   └── screenshot.png
    └── ...
```

### step_summary.json

```json
{
  "step_index": 0,
  "step_name": "0__step_0_ecb40f97ce06",
  "intent": "Navigate to OrangeHRM login page.",
  "duration_sec": 26.4899,
  "url": "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login",
  "attempts": 1,
  "max_retries": 1,
  "status": "passed"
}
```

## Usage Examples

### Python

```python
import base64
import requests

# Upload ZIP
with open('artifacts.zip', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/v1/generate-report', files=files)

result = response.json()
html_bytes = base64.b64decode(result['html'])
pdf_bytes = base64.b64decode(result['pdf'])

with open('report.html', 'wb') as f:
    f.write(html_bytes)
with open('report.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

### Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const formData = new FormData();
formData.append('file', fs.createReadStream('artifacts.zip'));

const response = await axios.post('http://localhost:8000/api/v1/generate-report', formData, {
  headers: formData.getHeaders()
});

const { html, pdf } = response.data;
fs.writeFileSync('report.html', Buffer.from(html, 'base64'));
fs.writeFileSync('report.pdf', Buffer.from(pdf, 'base64'));
```

### cURL

```bash
# Generate report
curl -X POST http://localhost:8000/api/v1/generate-report \
  -F "file=@artifacts.zip" > response.json

# Extract base64 and decode
jq -r '.html' response.json | base64 -d > report.html
jq -r '.pdf' response.json | base64 -d > report.pdf
```

## Configuration

### Environment Variables

```env
# Service
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# AI
GEMINI_API_KEY=your_key_here

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# File Upload
MAX_ZIP_SIZE_MB=500
UPLOAD_TIMEOUT_SECONDS=300

# Error Tracking (Optional)
SENTRY_DSN=
```

## Deployment

### Docker

```bash
# Build image
docker build -t artifact-reporter .

# Run container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  artifact-reporter
```

### Docker Compose

```bash
docker-compose up
```

### Vercel/Serverless

Customize for serverless:
- Use cloud storage (Vercel Blob, S3) for files
- Set appropriate timeouts for large ZIPs
- Configure environment variables in dashboard

## Performance & Monitoring

### Logging

All requests/errors logged as structured JSON:

```json
{
  "timestamp": "2026-01-15T08:15:00Z",
  "level": "INFO",
  "logger": "app.services.ai_service",
  "message": "Generated step summary",
  "method": "POST",
  "path": "/api/v1/generate-report"
}
```

### Error Tracking

Sentry integration enabled via `SENTRY_DSN`. Captures all unhandled exceptions with full context.

### Rate Limiting

- Per-IP tracking
- 30 requests/minute default (configurable)
- Returns 429 when exceeded

## Features

- **Async Processing** - Concurrent AI summaries with `asyncio.gather()`
- **Structured Logging** - JSON logs via `python-json-logger`
- **Error Codes** - Standardized error responses
- **CORS** - Enabled for all origins
- **Type Hints** - Full Python type annotations
- **Modular Design** - Easy to extend and maintain
- **No Storage** - Stateless, ZIPs processed on-the-fly
- **Health Checks** - Docker/Kubernetes compatible

## Troubleshooting

### Missing GEMINI_API_KEY
```bash
export GEMINI_API_KEY="your_key"
```

### Invalid ZIP
Ensure ZIP contains `status.txt` and appropriate folder (`success/` or `failures/`)

### PDF generation fails on Linux
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0
```

### Rate limit exceeded
Reduce request frequency or increase `RATE_LIMIT_PER_MINUTE` in `.env`

## API Documentation

Interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Dependencies

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **google-generativeai** - Gemini API
- **Jinja2** - HTML templating
- **WeasyPrint** - PDF generation
- **python-json-logger** - JSON logging
- **sentry-sdk** - Error tracking

## License

MIT

## Complete File Structure & Documentation

### Root Level Files

- **`app/`** - Main application module containing all service code
- **`requirements.txt`** - Python dependencies (11 packages total)
- **`Dockerfile`** - Production Docker image with WeasyPrint system dependencies
- **`docker-compose.yml`** - Multi-container orchestration
- **`.env.example`** - Environment variable template
- **`.gitignore`** - Git exclusion patterns (Python backend)
- **`README.md`** - This documentation

### Core Module (`app/core/`)

#### `config.py` (41 lines)
**Purpose**: Centralized configuration management using Pydantic Settings

**Key Components**:
- `Settings` class - Uses environment variables or defaults
- `get_settings()` - LRU-cached singleton for configuration
- Settings include: service metadata, server config, AI model selection, rate limits, file upload constraints, error tracking, logging levels

**Environment Variables Managed**:
```plaintext
SERVICE_NAME: str = "Artifact Report Generator"
SERVICE_VERSION: str = "1.0.0"
DEBUG: bool = false (development mode)
HOST: str = "0.0.0.0" (server bind address)
PORT: int = 8000 (server port)
WORKERS: int = 4 (uvicorn worker count)
API_PREFIX: str = "/api/v1" (API route prefix)
GEMINI_API_KEY: str = "" (REQUIRED - Google Gemini API key)
GEMINI_MODEL: str = "gemini-2.0-flash" (Gemini model version)
RATE_LIMIT_ENABLED: bool = true
RATE_LIMIT_PER_MINUTE: int = 30 (requests per IP per minute)
MAX_ZIP_SIZE_MB: int = 500 (maximum upload size)
UPLOAD_TIMEOUT_SECONDS: int = 300 (5 minute timeout)
SENTRY_DSN: str = "" (optional - for error tracking)
SENTRY_ENABLED: bool = auto (enabled if DSN set)
LOG_LEVEL: str = "INFO" (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

#### `logger.py` (32 lines)
**Purpose**: Structured JSON logging configuration

**Key Components**:
- `JSONFormatter` - Custom JSON formatter extending `pythonjsonlogger`
- `setup_logging()` - Configures global logger with JSON output to stdout
- `get_logger()` - Factory function to get named logger instances

**Logging Features**:
- JSON format with timestamp, level, logger name, message
- Automatic exception traceback inclusion
- Third-party loggers silenced (uvicorn set to WARNING)
- Stdout-only output (12-factor app compliance)
- All logs include ISO 8601 timestamps

**Example Log Output**:
```json
{
  "timestamp": "2026-01-15T08:15:30.123456Z",
  "level": "INFO",
  "logger": "app.routes.report",
  "message": "Report generated successfully",
  "steps": 15,
  "pathname": "app/routes/report.py",
  "lineno": 105
}
```

#### `errors.py` (40 lines)
**Purpose**: Standardized error codes and exception handling

**Error Codes Defined**:
```plaintext
INVALID_ZIP = "ERR_INVALID_ZIP"
ZIP_EXTRACTION_FAILED = "ERR_ZIP_EXTRACTION_FAILED"
MISSING_ARTIFACTS = "ERR_MISSING_ARTIFACTS"
GEMINI_API_ERROR = "ERR_GEMINI_API_ERROR"
PDF_GENERATION_FAILED = "ERR_PDF_GENERATION_FAILED"
RATE_LIMIT_EXCEEDED = "ERR_RATE_LIMIT_EXCEEDED"
INTERNAL_SERVER_ERROR = "ERR_INTERNAL_SERVER_ERROR"
```

**Key Classes**:
- `ErrorCode` - Enum with all standardized error codes
- `APIException` - Custom exception with error code, message, HTTP status, optional details
- `create_error_response()` - Factory for standardized error JSON responses

#### `exceptions.py` (48 lines)
**Purpose**: Global FastAPI exception handlers

**Exception Handlers**:
- `api_exception_handler()` - Catches APIException, returns custom error response with 400+ status
- `general_exception_handler()` - Catches all other exceptions, logs, returns 500 with error code

**Response Format**:
```json
{
  "status": "error",
  "error_code": "ERR_INVALID_ZIP",
  "message": "Invalid ZIP file format",
  "details": {}
}
```

### Services Module (`app/services/`)

#### `zip_service.py` (70 lines)
**Purpose**: ZIP file extraction and artifact parsing

**Main Method**: `extract_and_parse(zip_content: bytes) -> dict`

**Process Flow**:
1. Write bytes to temporary `/tmp/artifact.zip`
2. Open ZIP file with `zipfile.ZipFile()`
3. Read `status.txt` to determine if "passed" or "failed"
4. Select artifact folder: "success/" or "failures/"
5. Extract `started_at.txt` and `finished_at.txt` for timing
6. Iterate through ZIP entries matching `{folder}/*/step_summary.json`
7. Parse each `step_summary.json` as JSON
8. Find corresponding `screenshot.png` and read as binary data
9. Collect all steps with summaries and screenshots
10. Return structured dict with status, timing, and steps

**Error Handling**:
- Validates ZIP file format (catches `BadZipFile`)
- Checks artifact folder existence
- Ensures step artifacts exist (validates non-empty steps list)
- Cleans up temporary file in finally block
- Logs all operations for debugging

**Return Structure**:
```python
{
    "status": "passed",  # or "failed"
    "started_at": "2026-01-15T08:09:59.549459+00:00",
    "finished_at": "2026-01-15T08:15:26.037473+00:00",
    "steps": [
        {
            "summary": {...step_summary.json data...},
            "screenshot": b"<binary PNG data>"
        },
        # ... more steps
    ]
}
```

#### `ai_service.py` (56 lines)
**Purpose**: Gemini AI integration for generating summaries

**Key Components**:
- `__init__()` - Configures Gemini API with API key, selects model
- `generate_step_summary()` - Generate AI summary for each step
- `generate_overall_description()` - Generate process narrative

**`generate_step_summary()` Details**:
- Takes: step_intent, step_status, duration_sec
- Prompt: "Based on automation step info, provide 1-2 sentence summary"
- Returns: AI-generated text summary (1-2 sentences)
- Error handling: Catches all exceptions, raises APIException with GEMINI_API_ERROR

**`generate_overall_description()` Details**:
- Takes: total_steps, passed_steps, failed_steps, duration_sec
- Prompt: "Create 2-3 sentence narrative describing what happened"
- Focus: Process flow narrative (what steps executed, key actions)
- Returns: AI-generated text (2-3 sentences)
- Error handling: Same as step summaries

**Example Prompts Sent to Gemini**:
```plaintext
Step Summary Prompt:
"Based on the following automation step information, provide a brief 1-2 sentence summary:
- Intent: Click submit button on login form
- Status: passed
- Duration: 2.5s
Provide only the summary, no extra text."

Overall Description Prompt:
"Create a brief 2-3 sentence narrative describing the automation process execution:
- Total steps executed: 15
- Passed: 14
- Failed: 1
- Total duration: 285.5s
Focus on what happened during the process (the narrative flow). Provide only the narrative, no extra text."
```

#### `report_service.py` (180+ lines)
**Purpose**: Beautiful HTML report generation

**Key Component**: `HTML_TEMPLATE` - Embedded Jinja2 template (450+ lines)

**`generate_html()` Method**:
- Input: steps list, overall_description, started_at, finished_at
- Process:
  1. Count passed/failed steps
  2. Calculate total duration (sum of all step durations)
  3. Prepare step data with base64-encoded screenshots
  4. Render Jinja2 template with all data
  5. Return HTML string
- Output: Complete HTML5 document with embedded CSS

**HTML Features**:
- Responsive design (flexbox, grid, media queries)
- Gradient header with purple theme
- Stats cards showing total/passed/failed/duration
- Process Overview section with AI-generated narrative
- Step cards with:
  - Step name and metadata (duration, status, attempts)
  - Original intent highlighted in blue box
  - AI summary highlighted in yellow box
  - URL with clickable link
  - Base64-encoded screenshot embedded directly
- Print-friendly styling
- Box shadows and hover effects for interactivity

**CSS Highlights**:
- Color scheme: Purple (#667eea) primary, blue (#1976d2) links, yellow (#ffc107) accents
- Typography: System fonts (San Francisco, Segoe UI, Ubuntu)
- Cards: White background, shadow effects, rounded corners
- Status badges: Green for passed, red for failed
- Media queries: Print optimization

#### `pdf_service.py` (18 lines)
**Purpose**: Convert HTML to PDF

**`generate_pdf()` Method**:
- Input: HTML string content
- Process:
  1. Create BytesIO buffer
  2. Use WeasyPrint: `HTML(string=html_content).write_pdf(pdf_file)`
  3. Get bytes from buffer
  4. Return binary PDF data
- Error handling: Catches WeasyPrint errors, raises APIException with PDF_GENERATION_FAILED
- Note: WeasyPrint renders HTML → PDF with CSS support, includes images, handles fonts

### Routes Module (`app/routes/`)

#### `health.py` (15 lines)
**Purpose**: Health check endpoint for monitoring

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "service": "Artifact Report Generator"
}
```

**Use Case**: Kubernetes probes, load balancer health checks, uptime monitoring

#### `report.py` (115 lines)
**Purpose**: Main API endpoint for report generation

**Endpoint**: `POST /api/v1/generate-report`

**Request**:
- Content-Type: `multipart/form-data`
- Form field: `file` (ZIP file)

**Validation Steps**:
1. Check filename ends with `.zip`
2. Read file content
3. Calculate size in MB: `len(content) / (1024 * 1024)`
4. Validate size ≤ MAX_ZIP_SIZE_MB (default 500MB)

**Processing Steps**:
1. Extract ZIP using ZipService
2. Generate AI summaries concurrently:
   - Create async tasks for each step
   - Use `asyncio.gather()` for parallel execution
   - Attach AI summary to each step
3. Count passed/failed steps
4. Calculate total duration
5. Generate overall description
6. Generate HTML using ReportService
7. Generate PDF using PDFService
8. Base64 encode both HTML and PDF
9. Return response

**Response**:
```json
{
  "status": "success",
  "html": "base64_encoded_html_string",
  "pdf": "base64_encoded_pdf_string",
  "metadata": {
    "total_steps": 15,
    "passed_steps": 14,
    "failed_steps": 1,
    "total_duration_sec": 285.5
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": {
    "status": "error",
    "error_code": "ERR_INVALID_ZIP",
    "message": "File must be a ZIP archive"
  }
}
```

### Middleware Module (`app/middleware/`)

#### `rate_limit.py` (32 lines)
**Purpose**: Rate limiting per client IP

**`RateLimiter` Class**:
- `__init__(requests_per_minute=30)` - Initialize with rate limit
- `requests: dict` - Stores request timestamps per client IP
- Default: 30 requests per client per minute

**`check_rate_limit()` Method**:
- Extract client IP from request
- Clean requests older than 1 minute
- Check if current requests ≥ limit
- Raise HTTPException(429) if exceeded
- Append current request timestamp

**Raises**: HTTPException with status 429 (Too Many Requests)

#### `logging.py` (25 lines)
**Purpose**: Request/response logging middleware

**Logs**:
- Request: method, path, query params
- Response: status code, processing time
- Errors: Full exception traceback

**Output**: Structured JSON logs via logger

### Main Application (`app/main.py`) (65 lines)

**Components**:
1. **Sentry Initialization** - If SENTRY_DSN set, init error tracking
2. **Lifespan Context** - Logs startup/shutdown events
3. **FastAPI App** - Title, version, description
4. **CORS Middleware** - Allow all origins (*)
5. **Request Logging** - Log all requests
6. **Rate Limiting** - Check rate limits on POST requests
7. **Exception Handlers** - APIException and general Exception
8. **Route Registration** - Include health and report routers
9. **Uvicorn Server** - Run on HOST:PORT with worker count

## Input ZIP File Structure - Complete Reference

### Expected Directory Layout

```
automation_artifact.zip (max 500MB)
├── status.txt                              # Text file: "passed" or "failed"
├── started_at.txt                          # Text file: ISO 8601 timestamp
├── finished_at.txt                         # Text file: ISO 8601 timestamp
├── success/ (if status is "passed")
│   ├── 0__step_0_ecb40f97ce06/
│   │   ├── step_summary.json               # JSON metadata
│   │   ├── screenshot.png                  # Step screenshot
│   │   └── console.txt                     # Optional: console output
│   ├── 1__step_1_352839a0297a/
│   │   ├── step_summary.json
│   │   ├── screenshot.png
│   │   └── console.txt
│   └── ... (more steps)
└── failures/ (if status is "failed")
    ├── 13__step_13_3f239768b504/
    │   ├── attempt_1/
    │   │   ├── step_summary.json
    │   │   ├── screenshot.png
    │   │   ├── error.txt
    │   │   ├── traceback.txt
    │   │   └── console.txt
    │   └── ... (more attempts)
    └── ... (more failed steps)
```

### File Details

#### `status.txt`
- **Content**: Single line, either "passed" or "failed"
- **Purpose**: Determines which folder to process (success/ or failures/)
- **Example**:
  ```plaintext
  passed
  ```

#### `started_at.txt`
- **Content**: ISO 8601 formatted timestamp
- **Purpose**: Script execution start time
- **Format**: `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`
- **Example**:
  ```plaintext
  2026-01-15T08:09:59.549459+00:00
  ```

#### `finished_at.txt`
- **Content**: ISO 8601 formatted timestamp
- **Purpose**: Script execution end time
- **Format**: `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`
- **Example**:
  ```plaintext
  2026-01-15T08:15:26.037473+00:00
  ```

- **Note**: Converted to duration in report

#### `success/` Folder
- **When Used**: If status.txt contains "passed"
- **Contents**: Subdirectories named `{step_index}__{step_name}_{hash}/`
- **Each Subdirectory Must Contain**:
  - `step_summary.json` (REQUIRED)
  - `screenshot.png` (REQUIRED)
  - `console.txt` (optional - parsed but not displayed)

#### `failures/` Folder
- **When Used**: If status.txt contains "failed"
- **Contents**: Subdirectories named `{step_index}__{step_name}_{hash}/`
- **Each Subdirectory Contains**:
  - `attempt_1/`, `attempt_2/`, etc. (retry attempts)
  - Each attempt has: `step_summary.json`, `screenshot.png`, `error.txt`, `traceback.txt`, `console.txt`

#### `step_summary.json` - Complete Field Reference

```json
{
  "step_index": 0,
  "step_name": "0__step_0_ecb40f97ce06",
  "intent": "Navigate to OrangeHRM login page.",
  "started_at": "2026-01-15T08:09:59.549459+00:00",
  "ended_at": "2026-01-15T08:10:26.037473+00:00",
  "duration_sec": 26.4899,
  "url": "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login",
  "attempts": 1,
  "max_retries": 1,
  "status": "passed",
  "flaky": false,
  "step_code_hash": "ecb40f97ce06"
}
```

**Field Descriptions**:
- `step_index` (int): 0-based step sequence number
- `step_name` (str): Unique step identifier, format: `{index}__{description}_{hash}`
- `intent` (str): Human-readable description of what this step does
- `started_at` (str): ISO 8601 timestamp when step started (NOT used in report)
- `ended_at` (str): ISO 8601 timestamp when step ended (NOT used in report)
- `duration_sec` (float): Execution time in seconds (displayed in report)
- `url` (str): Page URL or target URL of step action (displayed in report)
- `attempts` (int): Number of successful attempts before passing
- `max_retries` (int): Maximum retry configuration
- `status` (str): "passed" or "failed" (displayed in report)
- `flaky` (bool): Whether step has intermittent failures (NOT used in report)
- `step_code_hash` (str): Code hash for deduplication (NOT used in report)

**Fields Displayed in Report**:
- step_name ✓
- intent ✓
- duration_sec ✓
- url ✓
- attempts ✓
- max_retries ✓
- status ✓

**Fields Hidden from Report**:
- started_at (replaced by calculated total duration)
- ended_at (replaced by calculated total duration)
- flaky (internal only)
- step_code_hash (internal only)

#### `screenshot.png`
- **Format**: PNG image file
- **Purpose**: Visual documentation of step state
- **Size**: Typically 1200x800 or 1920x1080 pixels
- **Embedded**: Base64 encoded directly in HTML (`data:image/png;base64,...`)
- **Display**: Full-width in report with 1px border

#### `console.txt` (Optional)
- **Content**: Step console output or logs
- **Purpose**: Debugging (currently not displayed in reports but extracted)
- **Format**: Plain text

#### `error.txt` & `traceback.txt` (In failures/ only)
- **Purpose**: Failure debugging information
- **Currently**: Not displayed in reports
- **Location**: Under `failures/{step_name}/attempt_N/`

### Example ZIP Creation (Python)

```python
import zipfile
import json
from datetime import datetime
import os

# Create ZIP
with zipfile.ZipFile('automation_artifact.zip', 'w') as zf:
    # Add status
    zf.writestr('status.txt', 'passed')
    zf.writestr('started_at.txt', '2026-01-15T08:09:59.549459+00:00')
    zf.writestr('finished_at.txt', '2026-01-15T08:15:26.037473+00:00')
    
    # Add step artifacts
    for i in range(15):
        step_dir = f'success/{i}__step_{i}_hash123/'
        
        # Add step_summary.json
        step_data = {
            "step_index": i,
            "step_name": f"{i}__step_{i}_hash123",
            "intent": f"Step {i}: Click button",
            "duration_sec": 15.5,
            "url": "https://example.com",
            "attempts": 1,
            "max_retries": 1,
            "status": "passed"
        }
        zf.writestr(f'{step_dir}step_summary.json', json.dumps(step_data))
        
        # Add screenshot
        with open(f'step_{i}_screenshot.png', 'rb') as f:
            zf.writestr(f'{step_dir}screenshot.png', f.read())
"# Report-Generator" 
