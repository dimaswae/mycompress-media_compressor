# AGENTS.md

## Project Overview

Project Name:
mycompress - media_compressor

Goal:
Build a web-based application that supports Image, Audio, and Video compression/decompression and steganography.

The system must:

* Compress media files
* Decompress media files
* Hide secret messages
* Extract hidden messages
* Compare original and processed files
* Display evaluation metrics

## Technology Stack

Frontend:

* React
* Vite
* TailwindCSS

Backend:

* Python
* FastAPI

Libraries:

* Pillow
* OpenCV
* NumPy
* FFmpeg
* Cryptography
* Scikit-image

## Architecture

Frontend -> FastAPI -> Compression Module -> Steganography Module -> Metrics Module

## Supported Media

Image:

* PNG
* JPG

Audio:

* WAV
* MP3

Video:

* MP4

## Metrics

Image:

* PSNR
* SSIM
* MSE

All Media:

* Compression Ratio
* Processing Time
* Hidden Capacity

## Coding Rules

* Use clean architecture
* Separate business logic from API layer
* Add type hints
* Write docstrings
* Keep functions under 50 lines if possible
* Prefer composition over large classes

## Testing Rules

Every feature must have:

* Unit test
* Error handling
* Sample test file

## Definition of Done

Feature is completed only if:

* Code works
* Tests pass
* API documented
* UI integrated
* README updated
