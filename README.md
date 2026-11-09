
# Render Capacitor APK Server

FastAPI backend + Capacitor + Android SDK/Gradle. Accepts `.html` or `.zip` containing `index.html`, and produces a **debug APK**.

## Important: Free-tier reality

This project includes a Render Free Blueprint, but Android compilation is resource intensive. Render Free has limited memory/CPU, sleeps when idle, and has ephemeral filesystem. Therefore APK builds may fail with out-of-memory/timeouts, and jobs/APKs may disappear after restart or redeploy. This is a free-tier experiment, **not a reliable always-on build server**. Reliable builds need a VPS/worker with persistent storage (recommended 2+ vCPU, 4+ GB RAM). No service can guarantee unlimited free Android builds.

## Deploy
1. Push this folder to a private GitHub repository.
2. Render Dashboard -> New -> Blueprint -> connect repository -> deploy `render.yaml`.
3. Wait for Docker build; Android SDK installation is large and can take time.
4. Copy the generated `API_KEY` from Render Environment. Keep it private.
5. Test `https://YOUR-SERVICE.onrender.com/health`; API docs at `/docs`.

## API
Create build:
```bash
curl -X POST https://YOUR-SERVICE.onrender.com/api/v1/builds \
 -H "X-API-Key: YOUR_API_KEY" \
 -F "app_name=Demo App" \
 -F "package_id=com.example.demo" \
 -F "file=@website.zip"
```
Poll:
```bash
curl -H "X-API-Key: YOUR_API_KEY" https://YOUR-SERVICE.onrender.com/api/v1/builds/JOB_ID
```
Download:
```bash
curl -L -H "X-API-Key: YOUR_API_KEY" https://YOUR-SERVICE.onrender.com/api/v1/builds/JOB_ID/download -o app.apk
```

Endpoints:
- `GET /health`
- `POST /api/v1/builds`
- `GET /api/v1/builds`
- `GET /api/v1/builds/{job_id}`
- `GET /api/v1/builds/{job_id}/download`
- Swagger: `/docs`

## Local Docker
```bash
cp .env.example .env
# Set a long random API_KEY in .env
docker build -t capacitor-apk-server .
docker run --rm -p 10000:10000 --env-file .env -v apkdata:/tmp/apk-server-data capacitor-apk-server
```
Docker build needs several GB of free disk and memory.

## Scope
- Static website only; ZIP must contain `index.html`.
- Does not compile arbitrary Android Studio projects or server-side PHP/Node apps.
- Debug APK only; not signed for Play Store release.
- Default Capacitor icon/splash.
- One build worker, one build at a time.
- Keep API key out of frontend/browser code. Put a trusted Telegram bot/backend in front of this API.
- ZIP path traversal, symlink, file-count and expanded-size checks are applied. Do not expose an unauthenticated public build endpoint.
