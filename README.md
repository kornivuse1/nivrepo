# NivPro – Music player server

A simple 24/7 music player server: you (and chosen admins) upload songs via a separate admin UI; family and friends log in as viewers to search and play.

## Features

- **Player** (`/`): log in, unified bar (play/pause, prev/next, shuffle), search, stream; love songs (heart); optional background image (auto-change per song)
- **Admin** (`/admin`): upload/edit/delete songs, play songs in admin; upload/activate background images; list and remove users; see love counts per song
- **Storage**: song files and images on disk, metadata in SQLite (or PostgreSQL via `DATABASE_URL`)
- **Deploy**: Docker image, GitHub Actions (test + build + push to GHCR), optional auto-deploy to VPS via SSH

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

   For **local dev** you can set `CREATE_DEFAULT_ADMIN=true` in `.env` to auto-create `admin`/`admin` when the DB is empty. **In production leave this unset or false** so no default password exists; always create the first admin with the script above.

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

If you cloned or created this folder without Git, see **PUSH_TO_GITHUB.md** for step-by-step push instructions. Quick version:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/nivpro.git
git push -u origin main
```

CI runs on push to `main` (test + build image + optional deploy).

---

## Leftovers (continue in another session)

Things to do next when you return:

1. **Push to GitHub** (if not done yet)
   - Install Git from https://git-scm.com/download/win if needed.
   - Follow **PUSH_TO_GITHUB.md** to create the repo and push.
   - Make the GitHub package public so the VPS can pull the image.

2. **VPS setup and deploy**
   - Buy/create a VPS (Ubuntu 22.04), note the IP.
   - Follow **DEPLOYMENT.md** step-by-step:
     - Phase 2: SSH, user, firewall (22, 80, 443).
     - Phase 3: Install Docker and Docker Compose on the VPS.
     - Phase 4: Add GitHub Actions secrets: `VPS_HOST`, `VPS_USER`, `SSH_PRIVATE_KEY`.
     - Phase 5–6: Create `~/nivpro` on the VPS, copy `deploy/` files, create `.env`, run `docker compose -f docker-compose.prod.yml up -d` (Nginx + app).
   - After that, each push to `main` will deploy automatically.

3. **HTTPS (optional)**
   - If you have a domain pointing to the VPS: **DEPLOYMENT.md** Phase 7 (Certbot + Nginx HTTPS).

4. **Optional improvements** (see PROJECT_SUMMARY.md)
   - HTTPS and reverse proxy on VPS.
   - Viewer registration or invite flow.
   - Password change / forgot password.
   - Sort/filter by love count in admin.

**Reference files**
- **PUSH_TO_GITHUB.md** – Push this repo to GitHub.
- **DEPLOYMENT.md** – Full VPS + Docker + Nginx + CI deploy guide.
- **PROJECT_SUMMARY.md** – What the app does and what was built.
