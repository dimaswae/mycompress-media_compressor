# `mycompress` Frontend — React + Vite + TailwindCSS UI

Modern, premium web UI built with React, Vite, and TailwindCSS to interact with the `mycompress` media compression and steganography backend.

---

## 1. Overview
The frontend provides an intuitive and responsive workspace for processing images, audio, and video files:
* **Image Processor**: Side-by-side comparison slider and quality metrics (PSNR, SSIM, MSE, ratio, timing) for compressed or steganographic images.
* **Audio Processor**: WAV/MP3 upload, LSB stego message embedding/extraction, and metrics.
* **Video Processor**: MP4 upload, CRF compression selection, LSB frame-level message hiding, and processing states.
* **History Dashboard**: A paginated view to list and audit recent jobs, status, and download original or processed artifacts.

### Key Technology Stack
* **Build Tool**: Vite 6
* **UI Framework**: React 19 (TypeScript)
* **CSS Styling**: TailwindCSS 4
* **Charts & Viz**: Recharts (for performance and ratio visualizations)
* **Test Runner**: Vitest with JSDOM and React Testing Library

---

## 2. Prerequisites
Before installing, ensure you have the following installed on your system:
* **Node.js**: **v18.0.0 or higher** (Recommended: v20 LTS).
* **Package Manager**: **npm** (comes bundled with Node.js), but yarn/pnpm are also compatible.

---

## 3. Setup Instructions

### Step 1: Navigate to the Frontend Directory
```bash
cd frontend
```

### Step 2: Install Node Dependencies
```bash
npm install
```

### Step 3: Configure Environment Variables
To define the backend server address, create a `.env` file (or `.env.local` for local dev) in the `frontend/` directory.

#### Configuration Variables:
* **`VITE_API_BASE`**:
  * **Default**: `"/api/v1"` (assumes requests are proxied or hosted on the same origin).
  * **Custom Server**: If your backend server is running on a different port or host (e.g., Uvicorn running on port 8000), set:
    ```env
    VITE_API_BASE=http://localhost:8000/api/v1
    ```

---

## 4. Running the Dev Server & Production Build

### Start Development Server
Run the local dev server with hot-module replacement (HMR):
```bash
npm run dev
```
By default, the Vite dev server runs at:
* Local: [http://localhost:5173/](http://localhost:5173/)

### Build for Production
To compile and optimize the application for production deployment:
```bash
npm run build
```
This command runs type-checking and compiles the build into the `dist/` directory.

### Preview Production Build Locally
Verify the production build locally before deploying:
```bash
npm run preview
```

---

## 5. Testing

The project uses `Vitest` for testing components, hooks, and API clients.

### Run All Tests
To run all test cases (22 tests) once and exit:
```bash
npm run test
```

### Run Tests in Watch Mode (Interactive)
To keep the test runner open and watch for file changes:
```bash
npx vitest
```

### Run a Specific Test File
```bash
# Run tests for a specific page component
npx vitest src/pages/__tests__/ImagePage.test.tsx

# Run tests for a specific custom hook
npx vitest src/hooks/__tests__/useJobPolling.test.tsx
```

---

## 6. Directory Structure

```
frontend/
├── public/              # Static assets (favicons, public images)
├── src/
│   ├── api/             # API client handlers communicating with FastAPI
│   │   ├── client.ts       # Centralized fetch/upload wrapper with error mapping
│   │   ├── imageApi.ts     # Image compress/decompress/embed/extract/compare calls
│   │   ├── audioApi.ts     # Audio calls
│   │   ├── videoApi.ts     # Video calls
│   │   └── jobsApi.ts      # Job status, paginated lists, and download endpoints
│   ├── components/      # Reusable UI component blocks
│   │   ├── common/         # Buttons, loaders, error banners
│   │   ├── upload/         # File dropzones, progress bars
│   │   ├── jobs/           # Job progress meters, status badges
│   │   ├── metrics/        # Tabular data and chart visualization (Recharts)
│   │   └── comparison/     # A/B player and image compare views
│   ├── hooks/           # Custom React Hooks
│   │   ├── useFileUpload.ts# Handles file uploading states & progress
│   │   └── useJobPolling.ts# Long-polls /jobs/{id} status securely
│   ├── pages/           # Page layouts mapped to routes
│   │   ├── HomePage.tsx      # Entry selection dashboard
│   │   ├── ImagePage.tsx     # Image workspace
│   │   ├── AudioPage.tsx     # Audio workspace
│   │   ├── VideoPage.tsx     # Video workspace
│   │   └── JobHistoryPage.tsx# Job auditing log list
│   ├── types/           # TypeScript interfaces (media, metrics, jobs)
│   ├── styles/          # TailwindCSS styles entry point
│   ├── main.tsx         # React app bootstrap entry point
│   └── router.tsx       # Routing table using react-router-dom
├── eslint.config.js     # ESLint configuration
├── vite.config.ts       # Vite config wiring plugins (@tailwindcss/vite, @vitejs/plugin-react)
├── tsconfig.json        # TypeScript configuration options
└── package.json         # Scripts and project dependencies
```
