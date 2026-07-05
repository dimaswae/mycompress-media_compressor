# `mycompress` Backend — FastAPI Media Compressor & Steganography API

FastAPI-based backend for a web-based media application supporting image, audio, and video compression, decompression, steganographic message embedding/extraction, and quality/fidelity comparison metrics.

---

## 1. Overview
The backend exposes high-performance endpoints for processing different media formats:
* **Image**: PNG and JPG compression (custom RLE/Huffman) and LSB-based message hiding.
* **Audio**: WAV-to-MP3 bitrate reduction compression and LSB message hiding in WAV.
* **Video**: MP4 compression (CRF-based) and LSB frame-level message hiding with lossless intermediate remuxing (to prevent transcoding loss).
* **Metrics**: Automated evaluation of **PSNR, SSIM, MSE**, Compression Ratio, Processing Time, and Steganographic Capacity.
* **Security**: Optional password-derived **AES-GCM** encryption for hidden stego payloads.

### Technology Stack
* **Web Framework**: FastAPI (Python 3.11/3.12/3.13)
* **Image Processing**: Pillow, Scikit-image, NumPy
* **Audio & Video Processing**: FFmpeg (via list-args subprocess)
* **Database & ORM**: SQLite (`mycompress.db`) with SQLAlchemy
* **Migration Manager**: Alembic
* **Quality Metrics**: Scikit-image, NumPy, OpenCV-Python

---

## 2. Prerequisites & System Dependencies

### Python Version
* Recommended: **Python 3.11 or later**. 

### FFmpeg (CRITICAL SYSTEM REQUIREMENT)
FFmpeg is **required** to process audio transcodings, video compressions, and video frame extractions. The app invokes FFmpeg via subprocess, so it **must be available in your system's PATH**.

#### How to Install and Verify FFmpeg:

##### 1. Windows (Development Environment)
1. Download a pre-built release package from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (e.g., `ffmpeg-git-full.7z` or `ffmpeg-release-essentials.zip`).
2. Extract the archive into a permanent folder, for example `C:\ffmpeg`.
3. Add the `bin` folder path (`C:\ffmpeg\bin`) to your User or System Environment Variables:
   * Press `Win + R`, type `sysdm.cpl` and press Enter.
   * Go to **Advanced** tab -> click **Environment Variables**.
   * Under **User variables** or **System variables**, select `Path` and click **Edit**.
   * Click **New** and paste: `C:\ffmpeg\bin`.
   * Click **OK** to save and close all dialogs.
4. **Important**: Restart any open Terminal, VS Code, or command-line windows to load the new PATH settings.

