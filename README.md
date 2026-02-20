# NivPro – Music player server

A simple 24/7 music player server: you (and chosen admins) upload songs via a separate admin UI; family and friends log in as viewers to search and play.

## Features

- **Player** (viewers): log in, browse and search songs, stream audio
- **Admin** (`/admin`): log in as admin to upload and remove songs (not part of the main app UI)
- **Storage**: song files on disk, metadata in SQLite (or PostgreSQL)
- **Deploy**: Docker image, CI builds and pushes to GitHub Container Registry; optional deploy to VPS

## Run locally (development)

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Copy environment template and set a secret key:

   ```bash
   copy .env.example .env
   # Edit .env: set SECRET_KEY and optionally DATABASE_URL, UPLOAD_DIR
   ```

3. Run the app:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Open http://127.0.0.1:8000 for the player; http://127.0.0.1:8000/admin for the admin UI.

5. Create the first admin user (one-time):

   ```bash
   python -m app.scripts.create_admin
   ```

## Run with Docker (local or VPS)

```bash
docker compose up -d
```

Songs and database are stored in Docker volumes so they persist across restarts.

## Deploy to VPS

1. Push this repo to GitHub.
2. In GitHub: add repository secrets (e.g. `VPS_HOST`, `VPS_USER`, `SSH_PRIVATE_KEY`) and optionally enable the deploy job in CI.
3. On the VPS: install Docker and Docker Compose, create volumes/dirs for uploads and DB, set `.env` (e.g. `SECRET_KEY`).
4. CI will build the image and push to GHCR; the deploy step will pull and restart the container on your VPS.

## Project layout

- `app/` – FastAPI app, auth, routers, services, static files
- `templates/` – Jinja2 templates (player + admin)
- `uploads/` – Song files (gitignored; use a volume in production)

## Git

If you cloned or created this folder without Git, initialize a repo and make the first commit:

```bash
git init
git add .
git commit -m "Initial commit"
```

Then add a remote and push to GitHub. CI will run on push to `main`.
