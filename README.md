# MyCompress - Media Compressor & Steganography Tool

Welcome to **MyCompress**, a comprehensive web application for media compression, decompression, and steganography (hiding secret messages in images, audio, and video).

## Project Overview

This repository is split into two main components:

1. **[Backend Application (FastAPI + Python)](file:///E:/.01-MyDocument/.03-Coding/repo_here/mycompress-media_compressor/backend/README.md)**:
   - Built with **Python** & **FastAPI**.
   - Handles image processing (Pillow, NumPy), audio processing, video processing (FFmpeg, OpenCV), and security/encryption (cryptography, AES-GCM).
   - Provides REST APIs for file upload, compression jobs management, steganography operations, and quality metrics (PSNR, SSIM, MSE).
   - Read the detailed backend documentation: **[backend/README.md](file:///E:/.01-MyDocument/.03-Coding/repo_here/mycompress-media_compressor/backend/README.md)**.

2. **[Frontend Application (React + Vite + TailwindCSS)](file:///E:/.01-MyDocument/.03-Coding/repo_here/mycompress-media_compressor/frontend/README.md)**:
   - Built with **React**, **Vite**, and **TailwindCSS**.
   - Offers an interactive, modern user interface to upload files, configure compression parameters, embed/extract secret messages, and view real-time metrics.
   - Read the detailed frontend documentation: **[frontend/README.md](file:///E:/.01-MyDocument/.03-Coding/repo_here/mycompress-media_compressor/frontend/README.md)**.

## Quick Start

For detailed setup, installation, and usage instructions, please refer to the respective subproject documentation:
* Go to **[Backend Setup Guide](file:///E:/.01-MyDocument/.03-Coding/repo_here/mycompress-media_compressor/backend/README.md)** to configure and run the Python FastAPI server.
* Go to **[Frontend Setup Guide](file:///E:/.01-MyDocument/.03-Coding/repo_here/mycompress-media_compressor/frontend/README.md)** to run the React single-page application.