##### 2. Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y ffmpeg
```

##### 3. macOS
```bash
brew install ffmpeg
```

##### 4. Verify FFmpeg Installation
Run the following commands in a new terminal window. Both must return version information without error:
```bash
ffmpeg -version
ffprobe -version
```

---

## 3. Setup Instructions

Follow these steps to set up the backend on your local environment:

### Step 1: Navigate to the Backend Folder
```bash
cd backend
```

### Step 2: Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Activate on Windows (CMD)
.venv\Scripts\activate.bat
# Activate on Linux/macOS
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
You can customize the settings by creating a `.env` file in the `backend/` directory.

#### Available Variables (Prefixed with `MYCOMPRESS_`):
| Env Variable | Type | Default Value | Description |
|---|---|---|---|
| `MYCOMPRESS_APP_NAME` | string | `"mycompress"` | Name of the FastAPI application. |
| `MYCOMPRESS_DEBUG` | boolean | `True` | Runs FastAPI in debug mode with interactive error outputs. |
| `MYCOMPRESS_API_PREFIX` | string | `"/api/v1"` | Router prefix for all REST endpoints. |
| `MYCOMPRESS_UPLOAD_MAX_SIZE_MB` | integer | `100` | Limits uploaded file sizes (default: 100MB). |
| `MYCOMPRESS_STORAGE_DIR` | string | `"storage"` | Local directory name for uploads/results. |
| `MYCOMPRESS_CORS_ORIGINS` | JSON array | `["http://localhost:5173", "http://127.0.0.1:5173"]` | Allowlist of origins for CORS. |
| `MYCOMPRESS_DB_URL` | string | `"sqlite:///./mycompress.db"` | Database connection string. |
| `MYCOMPRESS_DB_ECHO` | boolean | `False` | Enables printing SQL statements in server stdout. |
| `MYCOMPRESS_JOB_TTL_HOURS` | integer | `24` | TTL duration for file expiration sweep (default: 24 hours). |
| `MYCOMPRESS_STORAGE_QUOTA_GB` | integer | `5` | Disk quota cap for the storage directory before rejecting new uploads. |
| `MYCOMPRESS_FFMPEG_TIMEOUT_SECONDS` | integer | `120` | Subprocess timeout limit for FFmpeg calls. |
| `MYCOMPRESS_SWEEP_INTERVAL_MINUTES` | integer | `60` | Execution interval of the expired jobs cleanup daemon. |

---

## 4. Running the Server

### Start Dev Server
Run uvicorn to start the application with reload support:
```bash
uvicorn app.main:app --reload --port 8000
```

### Access API Documentation
Once started, the server listens on **port 8000** by default. Open the following URLs in your web browser:
* **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 5. Testing

The project uses `pytest` for all test execution.

### Run All Tests
Execute the full suite of unit and integration tests (251 tests):
```bash
pytest
```

### Run Specific Test Files or Folders
To run tests only in a specific directory or a single file:
```bash
# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run a single test file
pytest tests/unit/test_aes_cipher.py

# Run a specific test class/function inside a file
pytest tests/unit/test_aes_cipher.py::TestAesCipher::test_encrypt_decrypt_roundtrip
```

### Troubleshooting Tests
To print stdout/stderr outputs from tests during execution:
```bash
pytest -s
```

---

## 6. Project Directory Structure

```
backend/
├── app/
│   ├── api/             # REST Routers (routes_image, routes_audio, routes_video, routes_jobs, routes_health)
│   ├── schemas/         # Pydantic validation models (common, image, audio, video)
│   ├── services/        # Orchestrates domain logic (image_service, audio_service, video_service, job_service)
│   ├── core/            # Low-level core engines:
│   │   ├── compression/    # Codecs: RLE, Huffman, AudioBitrate, VideoTranscode
│   │   ├── steganography/  # LSB embedding & extraction for image, audio, video
│   │   ├── metrics/        # Calculations for PSNR, SSIM, MSE, Compression Ratio
│   │   └── security/       # Cryptographic engines (AES-GCM encryption/decryption)
│   ├── infra/           # Infrastructure & Platform helpers:
│   │   ├── storage.py      # Storage management & directory quota limits
│   │   ├── ffmpeg_runner.py# Subprocess wrapper running FFmpeg safely
│   │   ├── cleanup.py      # Expiration sweeper for uploaded/processed files
│   │   └── file_validation.py # Extension validation and magic-byte sniffing
│   ├── db/              # Persistent engine and ORM configurations
│   │   ├── database.py     # SQLAlchemy connection & session manager
│   │   ├── models.py       # Job & Metric ORM schema classes
│   │   └── migrations/     # Alembic revision files
│   ├── utils/           # Utility functions (timing decorators, app exceptions)
│   ├── middleware/      # Global middleware (exception/error handler mapping)
│   ├── config.py        # Settings management via pydantic-settings
│   └── main.py          # FastAPI app init, startup task registry, and error router hooks
├── tests/               # Pytest Suite
│   ├── unit/            # Unit tests verifying specific modules in isolation
│   ├── integration/     # Integration tests verifying complete route contracts
│   └── fixtures/        # Mock audio/video/image data fixtures for tests
├── requirements.txt     # Python requirements manifest
├── alembic.ini          # Alembic configuration
└── pytest.ini           # Pytest settings and options
```
